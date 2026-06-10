"""
Cloudflare Browser Rendering Crawler — Real content sourcing for Persnally digests.

Uses Cloudflare's /crawl REST API to fetch real articles from curated sources,
driven by the user's interest graph. Replaces AI-hallucinated content with
actual URLs, titles, and summaries from the web.

Flow:
1. Map interest graph topics → source URLs (dev.to, HN, lobste.rs, etc.)
2. Submit crawl jobs to Cloudflare /crawl endpoint
3. Poll for results (async, fits existing job pattern)
4. Extract structured content (title, URL, summary) via markdown + JSON extraction
5. Return as `fresh_updates` for the AI editorial engine to summarize/rank
"""

import asyncio
from typing import Any

import httpx

from .config import get_config

# Cloudflare Browser Rendering API base
CF_API_BASE = "https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl"

# Crawl timeout: max time to wait for a single crawl job
CRAWL_POLL_TIMEOUT = 60  # seconds
CRAWL_POLL_INTERVAL = 3  # seconds

# ── Source Registry ────────────────────────────────────────────
# Maps interest categories to crawlable source URLs.
# Each source has a base URL and optional include patterns.

SOURCE_REGISTRY: dict[str, list[dict[str, Any]]] = {
    "frontend": [
        {"url": "https://dev.to/t/frontend", "label": "DEV Community"},
        {"url": "https://dev.to/t/react", "label": "DEV Community"},
        {"url": "https://dev.to/t/javascript", "label": "DEV Community"},
        {"url": "https://www.smashingmagazine.com/articles/", "label": "Smashing Magazine"},
        {"url": "https://css-tricks.com", "label": "CSS-Tricks"},
        {"url": "https://www.reddit.com/r/reactjs/top/.json?t=week", "label": "r/reactjs"},
    ],
    "backend": [
        {"url": "https://dev.to/t/backend", "label": "DEV Community"},
        {"url": "https://dev.to/t/python", "label": "DEV Community"},
        {"url": "https://dev.to/t/go", "label": "DEV Community"},
        {"url": "https://www.reddit.com/r/python/top/.json?t=week", "label": "r/python"},
        {"url": "https://www.reddit.com/r/golang/top/.json?t=week", "label": "r/golang"},
        {"url": "https://blog.pragmaticengineer.com", "label": "Pragmatic Engineer"},
    ],
    "ai_ml": [
        {"url": "https://dev.to/t/ai", "label": "DEV Community"},
        {"url": "https://dev.to/t/machinelearning", "label": "DEV Community"},
        {"url": "https://huggingface.co/blog", "label": "Hugging Face Blog"},
        {"url": "https://www.reddit.com/r/MachineLearning/top/.json?t=week", "label": "r/MachineLearning"},
        {"url": "https://lilianweng.github.io", "label": "Lil'Log (AI Research)"},
        {"url": "https://simonwillison.net", "label": "Simon Willison"},
    ],
    "devops": [
        {"url": "https://dev.to/t/devops", "label": "DEV Community"},
        {"url": "https://dev.to/t/docker", "label": "DEV Community"},
        {"url": "https://www.reddit.com/r/devops/top/.json?t=week", "label": "r/devops"},
        {"url": "https://www.cncf.io/blog/", "label": "CNCF Blog"},
    ],
    "mobile": [
        {"url": "https://dev.to/t/mobile", "label": "DEV Community"},
        {"url": "https://dev.to/t/reactnative", "label": "DEV Community"},
        {"url": "https://www.reddit.com/r/FlutterDev/top/.json?t=week", "label": "r/FlutterDev"},
    ],
    "security": [
        {"url": "https://dev.to/t/security", "label": "DEV Community"},
        {"url": "https://www.reddit.com/r/netsec/top/.json?t=week", "label": "r/netsec"},
        {"url": "https://portswigger.net/daily-swig", "label": "Daily Swig"},
    ],
    "blockchain": [
        {"url": "https://dev.to/t/blockchain", "label": "DEV Community"},
        {"url": "https://dev.to/t/web3", "label": "DEV Community"},
        {"url": "https://www.reddit.com/r/ethereum/top/.json?t=week", "label": "r/ethereum"},
    ],
    "data": [
        {"url": "https://dev.to/t/database", "label": "DEV Community"},
        {"url": "https://www.reddit.com/r/dataengineering/top/.json?t=week", "label": "r/dataengineering"},
    ],
    "systems": [
        {"url": "https://dev.to/t/linux", "label": "DEV Community"},
        {"url": "https://www.reddit.com/r/rust/top/.json?t=week", "label": "r/rust"},
        {"url": "https://www.reddit.com/r/cpp/top/.json?t=week", "label": "r/cpp"},
    ],
    "gamedev": [
        {"url": "https://dev.to/t/gamedev", "label": "DEV Community"},
        {"url": "https://www.reddit.com/r/gamedev/top/.json?t=week", "label": "r/gamedev"},
    ],
    "general": [
        {"url": "https://lobste.rs", "label": "Lobsters"},
        {"url": "https://dev.to/t/programming", "label": "DEV Community"},
        {"url": "https://www.reddit.com/r/programming/top/.json?t=week", "label": "r/programming"},
        {"url": "https://newsletter.pragmaticengineer.com", "label": "Pragmatic Engineer"},
    ],
}

