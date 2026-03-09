"""
Web Opportunity Finder - Searches the web for current opportunities
Uses GitHub Search API to find hackathons, jobs, tools, and contribution opportunities
"""

import asyncio
import json
from datetime import datetime
from typing import Any

import httpx

from .cache import cache_get, cache_key, cache_set
from .config import get_config
from .topic_utils import expand_terms

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
GITHUB_ISSUES_URL = "https://api.github.com/search/issues"
TIMEOUT = 10.0


class WebOpportunityFinder:
    def __init__(self):
        config = get_config()
        self.github_token = config.GITHUB_TOKEN
        self._headers = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            self._headers["Authorization"] = f"Bearer {self.github_token}"

    async def find_opportunities(self, user_profile: dict, behavior_data: dict) -> dict[str, Any]:
        """
        Find real opportunities by searching the web
        Returns categorized opportunities: hackathons, events, tools, job_opportunities
        """
        location = user_profile.get("location", "")
        interests = user_profile.get("interests", [])
        skills = user_profile.get("skills", [])

        # Build search queries based on user profile
        queries = self._build_search_queries(location, interests, skills)

        print(f"[WebFinder] Searching GitHub with {len(interests)} interests, {len(skills)} skills")

        # Derive search terms from both interests and skills, expanded with synonyms
        base_terms = list(set(interests[:3] + skills[:3]))
        expanded = expand_terms(base_terms)
        # Use original terms plus up to 3 synonym expansions to broaden search
        extra = [t for t in expanded if t not in [b.lower() for b in base_terms]][:3]
        search_terms = base_terms + extra
        current_year = datetime.now().year

        # Run all searches in parallel
        async with httpx.AsyncClient(headers=self._headers, timeout=TIMEOUT) as client:
            tasks = [
                self._search_hackathons(client, search_terms, current_year),
                self._search_job_repos(client, search_terms),
                self._search_contribution_opportunities(client, search_terms),
                self._search_trending_tools(client, search_terms),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        hackathons = results[0] if not isinstance(results[0], BaseException) else []
        job_opportunities = results[1] if not isinstance(results[1], BaseException) else []
        events = results[2] if not isinstance(results[2], BaseException) else []
        tools = results[3] if not isinstance(results[3], BaseException) else []

        # Log errors for debugging
        for i, r in enumerate(results):
            if isinstance(r, BaseException):
                label = ["hackathons", "jobs", "contributions", "tools"][i]
                print(f"[WebFinder] {label} search failed: {r}")

        opportunities = {
            "hackathons": hackathons,
            "events": events,
            "tools": tools,
            "job_opportunities": job_opportunities,
        }

        total = sum(len(v) for v in opportunities.values())
        print(f"[WebFinder] Found {total} total opportunities")

        return {
            "search_queries": queries,
            "opportunities": opportunities,
            "location_hint": location,
            "interest_hints": interests,
        }

    async def _search_hackathons(self, client: httpx.AsyncClient, terms: list[str], year: int) -> list[dict]:
        """Search GitHub for hackathon repos updated recently."""
        results = []
        for term in terms[:2]:
            q = f"hackathon {year} {term}"
            items = await self._github_repo_search(client, q, sort="updated", per_page=5)
            for item in items:
                results.append(
                    {
                        "title": item["name"],
                        "description": (item.get("description") or "")[:200],
                        "url": item["html_url"],
                        "source": "github",
                        "stars": item.get("stargazers_count", 0),
                        "updated": item.get("updated_at", ""),
                        "type": "hackathon",
                    }
                )
        # Dedupe by url
        return _dedupe(results)

    async def _search_job_repos(self, client: httpx.AsyncClient, terms: list[str]) -> list[dict]:
        """Search GitHub for hiring/job-related repos matching user's stack."""
        results = []
        for term in terms[:2]:
            q = f"hiring {term}"
            items = await self._github_repo_search(client, q, sort="updated", per_page=5)
            for item in items:
                results.append(
                    {
                        "title": item["name"],
                        "description": (item.get("description") or "")[:200],
                        "url": item["html_url"],
                        "source": "github",
                        "stars": item.get("stargazers_count", 0),
                        "updated": item.get("updated_at", ""),
                        "type": "job",
                    }
                )
        return _dedupe(results)

    async def _search_contribution_opportunities(self, client: httpx.AsyncClient, terms: list[str]) -> list[dict]:
        """Search GitHub issues labeled good-first-issue matching user's languages."""
        results = []
        for term in terms[:2]:
            q = f"label:good-first-issue language:{term} state:open"
            items = await self._github_issue_search(client, q, sort="created", per_page=5)
            for item in items:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "description": (item.get("body") or "")[:200],
                        "url": item["html_url"],
                        "source": "github",
                        "comments": item.get("comments", 0),
                        "created": item.get("created_at", ""),
                        "type": "contribution",
                        "labels": [l["name"] for l in item.get("labels", [])[:5]],
                    }
                )
        return _dedupe(results)

    async def _search_trending_tools(self, client: httpx.AsyncClient, terms: list[str]) -> list[dict]:
        """Search GitHub for trending tools/libraries in user's interest areas."""
        results = []
        for term in terms[:2]:
            q = f"{term} tool"
            items = await self._github_repo_search(client, q, sort="stars", per_page=5)
            for item in items:
                results.append(
                    {
                        "title": item["name"],
                        "description": (item.get("description") or "")[:200],
                        "url": item["html_url"],
                        "source": "github",
                        "stars": item.get("stargazers_count", 0),
                        "updated": item.get("updated_at", ""),
                        "type": "tool",
                    }
                )
        return _dedupe(results)

    async def _github_repo_search(
        self, client: httpx.AsyncClient, q: str, sort: str = "updated", per_page: int = 5
    ) -> list[dict]:
        """Execute a GitHub repository search. Returns list of repo items."""
        ck = cache_key("wf_repo_search", q, sort, str(per_page))
        cached = cache_get(ck)
        if cached is not None:
            print(f"[WebFinder] Returning cached repo search for '{q}'")
            return cached
        try:
            resp = await client.get(GITHUB_SEARCH_URL, params={"q": q, "sort": sort, "per_page": per_page})
            resp.raise_for_status()
            items = resp.json().get("items", [])
            cache_set(ck, items)
            return items
        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError) as e:
            print(f"[WebFinder] GitHub repo search failed for '{q}': {e}")
            return []

    async def _github_issue_search(
        self, client: httpx.AsyncClient, q: str, sort: str = "created", per_page: int = 5
    ) -> list[dict]:
        """Execute a GitHub issue search. Returns list of issue items."""
        ck = cache_key("wf_issue_search", q, sort, str(per_page))
        cached = cache_get(ck)
        if cached is not None:
            print(f"[WebFinder] Returning cached issue search for '{q}'")
            return cached
        try:
            resp = await client.get(GITHUB_ISSUES_URL, params={"q": q, "sort": sort, "per_page": per_page})
            resp.raise_for_status()
            items = resp.json().get("items", [])
            cache_set(ck, items)
            return items
        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError) as e:
            print(f"[WebFinder] GitHub issue search failed for '{q}': {e}")
            return []

    def _build_search_queries(self, location: str, interests: list[str], skills: list[str]) -> list[str]:
        """Build targeted search queries - GLOBAL first, local second"""

        queries = []
        current_month = datetime.now().strftime("%B %Y")

        # GLOBAL queries first (most important)
        for interest in interests[:3]:
            queries.append(f"new {interest} tools {current_month}")
            queries.append(f"{interest} latest release {current_month}")
            queries.append(f"best {interest} projects {current_month}")

        # Skill-based queries (global)
        for skill in skills[:3]:
            queries.append(f"{skill} latest features {current_month}")
            queries.append(f"{skill} new updates {current_month}")

        # Location-based queries (secondary - only 2-3)
        if location:
            city = location.split(",")[0].strip()
            queries.append(f"{city} tech events {current_month}")
            queries.append(f"{location} hackathon {current_month}")

        return queries


def _dedupe(items: list[dict]) -> list[dict]:
    """Remove duplicates by url."""
    seen = set()
    out = []
    for item in items:
        url = item.get("url", "")
        if url not in seen:
            seen.add(url)
            out.append(item)
    return out
