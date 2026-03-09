"""
Digest API — Receives interest graph from MCP server and triggers personalized digest generation.

Two modes:
1. Authenticated (Supabase JWT) — for web dashboard users
2. API Key — for MCP server calling from local machine

The MCP server's `persnally_digest` tool outputs a JSON payload with the user's interest graph.
This endpoint receives that payload, converts it to a user profile the curation engine understands,
and triggers the full pipeline: research → AI curation → validation → Resend email.
"""

import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from middleware.auth_middleware import get_current_user
from services.engine_bridge import run_generation_pipeline
from services.supabase_client import get_service_client

router = APIRouter(prefix="/digest", tags=["digest"])


# ── Request/Response Models ──────────────────────────────────────


class TopicInput(BaseModel):
    topic: str
    weight: float
    category: str
    intent: str
    entities: list[str] = []


class DigestRequest(BaseModel):
    """Payload from MCP server's persnally_digest tool."""

    email: str
    interest_graph: dict  # { topics: [...], categories: {...}, total_signals: int }
    balanced_allocation: dict  # { category: { allocation: int, topics: [...] } }
    preferences: dict = {"max_items": 7, "frequency": "daily"}


class SyncRequest(BaseModel):
    """Lightweight sync — MCP server pushes interest graph updates."""

    email: str
    interest_graph: dict
    total_signals: int = 0


class DigestResponse(BaseModel):
    job_id: str
    status: str


# ── API Key auth (for MCP server) ──────────────────────────────────


async def verify_api_key_or_user(request: Request, x_api_key: str | None = Header(None)):
    """Allow either Supabase JWT or API key auth."""
    # Try API key first (MCP server flow)
    if x_api_key:
        client = get_service_client()
        try:
            result = (
                client.table("api_keys")
                .select("user_id, email")
                .eq("key", hashlib.sha256(x_api_key.encode()).hexdigest())
                .eq("active", True)
                .maybe_single()
                .execute()
            )
            if result and result.data:
                return {"id": result.data["user_id"], "email": result.data["email"]}
        except Exception:
            pass  # Table might not exist yet, fall through to JWT

    # Try Supabase JWT
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        client = get_service_client()
        try:
            user_response = client.auth.get_user(token)
            if user_response and user_response.user:
                return {
                    "id": str(user_response.user.id),
                    "email": user_response.user.email,
                }
        except Exception:
            pass

    raise HTTPException(status_code=401, detail="Invalid API key or token")


# ── Digest Generation Endpoint ──────────────────────────────────


@router.post("/generate", response_model=DigestResponse)
async def generate_digest(
    payload: DigestRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_api_key_or_user),
):
    """
    Generate a personalized digest from MCP interest graph.

    Called by the MCP server when user triggers `persnally_digest`.
    Converts interest graph → user profile → curation pipeline → email.
    """
    client = get_service_client()

    # Check for running job
    try:
        running = (
            client.table("generation_jobs")
            .select("id")
            .eq("user_id", user["id"])
            .in_("status", ["pending", "running"])
            .maybe_single()
            .execute()
        )
        if running and running.data:
            return DigestResponse(job_id=running.data["id"], status="already_running")
    except Exception:
        pass

    # Create job
    job = client.table("generation_jobs").insert({"user_id": user["id"], "status": "pending"}).execute()
    job_id = job.data[0]["id"]

    # Store interest graph snapshot for this digest
    try:
        client.table("interest_snapshots").insert(
            {
                "user_id": user["id"],
                "interest_graph": payload.interest_graph,
                "balanced_allocation": payload.balanced_allocation,
                "total_signals": payload.interest_graph.get("total_signals", 0),
            }
        ).execute()
    except Exception:
        pass  # Table might not exist yet, non-critical

    # Run digest generation in background
    background_tasks.add_task(
        run_interest_digest,
        user_id=user["id"],
        job_id=job_id,
        email=payload.email,
        interest_graph=payload.interest_graph,
        balanced_allocation=payload.balanced_allocation,
        preferences=payload.preferences,
    )

    return DigestResponse(job_id=job_id, status="pending")


