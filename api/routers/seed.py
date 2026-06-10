"""Seed API — Analyze GitHub repos/stars to bootstrap the interest graph for new users."""

import traceback
from collections import defaultdict
from datetime import datetime

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from middleware.auth_middleware import get_current_user
from services.supabase_client import get_service_client

router = APIRouter(prefix="/seed", tags=["seed"])

# ── Category mapping ──────────────────────────────────────────────

TOPIC_CATEGORY_MAP = {
    # Frontend
    "react": "technology",
    "vue": "technology",
    "angular": "technology",
    "svelte": "technology",
    "css": "technology",
    "html": "technology",
    "javascript": "technology",
    "typescript": "technology",
    "nextjs": "technology",
    "tailwindcss": "technology",
    # Backend
    "python": "technology",
    "go": "technology",
    "rust": "technology",
    "java": "technology",
    "ruby": "technology",
    "c": "technology",
    "c++": "technology",
    "c#": "technology",
    "kotlin": "technology",
    "swift": "technology",
    "php": "technology",
    "elixir": "technology",
    "scala": "technology",
    # AI/ML
    "machine-learning": "technology",
    "ai": "technology",
    "tensorflow": "technology",
    "pytorch": "technology",
    "deep-learning": "technology",
    "nlp": "technology",
    "computer-vision": "technology",
    "data-science": "technology",
    # DevOps
    "docker": "technology",
    "kubernetes": "technology",
    "terraform": "technology",
    "aws": "technology",
    "gcp": "technology",
    "azure": "technology",
    "ci-cd": "technology",
    "devops": "technology",
    # Business
    "startup": "business",
    "business": "business",
    "saas": "business",
    "marketing": "business",
    "entrepreneurship": "business",
    "fintech": "business",
    # Career
    "career": "career",
    "interview": "career",
    "resume": "career",
    "freelance": "career",
    "open-source": "career",
    # Design
    "design": "design",
    "ui": "design",
    "ux": "design",
    "figma": "design",
    # Science
    "bioinformatics": "science",
    "physics": "science",
    "mathematics": "science",
}

GITHUB_API_BASE = "https://api.github.com"
GITHUB_HEADERS_BASE = {"Accept": "application/vnd.github+json"}


def _normalize_topic(raw: str) -> str:
    """Lowercase, strip whitespace, replace spaces with hyphens."""
    return raw.strip().lower().replace(" ", "-").replace("_", "-")


def _category_for(topic: str) -> str:
    """Resolve category for a topic, defaulting to 'technology'."""
    return TOPIC_CATEGORY_MAP.get(topic, "technology")


async def _fetch_github_json(http: httpx.AsyncClient, url: str, token: str, params: dict | None = None) -> list | None:
    """GET a GitHub API endpoint; return parsed JSON list or None on error/rate-limit."""
    headers = {**GITHUB_HEADERS_BASE, "Authorization": f"Bearer {token}"}
    resp = await http.get(url, headers=headers, params=params)
    if resp.status_code == 403:
        print(f"GitHub rate limit hit for {url}")
        return None
    if resp.status_code != 200:
        print(f"GitHub API error {resp.status_code} for {url}")
        return None
    return resp.json()