# Topic keyword → category mapping for interest graph topics
TOPIC_CATEGORY_MAP: dict[str, str] = {
    # Frontend
    "react": "frontend",
    "vue": "frontend",
    "angular": "frontend",
    "svelte": "frontend",
    "nextjs": "frontend",
    "css": "frontend",
    "tailwind": "frontend",
    "typescript": "frontend",
    "javascript": "frontend",
    "html": "frontend",
    "astro": "frontend",
    "remix": "frontend",
    # Backend
    "python": "backend",
    "django": "backend",
    "fastapi": "backend",
    "flask": "backend",
    "nodejs": "backend",
    "go": "backend",
    "java": "backend",
    "ruby": "backend",
    "rails": "backend",
    "elixir": "backend",
    "spring": "backend",
    "graphql": "backend",
    # Systems
    "rust": "systems",
    "c": "systems",
    "cpp": "systems",
    "zig": "systems",
    "wasm": "systems",
    "webassembly": "systems",
    # AI/ML
    "ai": "ai_ml",
    "ml": "ai_ml",
    "machine learning": "ai_ml",
    "deep learning": "ai_ml",
    "llm": "ai_ml",
    "gpt": "ai_ml",
    "claude": "ai_ml",
    "pytorch": "ai_ml",
    "tensorflow": "ai_ml",
    "transformers": "ai_ml",
    "nlp": "ai_ml",
    "computer vision": "ai_ml",
    "langchain": "ai_ml",
    "rag": "ai_ml",
    # DevOps
    "docker": "devops",
    "kubernetes": "devops",
    "ci/cd": "devops",
    "terraform": "devops",
    "aws": "devops",
    "gcp": "devops",
    "azure": "devops",
    "linux": "devops",
    "nginx": "devops",
    # Mobile
    "ios": "mobile",
    "android": "mobile",
    "swift": "mobile",
    "kotlin": "mobile",
    "flutter": "mobile",
    "react native": "mobile",
    # Security
    "security": "security",
    "cybersecurity": "security",
    "encryption": "security",
    "pentest": "security",
    # Blockchain
    "blockchain": "blockchain",
    "web3": "blockchain",
    "solidity": "blockchain",
    "ethereum": "blockchain",
    "crypto": "blockchain",
    # Data
    "postgresql": "data",
    "mysql": "data",
    "mongodb": "data",
    "redis": "data",
    "sql": "data",
    "data engineering": "data",
    "spark": "data",
    "kafka": "data",
    # Game Dev
    "gamedev": "gamedev",
    "unity": "gamedev",
    "unreal": "gamedev",
    "godot": "gamedev",
    "game development": "gamedev",
}


