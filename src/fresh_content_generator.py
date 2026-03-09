"""
Fresh Content Generator - Fetches live content from GitHub and HackerNews
Matches results to user interests for personalized daily digests
"""
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .config import get_config
from .cache import cache_get, cache_set, cache_key
from .topic_utils import expand_terms, relevance_score


class FreshContentGenerator:
    def __init__(self):
        config = get_config()
        self.github_token = config.GITHUB_TOKEN
        self._github_headers = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            self._github_headers["Authorization"] = f"Bearer {self.github_token}"

    async def generate_fresh_daily_5(self, user_profile: dict) -> List[Dict[str, Any]]:
        """Generate 5 pieces of genuinely fresh, well-written content.

        If the user_profile contains an interest_graph (from MCP digest flow),
        delegates to generate_from_interest_graph for targeted queries.
        """
        # Delegate to interest-graph-aware path when available
        if user_profile.get("interest_graph"):
            return await self.generate_from_interest_graph(user_profile)

        print("Generating FRESH Daily 5 content...")

        interests = [i.lower() for i in user_profile.get("interests", [])]

        # Fetch data from both sources in parallel
        hn_stories, gh_trending, gh_learning, gh_opportunity = await asyncio.gather(
            self._fetch_hn_top_stories(),
            self._fetch_github_trending(interests),
            self._fetch_github_learning(interests),
            self._fetch_github_opportunity(interests),
        )

        # Build the 5 slots
        daily_5 = [
            self._build_breaking(hn_stories, interests),
            self._build_trending(gh_trending, interests),
            self._build_opportunity(gh_opportunity, interests),
            self._build_learn(gh_learning, interests),
            self._build_insight(hn_stories, interests),
        ]

        return daily_5

    async def generate_from_interest_graph(self, user_profile: dict) -> List[Dict[str, Any]]:
        """Generate content driven by the MCP interest graph.

        Extracts the top 5 topics by weight and uses them as targeted search
        queries for GitHub and HN instead of generic trending fetches.
        Falls back to the standard generate_fresh_daily_5 path when no
        interest_graph is present.
        """
        interest_graph = user_profile.get("interest_graph")
        if not interest_graph:
            # Strip key so we don't recurse back here
            return await self.generate_fresh_daily_5(user_profile)

        topics = interest_graph.get("topics", [])
        if not topics:
            return await self.generate_fresh_daily_5(
                {k: v for k, v in user_profile.items() if k != "interest_graph"}
            )

        # Top 5 topics by weight
        sorted_topics = sorted(topics, key=lambda t: t.get("weight", 0), reverse=True)[:5]
        top_queries = [t["topic"] for t in sorted_topics]

        # Expand queries with synonyms for broader GitHub coverage
        expanded_queries = expand_terms(top_queries)
        # Keep original topics first, then add a few synonym-expanded terms (cap to avoid API spam)
        extra_queries = [q for q in expanded_queries if q not in [t.lower() for t in top_queries]][:3]
        all_queries = top_queries + extra_queries

        print(f"Interest-graph mode: querying for top topics {top_queries} (+ {len(extra_queries)} synonym expansions)")

        interests = [i.lower() for i in user_profile.get("interests", [])]

        # Fetch HN stories once, then targeted GitHub searches per topic
        hn_coro = self._fetch_hn_top_stories(limit=50)
        gh_trending_coros = [self._fetch_github_trending(interests, query=q) for q in all_queries]
        gh_learning_coro = self._fetch_github_learning(interests)
        gh_opportunity_coro = self._fetch_github_opportunity(interests)

        results = await asyncio.gather(
            hn_coro, gh_learning_coro, gh_opportunity_coro, *gh_trending_coros
        )

        hn_stories = results[0]
        gh_learning = results[1]
        gh_opportunity = results[2]
        gh_trending_lists = results[3:]

        # Merge all targeted GitHub results, de-duplicate by repo id
        seen_ids = set()
        gh_trending_merged: List[Dict[str, Any]] = []
        for repo_list in gh_trending_lists:
            for repo in repo_list:
                rid = repo.get("id")
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    gh_trending_merged.append(repo)

        # Filter HN stories to those matching any interest-graph topic keyword (with synonym expansion)
        topic_keywords = set(expand_terms([kw for q in top_queries for kw in q.split()]))
        filtered_hn = [
            s for s in hn_stories
            if any(kw in s.get("title", "").lower() for kw in topic_keywords)
        ]
        # Fall back to full list if filter is too aggressive
        if len(filtered_hn) < 5:
            filtered_hn = hn_stories

        daily_5 = [
            self._build_breaking(filtered_hn, interests),
            self._build_trending(gh_trending_merged, interests),
            self._build_opportunity(gh_opportunity, interests),
            self._build_learn(gh_learning, interests),
            self._build_insight(filtered_hn, interests),
        ]

        return daily_5

    # ── Data fetching ─────────────────────────────────────────────

    async def _fetch_hn_top_stories(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Fetch top HackerNews stories with details."""
        ck = cache_key("hn_top_stories", str(limit))
        cached = cache_get(ck)
        if cached is not None:
            print("HackerNews: returning cached results")
            return cached
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://hacker-news.firebaseio.com/v0/topstories.json"
                )
                resp.raise_for_status()
                story_ids = resp.json()[:limit]

                tasks = [
                    client.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                    )
                    for sid in story_ids
                ]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                stories = []
                for r in responses:
                    if isinstance(r, Exception) or r.status_code != 200:
                        continue
                    data = r.json()
                    if data and data.get("title"):
                        stories.append(data)
                cache_set(ck, stories)
                return stories
        except Exception as e:
            print(f"HackerNews fetch failed: {e}")
            return []

    async def _fetch_github_trending(
        self, interests: List[str], query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch trending GitHub repos.

        When *query* is provided (interest-graph mode), search for that
        specific topic sorted by stars instead of generic "created in last
        7 days" trending.
        """
        if query:
            # Targeted search for a specific interest-graph topic
            search_q = f"{query} stars:>50"
            return await self._github_search(search_q, sort="stars")

        # Default: generic trending repos created in the last 7 days
        since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        search_q = f"created:>{since} stars:>10"
        if interests:
            search_q += f" {interests[0]}"
        return await self._github_search(search_q, sort="stars")

    async def _fetch_github_learning(
        self, interests: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch repos with learning/tutorial signals."""
        keywords = ["tutorial", "learn", "course", "awesome", "guide"]
        interest_part = interests[0] if interests else "programming"
        query = f"{interest_part} " + " OR ".join(keywords) + " in:name,description"
        return await self._github_search(query, sort="updated")

    async def _fetch_github_opportunity(
        self, interests: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch repos with contribution/hiring signals."""
        interest_part = interests[0] if interests else "opensource"
        query = (
            f"{interest_part} (good-first-issue OR help-wanted OR hiring OR contribute)"
            " in:name,description,topics"
        )
        return await self._github_search(query, sort="updated")

    async def _github_search(
        self, query: str, sort: str = "stars", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Run a GitHub search/repositories query."""
        ck = cache_key("gh_search", query, sort, str(limit))
        cached = cache_get(ck)
        if cached is not None:
            print(f"GitHub search: returning cached results for '{query}'")
            return cached
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": query,
                        "sort": sort,
                        "order": "desc",
                        "per_page": limit,
                    },
                    headers=self._github_headers,
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                cache_set(ck, items)
                return items
        except Exception as e:
            print(f"GitHub search failed for '{query}': {e}")
            return []

    # ── Interest matching ─────────────────────────────────────────

    @staticmethod
    def _relevance_score(text: str, interests: List[str]) -> int:
        """Relevance score using synonym expansion.

        Direct keyword match = 2 points, synonym match = 1 point.
        """
        return relevance_score(text, interests)

    def _best_hn_match(
        self, stories: List[Dict[str, Any]], interests: List[str], exclude_ids: set = None
    ) -> Optional[Dict[str, Any]]:
        """Return the HN story most relevant to interests."""
        if not stories:
            return None
        exclude_ids = exclude_ids or set()
        scored = []
        for s in stories:
            if s.get("id") in exclude_ids:
                continue
            title = s.get("title", "")
            score = self._relevance_score(title, interests)
            scored.append((score, s))
        scored.sort(key=lambda x: (-x[0], -x[1].get("score", 0)))
        return scored[0][1] if scored else None

    def _best_gh_match(
        self, repos: List[Dict[str, Any]], interests: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Return the GitHub repo most relevant to interests."""
        if not repos:
            return None
        scored = []
        for r in repos:
            blob = f"{r.get('name', '')} {r.get('description', '')} {' '.join(r.get('topics', []))}"
            score = self._relevance_score(blob, interests)
            scored.append((score, r))
        scored.sort(key=lambda x: (-x[0], -x[1].get("stargazers_count", 0)))
        return scored[0][1] if scored else None

    # ── Slot builders ─────────────────────────────────────────────

    def _build_breaking(
        self, hn_stories: List[Dict[str, Any]], interests: List[str]
    ) -> Dict[str, Any]:
        """BREAKING — top HN story matching interests."""
        story = self._best_hn_match(hn_stories, interests)
        if not story:
            return self._fallback("BREAKING", "HackerNews", "https://news.ycombinator.com")

        title = story.get("title", "Untitled")
        url = story.get("url") or f"https://news.ycombinator.com/item?id={story['id']}"
        hn_url = f"https://news.ycombinator.com/item?id={story['id']}"
        points = story.get("score", 0)
        comments = story.get("descendants", 0)

        return {
            "category": "BREAKING",
            "title": title,
            "description": (
                f"This story is trending on HackerNews right now with {points} points "
                f"and {comments} comments. The community discussion is active — "
                f"check the comments for expert takes and additional context."
            ),
            "action": f"Read the full story and join the discussion at {hn_url}",
            "url": url,
            "image_query": title,
            "meta_info": f"{points} points | {comments} comments | HackerNews",
        }

    def _build_trending(
        self, gh_repos: List[Dict[str, Any]], interests: List[str]
    ) -> Dict[str, Any]:
        """TRENDING — hot GitHub repo."""
        repo = self._best_gh_match(gh_repos, interests)
        if not repo:
            return self._fallback("TRENDING", "GitHub Trending", "https://github.com/trending")

        name = repo.get("full_name", "unknown/repo")
        desc = repo.get("description") or "No description provided."
        stars = repo.get("stargazers_count", 0)
        lang = repo.get("language") or "Various"
        url = repo.get("html_url", "https://github.com")
        created = repo.get("created_at", "")[:10]

        return {
            "category": "TRENDING",
            "title": f"{name} — rapidly gaining stars on GitHub",
            "description": (
                f"{desc}\n\n"
                f"This {lang} project was created on {created} and has already "
                f"earned {stars:,} stars. It is trending in the developer community "
                f"right now."
            ),
            "action": f"Star the repo and explore the codebase at {url}",
            "url": url,
            "image_query": f"{name} {lang} github open source",
            "meta_info": f"{stars:,} stars | {lang} | Created {created}",
        }

    def _build_opportunity(
        self, gh_repos: List[Dict[str, Any]], interests: List[str]
    ) -> Dict[str, Any]:
        """OPPORTUNITY — repo with contribution/hiring signals."""
        repo = self._best_gh_match(gh_repos, interests)
        if not repo:
            return self._fallback(
                "OPPORTUNITY",
                "GitHub good-first-issues",
                "https://github.com/topics/good-first-issue",
            )

        name = repo.get("full_name", "unknown/repo")
        desc = repo.get("description") or "No description provided."
        stars = repo.get("stargazers_count", 0)
        issues = repo.get("open_issues_count", 0)
        url = repo.get("html_url", "https://github.com")
        lang = repo.get("language") or "Various"

        return {
            "category": "OPPORTUNITY",
            "title": f"Contribute to {name} — {issues} open issues waiting",
            "description": (
                f"{desc}\n\n"
                f"This {lang} project has {stars:,} stars and {issues} open issues. "
                f"It is actively looking for contributors. Open-source contributions "
                f"here could boost your portfolio and connect you with maintainers."
            ),
            "action": f"Browse open issues and find one that matches your skills at {url}/issues",
            "url": f"{url}/issues",
            "image_query": f"{name} open source contribute",
            "meta_info": f"{stars:,} stars | {issues} open issues | {lang}",
        }

    def _build_learn(
        self, gh_repos: List[Dict[str, Any]], interests: List[str]
    ) -> Dict[str, Any]:
        """LEARN — educational/tutorial repo."""
        repo = self._best_gh_match(gh_repos, interests)
        if not repo:
            return self._fallback(
                "LEARN",
                "GitHub learning resources",
                "https://github.com/topics/tutorial",
            )

        name = repo.get("full_name", "unknown/repo")
        desc = repo.get("description") or "No description provided."
        stars = repo.get("stargazers_count", 0)
        url = repo.get("html_url", "https://github.com")
        lang = repo.get("language") or "Various"

        return {
            "category": "LEARN",
            "title": f"{name} — a learning resource worth bookmarking",
            "description": (
                f"{desc}\n\n"
                f"With {stars:,} stars, this {lang} resource is well-regarded by "
                f"the community. Dive in to sharpen your skills."
            ),
            "action": f"Start learning at {url}",
            "url": url,
            "image_query": f"{name} tutorial learn {lang}",
            "meta_info": f"{stars:,} stars | {lang} | Learning resource",
        }

    def _build_insight(
        self, hn_stories: List[Dict[str, Any]], interests: List[str]
    ) -> Dict[str, Any]:
        """INSIGHT — HN story about industry trends (avoid duplicating BREAKING pick)."""
        # Pick second-best match to avoid duplicating the BREAKING slot
        best = self._best_hn_match(hn_stories, interests)
        exclude = {best["id"]} if best else set()
        story = self._best_hn_match(hn_stories, interests, exclude_ids=exclude)

        # If no second match, try the first non-best story by raw score
        if not story and hn_stories:
            for s in sorted(hn_stories, key=lambda x: -x.get("score", 0)):
                if s.get("id") not in exclude:
                    story = s
                    break

        if not story:
            return self._fallback("INSIGHT", "HackerNews", "https://news.ycombinator.com")

        title = story.get("title", "Untitled")
        url = story.get("url") or f"https://news.ycombinator.com/item?id={story['id']}"
        hn_url = f"https://news.ycombinator.com/item?id={story['id']}"
        points = story.get("score", 0)
        comments = story.get("descendants", 0)

        return {
            "category": "INSIGHT",
            "title": title,
            "description": (
                f"An industry discussion gaining traction on HackerNews with "
                f"{points} points and {comments} comments. The comment thread "
                f"often contains valuable perspectives from practitioners."
            ),
            "action": f"Read the discussion at {hn_url}",
            "url": url,
            "image_query": title,
            "meta_info": f"{points} points | {comments} comments | HackerNews",
        }

    # ── Fallback ──────────────────────────────────────────────────

    @staticmethod
    def _fallback(category: str, source: str, url: str) -> Dict[str, Any]:
        """Honest fallback when an API call fails or returns no results."""
        return {
            "category": category,
            "title": f"Check out today's top picks on {source}",
            "description": (
                f"We could not fetch a personalised item for this slot right now. "
                f"Head over to {source} to browse the latest content yourself."
            ),
            "action": f"Visit {url}",
            "url": url,
            "image_query": f"{source} technology",
            "meta_info": f"Source: {source}",
        }
