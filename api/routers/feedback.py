"""Feedback API — Record upvote/downvote on digest items and adjust interest weights."""

from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from services.supabase_client import get_service_client

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _adjust_interest_weight(client, user_id: str, topic: str, vote: str) -> None:
    """Nudge the topic weight in the user's interest graph based on feedback."""
    snapshot = (
        client.table("interest_snapshots").select("interest_graph").eq("user_id", user_id).maybe_single().execute()
    )
    if not snapshot or not snapshot.data:
        return

    graph = snapshot.data.get("interest_graph", {})
    topics = graph.get("topics", [])

    delta = 0.05 if vote == "up" else -0.03
    updated = False

    for t in topics:
        if t["topic"].lower() == topic.lower():
            t["weight"] = round(max(0.01, min(1.0, t["weight"] + delta)), 3)
            updated = True
            break

    if updated:
        graph["topics"] = topics
        client.table("interest_snapshots").update(
            {"interest_graph": graph, "synced_at": datetime.utcnow().isoformat()}
        ).eq("user_id", user_id).execute()


# ── Endpoint ──────────────────────────────────────────────────────


@router.get("/vote")
async def record_vote(
    user_id: str = Query(...),
    item_id: str = Query(...),
    vote: str = Query(..., regex="^(up|down)$"),
    topic: str = Query(default=""),
):
    """Record a feedback vote from a digest email link.

    Stores the vote and optionally adjusts interest weights.
    Returns a simple thank-you HTML page (since this is opened in a browser).
    """
    client = get_service_client()

    # Store the feedback row (upsert so double-clicks don't duplicate)
    client.table("digest_feedback").upsert(
        {
            "user_id": user_id,
            "item_id": item_id,
            "vote": vote,
            "topic": topic,
            "voted_at": datetime.utcnow().isoformat(),
        },
        on_conflict="user_id,item_id",
    ).execute()

    # Adjust interest weight if we know the topic
    if topic:
        try:
            _adjust_interest_weight(client, user_id, topic, vote)
        except Exception as e:
            print(f"Weight adjustment failed: {e}")

    emoji = "&#128077;" if vote == "up" else "&#128078;"
    label = "Glad you liked it!" if vote == "up" else "Thanks, we'll improve."

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Feedback Recorded</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       display: flex; align-items: center; justify-content: center; min-height: 100vh;
       margin: 0; background: #fafafa; color: #1a1a1a; }}
.card {{ text-align: center; padding: 48px; background: #fff; border-radius: 16px;
         box-shadow: 0 1px 3px rgba(0,0,0,.08); max-width: 400px; }}
.emoji {{ font-size: 48px; margin-bottom: 16px; }}
h1 {{ font-size: 20px; margin: 0 0 8px; }}
p {{ color: #6b7280; font-size: 14px; margin: 0; }}
</style></head>
<body><div class="card">
<div class="emoji">{emoji}</div>
<h1>{label}</h1>
<p>Your feedback helps Persnally learn what matters to you.</p>
</div></body></html>"""

    return HTMLResponse(content=html)
