"""
Career Bridge - Connects the FastAPI layer to the Skill Analyzer engine.
Follows the same pattern as engine_bridge.py.
"""
from datetime import datetime
from services.supabase_client import get_service_client


async def run_skill_analysis(user_id: str, job_id: str):
    """Background task: run full skill analysis and store results."""
    client = get_service_client()

    try:
        # Mark job as running
        client.table("analysis_jobs").update({
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }).eq("id", job_id).execute()

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

        prefs = prefs_row.data or {}
        github_account = account_row.data

        if not github_account:
            raise Exception("GitHub not connected")

        github_token = github_account["access_token"]
        username = github_account["username"]
        user_interests = prefs.get("interests", [])
        experience_level = prefs.get("experience_level", "intermediate")

        # Import engine (lazy to avoid import issues at module level)
        from src.config import Config
        from src.skill_analyzer import SkillAnalyzer

        config = Config()
        analyzer = SkillAnalyzer(config)

        # Run analysis
        snapshot = await analyzer.analyze(
            github_token=github_token,
            username=username,
            user_interests=user_interests,
            experience_level=experience_level,
        )

        # Store skill snapshot
        snapshot_data = {
            "user_id": user_id,
            "snapshot_date": snapshot.get("snapshot_date", datetime.utcnow().strftime("%Y-%m-%d")),
            "skills": snapshot.get("skills", {}),
            "languages": snapshot.get("languages", {}),
            "frameworks": snapshot.get("frameworks", []),
            "domains": snapshot.get("domains", {}),
            "experience_level": snapshot.get("experience_level", experience_level),
            "career_stage": snapshot.get("career_stage", "professional"),
            "specialization": snapshot.get("specialization", ""),
            "summary": snapshot.get("summary", ""),
            "strengths": snapshot.get("strengths", []),
            "growth_areas": snapshot.get("growth_areas", []),
            "raw_github_data": {
                "repo_count": snapshot.get("repo_count", 0),
                "active_repo_count": snapshot.get("active_repo_count", 0),
                "top_repos": snapshot.get("top_repos", []),
            },
        }

        # Upsert snapshot (one per day)
        client.table("skill_snapshots").upsert(
            snapshot_data,
            on_conflict="user_id,snapshot_date",
        ).execute()

        # Store skill gaps
        skill_gaps = snapshot.get("skill_gaps", [])
        if skill_gaps:
            # Get the snapshot ID
            snap_result = (
                client.table("skill_snapshots")
                .select("id")
                .eq("user_id", user_id)
                .eq("snapshot_date", snapshot_data["snapshot_date"])
                .single()
                .execute()
            )
            snapshot_id = snap_result.data["id"] if snap_result.data else None

            # Clear old gaps for this user and insert new ones
            client.table("skill_gaps").delete().eq("user_id", user_id).eq("status", "identified").execute()

            for gap in skill_gaps:
                client.table("skill_gaps").insert({
                    "user_id": user_id,
                    "skill_name": gap["skill_name"],
                    "current_level": gap.get("current_level", 0),
                    "market_demand": gap.get("market_demand", 0),
                    "gap_score": gap.get("gap_score", 0),
                    "reason": gap.get("reason", ""),
                    "category": gap.get("category", "recommended"),
                    "snapshot_id": snapshot_id,
                }).execute()

        # Mark job complete
        client.table("analysis_jobs").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "result_summary": {
                "skills_count": len(snapshot.get("skills", {})),
                "frameworks_count": len(snapshot.get("frameworks", [])),
                "gaps_count": len(skill_gaps),
                "specialization": snapshot.get("specialization", ""),
            },
        }).eq("id", job_id).execute()

    except Exception as e:
        # Mark job failed
        client.table("analysis_jobs").update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error": str(e)[:500],
        }).eq("id", job_id).execute()