class CloudflareCrawler:
    """Fetches real web content using Cloudflare Browser Rendering /crawl API."""

    def __init__(self):
        config = get_config()
        self.account_id = getattr(config, "CLOUDFLARE_ACCOUNT_ID", None)
        self.api_token = getattr(config, "CLOUDFLARE_API_TOKEN", None)
        self._enabled = bool(self.account_id and self.api_token)

        if not self._enabled:
            print("[CloudflareCrawler] Disabled — CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN not set")

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def crawl_for_interests(
        self,
        topics: list[dict[str, Any]],
        categories: dict[str, float],
        max_sources: int = 5,
        items_per_source: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Crawl real content based on interest graph topics.

        Returns a list of structured articles:
        [
            {
                "title": "Article Title",
                "url": "https://...",
                "summary": "Brief description from the page",
                "source": "DEV Community",
                "category": "frontend",
                "crawled": True,
            }
        ]
        """
        if not self._enabled:
            print("[CloudflareCrawler] Skipping — not configured")
            return []

        # Step 1: Map topics → source URLs
        sources = self._select_sources(topics, categories, max_sources)
        if not sources:
            print("[CloudflareCrawler] No matching sources for user interests")
            return []

        print(f"[CloudflareCrawler] Crawling {len(sources)} sources: {[s['label'] for s in sources]}")

        # Step 2: Submit crawl jobs in parallel
        async with httpx.AsyncClient(timeout=90.0) as client:
            crawl_tasks = [self._crawl_source(client, source, items_per_source) for source in sources]
            results = await asyncio.gather(*crawl_tasks, return_exceptions=True)

        # Step 3: Flatten and deduplicate
        all_articles: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                print(f"[CloudflareCrawler] Source {sources[i]['label']} failed: {result}")
                continue
            for article in result:
                url = article.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_articles.append(article)

        print(f"[CloudflareCrawler] Fetched {len(all_articles)} unique articles")
        return all_articles

    def _select_sources(
        self,
        topics: list[dict[str, Any]],
        categories: dict[str, float],
        max_sources: int,
    ) -> list[dict[str, Any]]:
        """
        Select which sources to crawl based on the interest graph.
        Proportionally allocates crawl budget across categories.
        """
        # Determine which categories matter
        category_scores: dict[str, float] = {}

        # From interest graph categories directly
        for cat, weight in categories.items():
            cat_key = cat.lower().replace(" ", "_")
            if cat_key in SOURCE_REGISTRY:
                category_scores[cat_key] = category_scores.get(cat_key, 0) + weight

        # From topic keywords
        for topic in topics:
            topic_name = topic.get("topic", "").lower()
            weight = topic.get("weight", 0.5)
            matched_cat = TOPIC_CATEGORY_MAP.get(topic_name)
            if matched_cat:
                category_scores[matched_cat] = category_scores.get(matched_cat, 0) + weight

        # Always include general sources
        category_scores["general"] = category_scores.get("general", 0) + 0.5

        # Sort by score, pick top categories
        sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

        # Allocate sources proportionally
        selected: list[dict[str, Any]] = []
        total_weight = sum(s for _, s in sorted_cats) or 1

        for cat, score in sorted_cats:
            if len(selected) >= max_sources:
                break
            allocation = max(1, round((score / total_weight) * max_sources))
            cat_sources = SOURCE_REGISTRY.get(cat, [])
            for source in cat_sources[:allocation]:
                if len(selected) >= max_sources:
                    break
                source_with_cat = {**source, "category": cat}
                # Avoid duplicate URLs
                if source["url"] not in [s["url"] for s in selected]:
                    selected.append(source_with_cat)

        return selected

    async def _crawl_source(
        self,
        client: httpx.AsyncClient,
        source: dict[str, Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        """
        Crawl a single source URL using Cloudflare /crawl API.

        API response shape:
        - Start: {"success": true, "result": "<crawl_id>"}
        - Poll:  {"success": true, "result": {"status": "completed", "data": [...]}}
        """
        api_url = CF_API_BASE.format(account_id=self.account_id)

        crawl_payload = {
            "url": source["url"],
            "limit": limit,
            "formats": ["markdown"],
            "render": False,  # Fast HTML fetch — free during beta, no JS needed for blogs
        }

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        # Start the crawl
        resp = await client.post(api_url, json=crawl_payload, headers=headers)
        data = resp.json()

        if not data.get("success"):
            error = data.get("errors", [{}])[0].get("message", "unknown")
            code = data.get("errors", [{}])[0].get("code", 0)
            # Rate limit — don't retry, just skip gracefully
            if code == 2001:
                print(f"[CloudflareCrawler] Rate limited — skipping {source['url']}")
            else:
                print(f"[CloudflareCrawler] Crawl start failed for {source['url']}: {error}")
            return []

        # result is the crawl_id string
        crawl_id = data.get("result")
        if not crawl_id or not isinstance(crawl_id, str):
            print(f"[CloudflareCrawler] Unexpected start response for {source['url']}: {data}")
            return []

        print(f"[CloudflareCrawler] Crawl started for {source['url']} (id: {crawl_id[:12]}...)")

        # Poll for results
        poll_url = f"{api_url}/{crawl_id}"
        elapsed = 0
        while elapsed < CRAWL_POLL_TIMEOUT:
            await asyncio.sleep(CRAWL_POLL_INTERVAL)
            elapsed += CRAWL_POLL_INTERVAL

            poll_resp = await client.get(poll_url, headers=headers)
            if poll_resp.status_code != 200:
                continue

            poll_data = poll_resp.json()
            if not poll_data.get("success"):
                continue

            result = poll_data.get("result", {})
            if not isinstance(result, dict):
                continue

            status = result.get("status", "unknown")

            if status == "completed":
                pages = result.get("data", [])
                print(f"[CloudflareCrawler] Crawl completed for {source['url']}: {len(pages)} pages")
                return self._extract_articles(pages, source)
            elif status in ("failed", "cancelled"):
                print(f"[CloudflareCrawler] Crawl {status} for {source['url']}")
                return []

        print(f"[CloudflareCrawler] Crawl timed out for {source['url']} after {CRAWL_POLL_TIMEOUT}s")
        return []

    def _extract_articles(
        self,
        pages: list[dict[str, Any]] | dict[str, Any],
        source: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract structured article data from crawl results."""
        articles: list[dict[str, Any]] = []

        if isinstance(pages, dict):
            pages = pages.get("data", [pages])

        if not isinstance(pages, list):
            return articles

        for page in pages:
            if not isinstance(page, dict):
                continue

            url = page.get("url", "")
            status = page.get("status", "")

            # Skip non-completed, disallowed, or error pages
            if status and status not in ("completed", "success", ""):
                continue

            # Skip the listing page itself (we want article pages)
            if url == source["url"]:
                continue

            # Extract content
            metadata = page.get("metadata", {})
            title = metadata.get("title", "")
            markdown = page.get("markdown", "")

            # Derive title from markdown if metadata is empty
            if not title and markdown:
                first_line = markdown.strip().split("\n")[0]
                if first_line.startswith("#"):
                    title = first_line.lstrip("#").strip()
                else:
                    title = first_line[:120]

            # Skip pages without meaningful titles
            if not title or len(title) < 10:
                continue

            # Build summary from markdown (first ~200 chars after title)
            summary = ""
            if markdown:
                lines = markdown.strip().split("\n")
                content_lines = [ln.strip() for ln in lines[1:] if ln.strip() and not ln.startswith("#")]
                summary = " ".join(content_lines)[:300]

            articles.append(
                {
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "source": source.get("label", "Web"),
                    "category": source.get("category", "general"),
                    "crawled": True,
                }
            )

        return articles


async def crawl_content_for_interests(
    topics: list[dict[str, Any]],
    categories: dict[str, float],
    max_sources: int = 5,
    items_per_source: int = 5,
) -> list[dict[str, Any]]:
    """
    Convenience function for use in the digest pipeline.
    Returns empty list if Cloudflare is not configured (graceful degradation).
    """
    crawler = CloudflareCrawler()
    if not crawler.enabled:
        return []
    return await crawler.crawl_for_interests(topics, categories, max_sources, items_per_source)
