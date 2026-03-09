"""
Engine Bridge - Connects the FastAPI layer to the existing Persnally engine.
Constructs user_profile dicts from Supabase data and runs the generation pipeline.
"""
import asyncio
import hashlib
from datetime import datetime
from services.supabase_client import get_service_client

PIPELINE_TIMEOUT_SECONDS = 120


async def run_generation_pipeline(
    user_id: str,
    job_id: str,
    user_profile: dict,
    github_token: str | None = None,
    research_data: dict | None = None,
    newsletter_extra_fields: dict | None = None,
):
    """
    Shared generation pipeline used by both the web dashboard and MCP digest flows.

    Takes a pre-built user_profile and runs the full pipeline:
    config → orchestrator → research → AI engine → email → store newsletter → store hashes → update job.

    If research_data is provided it is used directly; otherwise web research is gathered.
    newsletter_extra_fields are merged into the newsletter row (e.g. {"source": "mcp_interest_graph"}).
    """
    client = get_service_client()

    try:
        # Mark job as running (before timeout wrapper so user sees it started)
        client.table("generation_jobs").update({
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }).eq("id", job_id).execute()

        # Run the core pipeline with a timeout
        await asyncio.wait_for(
            _run_pipeline_inner(
                client, user_id, job_id, user_profile, github_token,
                research_data, newsletter_extra_fields,
            ),
            timeout=PIPELINE_TIMEOUT_SECONDS,
        )

    except asyncio.TimeoutError:
        # Pipeline took too long – mark job as failed
        client.table("generation_jobs").update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error": f"Pipeline timed out after {PIPELINE_TIMEOUT_SECONDS} seconds",
        }).eq("id", job_id).execute()

    except Exception as e:
        # Mark job failed
        client.table("generation_jobs").update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error": str(e)[:500],
        }).eq("id", job_id).execute()


async def _run_pipeline_inner(
    client,
    user_id: str,
    job_id: str,
    user_profile: dict,
    github_token: str | None,
    research_data: dict | None,
    newsletter_extra_fields: dict | None,
):
    """Core pipeline logic executed under the timeout wrapper."""
    # Import engine components (lazy to avoid import issues at module level)
    from src.config import Config
    from src.mcp_clients.resend_client import MCPResendClient
    from src.ai_engine import AIEditorialEngine
    from src.email_sender import PremiumEmailSender
    from src.system_prompts import LOCATION_RULES

    # Create config, override github token for this user
    config = Config()
    if github_token:
        config.GITHUB_TOKEN = github_token

    resend_client = MCPResendClient(config)
    ai_engine = AIEditorialEngine(config)
    email_sender = PremiumEmailSender(config, resend_client)

    await resend_client.start_mcp_server()

    # Gather research if not provided
    if research_data is None:
        from data_sources.web_research import WebResearchAggregator
        web_research = WebResearchAggregator(github_token or config.GITHUB_TOKEN)
        research_data = await web_research.gather_comprehensive_research_with_opportunities(user_profile)
        if not research_data:
            raise Exception("Failed to gather research data")

    # Generate content
    location = user_profile.get("location", "")
    location_rule = LOCATION_RULES.get("India" if "india" in location.lower() else "default")

    daily_5_content = await ai_engine.generate_daily_5(
        user_profile, research_data, location_rule=location_rule
    )

    # Render HTML
    html_content = email_sender._generate_daily_5_email_html(user_profile, daily_5_content)

    # Send email
    success = await email_sender.send_daily_5_newsletter(user_profile, daily_5_content)

    # Store newsletter
    newsletter_row = {
        "user_id": user_id,
        "subject": daily_5_content.get("subject_line", "Persnally Daily 5"),
        "headline": daily_5_content.get("headline", ""),
        "items": daily_5_content.get("items", []),
        "full_content": daily_5_content,
        "html_snapshot": html_content,
        "status": "sent" if success else "failed",
    }
    if newsletter_extra_fields:
        newsletter_row.update(newsletter_extra_fields)

    newsletter = client.table("newsletters").insert(newsletter_row).execute()
    newsletter_id = newsletter.data[0]["id"] if newsletter.data else None

    # Store content hashes for dedup
    for item in daily_5_content.get("items", []):
        content_hash = hashlib.md5(
            (item.get("title", "") + item.get("url", "")).encode()
        ).hexdigest()
        try:
            client.table("content_history").insert({
                "user_id": user_id,
                "content_hash": content_hash,
                "title": item.get("title", ""),
                "url": item.get("url", ""),
            }).execute()
        except Exception:
            pass  # Ignore duplicate hash errors

    # Mark job complete
    client.table("generation_jobs").update({
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "newsletter_id": newsletter_id,
    }).eq("id", job_id).execute()


async def run_generation_for_user(user_id: str, job_id: str):
    """Background task: generate a newsletter for a user and store results."""
    client = get_service_client()

    # Fetch user data
    user_row = client.table("users").select("*").eq("id", user_id).single().execute()
    prefs_row = client.table("user_preferences").select("*").eq("user_id", user_id).maybe_single().execute()
    account_row = (
        client.table("connected_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("provider", "github")
        .maybe_single()
        .execute()
    )

    user_data = user_row.data
    prefs = prefs_row.data or {}
    github_account = account_row.data

    # Build profile dict matching the format the engine expects
    user_profile = _build_user_profile(user_data, prefs, github_account)
    github_token = github_account["access_token"] if github_account else None

    await run_generation_pipeline(
        user_id=user_id,
        job_id=job_id,
        user_profile=user_profile,
        github_token=github_token,
    )


def _build_user_profile(user_data: dict, prefs: dict, github_account: dict | None) -> dict:
    """Build a user_profile dict matching the format the engine expects."""
    return {
        "name": user_data.get("name", ""),
        "email": user_data.get("email", ""),
        "github_username": github_account["username"] if github_account else "",
        "location": prefs.get("location", ""),
        "interests": prefs.get("interests", []),
        "experience_level": prefs.get("experience_level", "intermediate"),
        "preferences": {
            "content_style": prefs.get("content_style", "technical_with_business_context"),
            "prioritize_local": prefs.get("prioritize_local", True),
            "opportunity_types": prefs.get("opportunity_types", ["hackathons", "jobs", "funding"]),
        },
    }
