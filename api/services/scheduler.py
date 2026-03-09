"""
Digest Scheduler — Automatically sends digests based on user preferences.

Runs as a background task in the FastAPI app. Checks hourly for users
who need a digest based on their configured frequency (daily/weekly)
and when they last received one.
"""

import asyncio
from datetime import datetime

from services.engine_bridge import run_generation_pipeline
from services.supabase_client import get_service_client

SCHEDULER_INTERVAL = 3600  # Check every hour


async def digest_scheduler_loop():
    """Main scheduler loop. Runs forever, checks hourly."""
    while True:
        try:
            await check_and_send_digests()
        except Exception as e:
            print(f"Scheduler error: {e}")
        await asyncio.sleep(SCHEDULER_INTERVAL)


async def check_and_send_digests():
    """Check all users and send digests to those who are due."""
    client = get_service_client()

    # Get all users with interest snapshots who have email configured
    # interest_snapshots table has: user_id, interest_graph, synced_at
    try:
        snapshots = (
            client.table("interest_snapshots").select("user_id, interest_graph, total_signals, synced_at").execute()
        )
    except Exception:
        return  # Table might not exist yet

    if not snapshots or not snapshots.data:
        return

    now = datetime.utcnow()

    for snapshot in snapshots.data:
        user_id = snapshot["user_id"]

        try:
            # Get user preferences (frequency, email)
            user = client.table("users").select("email, name").eq("id", user_id).maybe_single().execute()
            if not user or not user.data or not user.data.get("email"):
                continue

            prefs = client.table("user_preferences").select("*").eq("user_id", user_id).maybe_single().execute()
            frequency = "daily"
            if prefs and prefs.data:
                frequency = prefs.data.get("send_frequency", "daily")

            # Check last newsletter sent time
            last_newsletter = (
                client.table("newsletters")
                .select("sent_at")
                .eq("user_id", user_id)
                .order("sent_at", desc=True)
                .limit(1)
                .maybe_single()
                .execute()
            )

            if last_newsletter and last_newsletter.data:
                last_sent = datetime.fromisoformat(last_newsletter.data["sent_at"].replace("Z", "+00:00")).replace(
                    tzinfo=None
                )
                hours_since = (now - last_sent).total_seconds() / 3600

                if frequency == "daily" and hours_since < 20:  # 20 hours buffer
                    continue
                if frequency == "weekly" and hours_since < 144:  # 6 days buffer
                    continue

            # Check for running jobs
            running = (
                client.table("generation_jobs")
                .select("id")
                .eq("user_id", user_id)
                .in_("status", ["pending", "running"])
                .maybe_single()
                .execute()
            )
            if running and running.data:
                continue

            # Create job and generate digest
            interest_graph = snapshot.get("interest_graph", {})
            if not interest_graph.get("topics"):
                continue

            print(f"Scheduler: Sending {frequency} digest to {user.data['email']}")

            job = client.table("generation_jobs").insert({"user_id": user_id, "status": "pending"}).execute()
            job_id = job.data[0]["id"]

            # Build user profile from interest graph
            from routers.digest import _build_research_from_interests, _interest_graph_to_profile

            user_profile = _interest_graph_to_profile(
                user.data["email"],
                interest_graph,
                {},  # No balanced allocation stored separately
            )
            user_profile["name"] = user.data.get("name", "")

            # Get GitHub token if available
            github_token = None
            try:
                account = (
                    client.table("connected_accounts")
                    .select("access_token, username")
                    .eq("user_id", user_id)
                    .eq("provider", "github")
                    .maybe_single()
                    .execute()
                )
                if account and account.data:
                    github_token = account.data["access_token"]
                    user_profile["github_username"] = account.data["username"]
            except Exception:
                pass

            research_data = _build_research_from_interests(interest_graph, {})

            # Fire and forget — run_generation_pipeline handles its own error reporting
            asyncio.create_task(
                run_generation_pipeline(
                    user_id=user_id,
                    job_id=job_id,
                    user_profile=user_profile,
                    github_token=github_token,
                    research_data=research_data,
                    newsletter_extra_fields={"source": "scheduled_digest"},
                )
            )

        except Exception as e:
            print(f"Scheduler: Error processing user {user_id}: {e}")
            continue