async def _run_github_seed(user_id: str, job_id: str) -> None:
    """Background task: fetch GitHub data and build an initial interest graph."""
    client = get_service_client()
    try:
        # Mark job running
        client.table("analysis_jobs").update({"status": "running"}).eq("id", job_id).execute()

        # 1. Get GitHub token
        account = (
            client.table("connected_accounts")
            .select("access_token")
            .eq("user_id", user_id)
            .eq("provider", "github")
            .maybe_single()
            .execute()
        )
        if not account or not account.data:
            client.table("analysis_jobs").update({"status": "failed", "error": "GitHub not connected"}).eq(
                "id", job_id
            ).execute()
            return

        token = account.data["access_token"]

        # 2. Fetch GitHub data concurrently
        async with httpx.AsyncClient(timeout=30) as http:
            repos_data = await _fetch_github_json(
                http, f"{GITHUB_API_BASE}/user/repos", token, {"sort": "updated", "per_page": "30"}
            )
            starred_data = await _fetch_github_json(
                http, f"{GITHUB_API_BASE}/user/starred", token, {"sort": "updated", "per_page": "20"}
            )

        repos = repos_data or []
        starred = starred_data or []

        # 3. Fetch onboarding interests from user_preferences
        prefs_result = (
            client.table("user_preferences").select("interests").eq("user_id", user_id).maybe_single().execute()
        )
        onboarding_interests: list[str] = []
        if prefs_result and prefs_result.data and prefs_result.data.get("interests"):
            raw = prefs_result.data["interests"]
            if isinstance(raw, list):
                onboarding_interests = [_normalize_topic(i) for i in raw if i]

        # 4. Aggregate counts
        lang_counts: dict[str, int] = defaultdict(int)
        repo_topic_counts: dict[str, int] = defaultdict(int)
        star_topic_counts: dict[str, int] = defaultdict(int)
        repo_topic_entities: dict[str, set[str]] = defaultdict(set)

        for repo in repos:
            lang = repo.get("language")
            if lang:
                lang_counts[_normalize_topic(lang)] += 1
            for t in repo.get("topics", []):
                nt = _normalize_topic(t)
                repo_topic_counts[nt] += 1
                # Collect related entities from repo description
                if repo.get("description"):
                    repo_topic_entities[nt].add(repo["name"])

        for repo in starred:
            for t in repo.get("topics", []):
                star_topic_counts[_normalize_topic(t)] += 1

        # 5. Build topic list
        topics: list[dict] = []
        seen: set[str] = set()

        # Own repo languages
        for lang, count in lang_counts.items():
            weight = min(count / 5, 0.8)
            topics.append(
                {
                    "topic": lang,
                    "weight": round(weight, 2),
                    "category": _category_for(lang),
                    "intent": "building",
                    "entities": [],
                    "sentiment_balance": 0.5,
                }
            )
            seen.add(lang)

        # Own repo topics
        for topic, count in repo_topic_counts.items():
            if topic in seen:
                continue
            weight = min(count / 3, 0.7)
            entities = sorted(repo_topic_entities.get(topic, set()))[:5]
            topics.append(
                {
                    "topic": topic,
                    "weight": round(weight, 2),
                    "category": _category_for(topic),
                    "intent": "building",
                    "entities": entities,
                    "sentiment_balance": 0.5,
                }
            )
            seen.add(topic)

        # Starred repo topics
        for topic, count in star_topic_counts.items():
            if topic in seen:
                continue
            weight = min(count / 5, 0.5)
            topics.append(
                {
                    "topic": topic,
                    "weight": round(weight, 2),
                    "category": _category_for(topic),
                    "intent": "exploring",
                    "entities": [],
                    "sentiment_balance": 0.5,
                }
            )
            seen.add(topic)

        # Onboarding interests
        for interest in onboarding_interests:
            if interest in seen:
                continue
            topics.append(
                {
                    "topic": interest,
                    "weight": 0.4,
                    "category": _category_for(interest),
                    "intent": "learning",
                    "entities": [],
                    "sentiment_balance": 0.5,
                }
            )
            seen.add(interest)

        # 6. Compute category breakdowns
        category_weights: dict[str, float] = defaultdict(float)
        for t in topics:
            category_weights[t["category"]] += t["weight"]

        total_weight = sum(category_weights.values()) or 1.0
        categories = {cat: round((w / total_weight) * 100, 1) for cat, w in category_weights.items()}

        total_signals = len(repos) + len(starred) + len(onboarding_interests)

        interest_graph = {
            "topics": topics,
            "categories": categories,
            "total_signals": total_signals,
        }

        # 7. Build balanced allocation
        balanced_allocation: dict[str, dict] = {}
        for t in topics:
            cat = t["category"]
            if cat not in balanced_allocation:
                balanced_allocation[cat] = {"allocation": 0, "topics": []}
            balanced_allocation[cat]["topics"].append(t["topic"])
        for cat in balanced_allocation:
            balanced_allocation[cat]["allocation"] = round(categories.get(cat, 0))

        # 8. Upsert interest snapshot
        client.table("interest_snapshots").upsert(
            {
                "user_id": user_id,
                "interest_graph": interest_graph,
                "balanced_allocation": balanced_allocation,
                "total_signals": total_signals,
                "synced_at": datetime.utcnow().isoformat(),
            },
            on_conflict="user_id",
        ).execute()

        # 9. Mark job complete
        client.table("analysis_jobs").update(
            {
                "status": "completed",
                "result_summary": f"Seeded {len(topics)} topics from {len(repos)} repos, "
                f"{len(starred)} stars, {len(onboarding_interests)} onboarding interests",
            }
        ).eq("id", job_id).execute()

    except Exception as e:
        print(f"GitHub seed error: {type(e).__name__}: {e}")
        traceback.print_exc()
        try:
            client.table("analysis_jobs").update({"status": "failed", "error": f"{type(e).__name__}: {e}"}).eq(
                "id", job_id
            ).execute()
        except Exception:
            pass


# ── Endpoints ──────────────────────────────────────────────────────


@router.post("/github")
async def seed_from_github(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """Analyze GitHub repos & stars to bootstrap the interest graph. Runs in background."""
    client = get_service_client()

    # Check for already-running seed job
    try:
        running = (
            client.table("analysis_jobs")
            .select("id")
            .eq("user_id", user["id"])
            .eq("job_type", "github_seed")
            .in_("status", ["pending", "running"])
            .maybe_single()
            .execute()
        )
        if running and running.data:
            return {"job_id": running.data["id"], "status": "already_running"}
    except Exception:
        pass

    # Verify GitHub is connected before queuing
    account = (
        client.table("connected_accounts")
        .select("access_token")
        .eq("user_id", user["id"])
        .eq("provider", "github")
        .maybe_single()
        .execute()
    )
    if not account or not account.data:
        raise HTTPException(status_code=400, detail="GitHub account not connected. Please connect GitHub first.")

    # Create job
    job = (
        client.table("analysis_jobs")
        .insert({"user_id": user["id"], "job_type": "github_seed", "status": "pending"})
        .execute()
    )
    job_id = job.data[0]["id"]

    background_tasks.add_task(_run_github_seed, user["id"], job_id)

    return {"job_id": job_id, "status": "pending"}


@router.get("/github/{job_id}")
async def get_seed_status(job_id: str, user: dict = Depends(get_current_user)):
    """Check the status of a GitHub seed job."""
    client = get_service_client()
    try:
        result = client.table("analysis_jobs").select("*").eq("id", job_id).eq("user_id", user["id"]).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": result.data["id"],
        "status": result.data["status"],
        "job_type": result.data["job_type"],
        "result_summary": result.data.get("result_summary"),
        "error": result.data.get("error"),
        "created_at": result.data["created_at"],
    }
