"""
Context API — Receives the interest graph from the MCP server and serves it to the dashboard.

Two modes:
1. Authenticated (Supabase JWT) — for web dashboard reads
2. API Key — for the MCP server syncing the local interest graph from the user's machine

NOTE (v2 pivot): the digest-generation pipeline (research → curation → email) has been
removed. This router now only persists the synced interest graph and exposes it for display.
The `/digest` prefix is retained to avoid frontend churn; rename to `/context` in Phase 1.
"""

import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from middleware.auth_middleware import get_current_user
from pydantic import BaseModel
from services.supabase_client import get_service_client

router = APIRouter(prefix="/digest", tags=["context"])


# ── Request Models ────────────────────────────────────────────────


class SyncRequest(BaseModel):
    """Lightweight sync — MCP server pushes interest graph updates."""

    email: str
    interest_graph: dict
    total_signals: int = 0


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


# ── Interest Graph Sync (from MCP server) ──────────────────────────


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
    """Get aggregated interest-graph stats for the dashboard overview."""
    client = get_service_client()

    snapshot = (
        client.table("interest_snapshots")
        .select("interest_graph, total_signals, synced_at")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    graph = snapshot.data.get("interest_graph", {}) if snapshot and snapshot.data else {}
    topics = graph.get("topics", [])
    categories = graph.get("categories", {})

    total_topics = len(topics)
    total_signals = snapshot.data.get("total_signals", 0) if snapshot and snapshot.data else 0
    last_synced = snapshot.data.get("synced_at") if snapshot and snapshot.data else None

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
        "last_synced": last_synced,
        "top_categories": [{"name": c[0], "weight": round(c[1], 2)} for c in top_categories],
        "intent_breakdown": intent_counts,
        "sentiment": {
            "positive": sentiment_positive,
            "negative": sentiment_negative,
            "neutral": sentiment_neutral,
        },
    }