@router.get("/generate/{job_id}", response_model=DigestResponse)
async def get_digest_status(
    job_id: str,
    user: dict = Depends(verify_api_key_or_user),
):
    """Poll digest generation status."""
    client = get_service_client()
    try:
        result = (
            client.table("generation_jobs")
            .select("id, status")
            .eq("id", job_id)
            .eq("user_id", user["id"])
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return DigestResponse(job_id=result.data["id"], status=result.data["status"])


@router.post("/sync")
async def sync_interest_graph(
    payload: SyncRequest,
    user: dict = Depends(verify_api_key_or_user),
):
    """
    Sync interest graph from MCP server to cloud.
    Called periodically so the web dashboard can show the user's interest profile.
    """
    client = get_service_client()
    try:
        client.table("interest_snapshots").upsert(
            {
                "user_id": user["id"],
                "interest_graph": payload.interest_graph,
                "total_signals": payload.total_signals,
                "synced_at": datetime.utcnow().isoformat(),
            },
            on_conflict="user_id",
        ).execute()
    except Exception as e:
        # Non-critical — the MCP server still works locally
        print(f"Sync warning: {e}")

    return {"status": "synced", "total_signals": payload.total_signals}


# ── Interest Graph Endpoints (for web dashboard) ──────────────


@router.get("/interests")
async def get_interests(user: dict = Depends(get_current_user)):
    """Get the user's current interest graph for dashboard display."""
    client = get_service_client()

    snapshot = (
        client.table("interest_snapshots")
        .select("interest_graph, balanced_allocation, total_signals, synced_at")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    if not snapshot or not snapshot.data:
        return {
            "has_data": False,
            "interest_graph": {"topics": [], "categories": {}, "total_signals": 0},
            "balanced_allocation": {},
            "total_signals": 0,
            "synced_at": None,
        }

    return {
        "has_data": True,
        **snapshot.data,
    }


@router.get("/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Get aggregated stats for the dashboard overview."""
    client = get_service_client()

    # Interest snapshot
    snapshot = (
        client.table("interest_snapshots")
        .select("interest_graph, total_signals, synced_at")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    # Newsletter count and last sent
    newsletters = (
        client.table("newsletters")
        .select("id, sent_at, quality_score")
        .eq("user_id", user["id"])
        .order("sent_at", desc=True)
        .limit(5)
        .execute()
    )

    # Preferences
    prefs = (
        client.table("user_preferences")
        .select("send_frequency")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    graph = snapshot.data.get("interest_graph", {}) if snapshot and snapshot.data else {}
    topics = graph.get("topics", [])
    categories = graph.get("categories", {})
    newsletter_list = newsletters.data if newsletters and newsletters.data else []

    # Compute stats
    total_topics = len(topics)
    total_signals = snapshot.data.get("total_signals", 0) if snapshot and snapshot.data else 0
    total_digests = len(newsletter_list)
    avg_quality = (
        round(sum(n.get("quality_score", 0) for n in newsletter_list) / len(newsletter_list))
        if newsletter_list
        else 0
    )
    last_synced = snapshot.data.get("synced_at") if snapshot and snapshot.data else None
    last_digest = newsletter_list[0].get("sent_at") if newsletter_list else None
    frequency = prefs.data.get("send_frequency", "daily") if prefs and prefs.data else "daily"

    # Top categories
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]

    # Intent breakdown
    intent_counts: dict = {}
    for t in topics:
        intent = t.get("intent", "other")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    # Sentiment breakdown
    sentiment_positive = sum(1 for t in topics if t.get("sentiment_balance", t.get("sentiment", 0)) > 0.2)
    sentiment_negative = sum(1 for t in topics if t.get("sentiment_balance", t.get("sentiment", 0)) < -0.2)
    sentiment_neutral = total_topics - sentiment_positive - sentiment_negative

    return {
        "total_topics": total_topics,
        "total_signals": total_signals,
        "total_digests": total_digests,
        "avg_quality": avg_quality,
        "last_synced": last_synced,
        "last_digest": last_digest,
        "frequency": frequency,
        "top_categories": [{"name": c[0], "weight": round(c[1], 2)} for c in top_categories],
        "intent_breakdown": intent_counts,
        "sentiment": {
            "positive": sentiment_positive,
            "negative": sentiment_negative,
            "neutral": sentiment_neutral,
        },
    }


# ── Schedule Status ─────────────────────────────────────────────


@router.get("/schedule/status")
async def get_schedule_status(user: dict = Depends(verify_api_key_or_user)):
    """Check when the user's next digest is scheduled."""
    client = get_service_client()

    last = (
        client.table("newsletters")
        .select("sent_at")
        .eq("user_id", user["id"])
        .order("sent_at", desc=True)
        .limit(1)
        .maybe_single()
        .execute()
    )

    prefs = client.table("user_preferences").select("send_frequency").eq("user_id", user["id"]).maybe_single().execute()
    frequency = prefs.data.get("send_frequency", "daily") if prefs and prefs.data else "daily"

    last_sent = last.data["sent_at"] if last and last.data else None

    return {
        "frequency": frequency,
        "last_sent": last_sent,
        "next_expected": "within 24 hours" if frequency == "daily" else "within 7 days",
    }


# ── Background Digest Generation ────────────────────────────────


async def run_interest_digest(
    user_id: str,
    job_id: str,
    email: str,
    interest_graph: dict,
    balanced_allocation: dict,
    preferences: dict,
):
    """
    Generate digest from interest graph.

    Converts MCP interest graph into the user_profile format the existing
    curation engine expects, then runs the full pipeline.
    """
    client = get_service_client()

    # Convert interest graph → user profile for the curation engine
    user_profile = _interest_graph_to_profile(email, interest_graph, balanced_allocation)

    # Fetch GitHub token if user has one connected
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

    # Build research data from interest graph topics
    # Instead of web_research.gather_comprehensive_research (which needs GitHub activity),
    # we construct research context directly from the interest graph
    research_data = _build_research_from_interests(interest_graph, balanced_allocation)

    await run_generation_pipeline(
        user_id=user_id,
        job_id=job_id,
        user_profile=user_profile,
        github_token=github_token,
        research_data=research_data,
        newsletter_extra_fields={"source": "mcp_interest_graph"},
    )


def _interest_graph_to_profile(
    email: str,
    interest_graph: dict,
    balanced_allocation: dict,
) -> dict:
    """
    Convert MCP interest graph into the user_profile dict the curation engine expects.

    The key insight: the interest graph IS the preference engine. Instead of static
    interests like ["AI", "web dev"], we have weighted, decayed, sentiment-aware signals.
    """
    topics = interest_graph.get("topics", [])
    categories = interest_graph.get("categories", {})

    # Extract top interests as strings (for the engine's interests field)
    interests = [t["topic"] for t in sorted(topics, key=lambda x: x.get("weight", 0), reverse=True)[:15]]

    # Determine experience level from intents
    intents = [t.get("intent", "") for t in topics]
    building_ratio = intents.count("building") / max(len(intents), 1)
    experience_level = "advanced" if building_ratio > 0.4 else "intermediate" if building_ratio > 0.2 else "beginner"

    # Extract all entities for richer context
    all_entities = []
    for t in topics:
        all_entities.extend(t.get("entities", []))

    # Determine dominant categories for content style
    top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
    content_style = (
        "technical_deep_dive" if any(c[0] == "technology" for c in top_cats) else "technical_with_business_context"
    )

    return {
        "name": email.split("@")[0].replace(".", " ").title(),
        "email": email,
        "github_username": "",
        "location": "",
        "interests": interests,
        "entities": list(set(all_entities))[:30],
        "experience_level": experience_level,
        "interest_graph": interest_graph,
        "balanced_allocation": balanced_allocation,
        "preferences": {
            "content_style": content_style,
            "prioritize_local": False,
            "opportunity_types": ["hackathons", "jobs", "funding", "open_source"],
        },
    }


def _build_research_from_interests(
    interest_graph: dict,
    balanced_allocation: dict,
) -> dict:
    """
    Build research_data dict from interest graph.

    The curation engine expects research_data with specific fields.
    We construct a lightweight version that focuses the AI on the user's
    actual interests rather than generic GitHub activity.
    """
    topics = interest_graph.get("topics", [])

    # Build topic descriptions for the AI to research
    topic_summaries = []
    for t in topics[:20]:
        entities_str = ", ".join(t.get("entities", [])[:3])
        summary = f"{t['topic']} (weight: {t.get('weight', 0):.2f}, intent: {t.get('intent', 'learning')}"
        if entities_str:
            summary += f", related: {entities_str}"
        summary += ")"
        topic_summaries.append(summary)

    # Build allocation context
    allocation_context = []
    for cat, data in balanced_allocation.items():
        cat_topics = [t["topic"] for t in data.get("topics", [])]
        allocation_context.append(f"{cat} ({data.get('allocation', 1)} items): {', '.join(cat_topics)}")

    return {
        "github_activity": {
            "recent_repos": [],
            "languages": {},
            "starred_repos": [],
        },
        "interest_context": {
            "topics": topic_summaries,
            "allocation": allocation_context,
            "total_signals": interest_graph.get("total_signals", 0),
            "categories": interest_graph.get("categories", {}),
        },
        "web_results": [],
        "trending": [],
    }
