"""
Engine Bridge - Connects the FastAPI layer to the existing Persnally engine.
Constructs user_profile dicts from Supabase data and runs the generation pipeline.
"""
import asyncio
import json
import hashlib
from datetime import datetime
from services.supabase_client import get_service_client


async def run_generation_for_user(user_id: str, job_id: str):
    """Background task: generate a newsletter for a user and store results."""
    client = get_service_client()

    try:
        # Mark job as running
        client.table("generation_jobs").update({
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

        user_data = user_row.data
        prefs = prefs_row.data or {}
        github_account = account_row.data

        # Build profile dict matching the format the engine expects
        user_profile = _build_user_profile(user_data, prefs, github_account)
        github_token = github_account["access_token"] if github_account else None

        # Import engine components (lazy to avoid import issues at module level)
        from src.config import Config
        from src.mcp_orchestrator import MCPOrchestrator
        from src.ai_engine import AIEditorialEngine
        from src.email_sender import PremiumEmailSender
        from src.system_prompts import LOCATION_RULES
        from data_sources.web_research import WebResearchAggregator

        # Create config, override github token for this user
        config = Config()
        if github_token:
            config.GITHUB_TOKEN = github_token

        mcp_orchestrator = MCPOrchestrator(config)
        ai_engine = AIEditorialEngine(config)
        email_sender = PremiumEmailSender(config, mcp_orchestrator)
        web_research = WebResearchAggregator(github_token or config.GITHUB_TOKEN)

        await mcp_orchestrator.initialize_all_clients()

        # Gather research
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
        newsletter = client.table("newsletters").insert({
            "user_id": user_id,
            "subject": daily_5_content.get("subject_line", "Persnally Daily 5"),
            "headline": daily_5_content.get("headline", ""),
            "items": daily_5_content.get("items", []),
            "full_content": daily_5_content,
            "html_snapshot": html_content,
            "status": "sent" if success else "failed",
        }).execute()

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

    except Exception as e:
        # Mark job failed
        client.table("generation_jobs").update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error": str(e)[:500],
        }).eq("id", job_id).execute()


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
