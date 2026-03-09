"""
Content Curator - Coordinator for Daily 5 Content Generation

Thin coordinator that delegates to:
- SmartUserAnalyzer for understanding user interests
- FreshContentGenerator for fetching real content via API calls
- Anthropic Claude for expanding content ideas into full items
"""
import json
from typing import List, Dict, Any
from datetime import datetime
import anthropic
from .config import get_config
from .fresh_content_generator import FreshContentGenerator
from .smart_user_analyzer import SmartUserAnalyzer


class ContentCurator:
    def __init__(self):
        config = get_config()
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.fresh_generator = FreshContentGenerator()
        self.user_analyzer = SmartUserAnalyzer()

    async def create_valuable_daily_5(self, user_profile: dict, research_data: dict) -> List[Dict[str, Any]]:
        """
        Create Daily 5 content by analyzing user interests and delegating
        to FreshContentGenerator for real API-sourced content.
        """

        print("Creating content via user analysis + fresh content generator...")

        # Analyze user interests
        user_analysis = self.user_analyzer.analyze_user_interests(user_profile, research_data)

        print(f"  Validated interests: {list(user_analysis['validated_interests'].keys())}")
        print(f"  Primary focus: {user_analysis['current_focus']['primary_focus']}")
        print(f"  Languages: {[lang for lang, _ in user_analysis['primary_languages'][:3]]}")

        # Delegate to FreshContentGenerator which does real API calls
        fresh_daily_5 = await self.fresh_generator.generate_fresh_daily_5(user_profile)

        # Ensure all required fields exist
        for item in fresh_daily_5:
            if 'image_query' not in item:
                item['image_query'] = f"{item.get('category', 'tech')} {item.get('title', 'news')[:30]}"
            item.setdefault('relevance_score', 9)
            item.setdefault('source', 'Curated')

        print(f"Generated {len(fresh_daily_5)} pieces of curated content")
        return fresh_daily_5

    async def curate_geographically_relevant_content(
        self, user_profile: dict, research_data: dict, user_intent: dict
    ) -> List[Dict[str, Any]]:
        """
        Two-step AI generation: generate content ideas from real research data,
        then expand each idea to a full item via Claude.
        """

        print("Using two-step AI generation process...")

        # Step 1: Generate content ideas from real research data
        ideas_prompt = f"""
        Generate 5 personalized tech intelligence items for {user_profile.get('name', 'this developer')}.

        USER'S ACTIVE REPOS:
        {self._format_repos(user_intent.get('current_projects', []) if isinstance(user_intent, dict) else [])}

        USER'S LOCATION: {user_profile.get('location', '')}

        REAL DATA SOURCES (ONLY USE THESE):
        GitHub Trending: {json.dumps(list(research_data.get('trending_repos', []))[:15] if research_data.get('trending_repos') else [], indent=2)}
        HackerNews: {json.dumps(list(research_data.get('hackernews_stories', []))[:10] if research_data.get('hackernews_stories') else [], indent=2)}
        User's Starred Repos: {json.dumps(research_data.get('user_context', {}).get('interests_from_stars', [])[:5] if research_data.get('user_context', {}).get('interests_from_stars') else [], indent=2)}
        Opportunities Found: {json.dumps(list(research_data.get('opportunities', []))[:10] if research_data.get('opportunities') else [], indent=2)}

        For each item, provide:
        1. A specific, relevant title
        2. A brief description (50-100 words)
        3. Why it matters to THIS specific user
        4. A real URL
        5. A category from: "🎯 FOR YOU", "⚡ ACT NOW", "🧠 LEVEL UP", "💰 OPPORTUNITY", "🔮 NEXT WAVE"

        Requirements:
        - At least 2 items must reference specific repos from the data above
        - Be specific, not generic
        - Use real data, not placeholders

        Return as JSON array:
        [
            {{
                "title": "Specific title",
                "description": "Brief description (50-100 words)",
                "url": "real URL",
                "repo_connection": "which repo this relates to",
                "category": "one of the categories above"
            }}
        ]
        """

        ideas_response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.3,
            system="You are a tech intelligence curator. Generate specific, actionable content ideas using real data. Always return valid JSON.",
            messages=[
                {"role": "user", "content": ideas_prompt}
            ]
        )

        try:
            ideas_content = ideas_response.content[0].text.strip()

            # Extract JSON from response
            if ideas_content.startswith('```json'):
                ideas_content = ideas_content.split('```json')[1].split('```')[0].strip()
            elif ideas_content.startswith('```'):
                ideas_content = ideas_content.split('```')[1].strip()

            ideas = json.loads(ideas_content)

            if not isinstance(ideas, list) or len(ideas) < 5:
                raise ValueError("Invalid ideas format")

            print(f"Generated {len(ideas)} content ideas")

        except Exception as e:
            print(f"Ideas generation failed: {e}")
            raise Exception("Content ideas generation failed")

        # Step 2: Expand each idea to full content (100-200 words)
        expanded_items = []
        for idea in ideas[:5]:
            expansion_prompt = f"""
            Expand this content idea to exactly 150 words while maintaining specificity:

            Title: {idea.get('title', 'Tech Update')}
            Current description: {idea.get('description', '')}
            URL: {idea.get('url', 'https://github.com')}
            Repo connection: {idea.get('repo_connection', '')}

            Rules:
            - Expand to 150 words (plus or minus 10 words OK)
            - Add specific details (file names, line numbers, metrics)
            - NO generic phrases like "could be useful" or "great opportunity"
            - Include the URL: {idea.get('url', 'https://github.com')}
            - Reference the specific repo: {idea.get('repo_connection', '')}

            Expanded content (150 words):
            """

            expansion_response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                temperature=0.2,
                system="You are a content writer. Expand ideas into detailed, specific content. Always maintain the exact word count requested.",
                messages=[
                    {"role": "user", "content": expansion_prompt}
                ]
            )

            expanded_content = expansion_response.content[0].text.strip()

            expanded_items.append({
                'title': idea.get('title', 'Tech Update'),
                'content': expanded_content,
                'category': idea.get('category', '🎯 FOR YOU'),
                'url': idea.get('url', 'https://github.com'),
                'repo_connection': idea.get('repo_connection', '')
            })

        print(f"Expanded {len(expanded_items)} items")
        return expanded_items

    def _format_repos(self, repos: list) -> str:
        """Format repo list for prompts"""
        if not repos:
            return "No active repositories found"

        formatted = []
        for i, repo in enumerate(repos[:5], 1):
            formatted.append(f"{i}. {repo}")

        return "\n".join(formatted)

    def _validate_content_freshness(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate content freshness - reject items older than 7 days"""
        from datetime import timedelta

        fresh_items = []
        cutoff_date = datetime.now() - timedelta(days=7)

        for item in items:
            published_at = item.get('published_at', '')
            if published_at:
                try:
                    if 'T' in published_at:
                        item_date = datetime.fromisoformat(
                            published_at.replace('Z', '+00:00')
                        ).replace(tzinfo=None)
                    else:
                        item_date = datetime.fromisoformat(published_at)

                    if item_date >= cutoff_date:
                        fresh_items.append(item)
                    else:
                        print(f"Rejected stale content: {item.get('title', 'Unknown')} (from {item_date.strftime('%Y-%m-%d')})")
                except Exception as e:
                    print(f"Could not parse date for {item.get('title', 'Unknown')}: {e}")
                    fresh_items.append(item)
            else:
                # No date means assume fresh
                fresh_items.append(item)

        print(f"Freshness validation: {len(fresh_items)}/{len(items)} items passed")
        return fresh_items
