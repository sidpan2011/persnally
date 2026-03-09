"""
Smart Opportunity Matcher
Matches user intent with 5 most relevant opportunities from research data
"""

import json
from typing import Any

import anthropic


class OpportunityMatcher:
    def __init__(self, config):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    async def find_daily_5(self, user_intent: dict, research_data: dict) -> list[dict[str, Any]]:
        """Match user intent with 5 most relevant opportunities"""

        # Extract user profile data - THIS IS PRIMARY
        user_interests = user_intent.get("interests", [])
        user_experience = user_intent.get("experience_level", "intermediate")
        user_preferences = user_intent.get("preferences", {})
        opportunity_types = user_preferences.get("opportunity_types", [])

        # Extract GitHub context - THIS IS SECONDARY (for technical understanding)
        github_context = research_data.get("user_context", {})

        prompt = f"""
        You are creating a personalized Daily 5 for a developer. PRIORITIZE THEIR STATED INTERESTS ABOVE ALL.

        ═══════════════════════════════════════════════════════════════════
        PRIMARY FACTORS (Weight: 70%) - USER PROFILE:
        ═══════════════════════════════════════════════════════════════════

        USER INTERESTS (MOST IMPORTANT): {json.dumps(user_interests, indent=2)}
        EXPERIENCE LEVEL: {user_experience}
        PREFERRED OPPORTUNITY TYPES: {json.dumps(opportunity_types, indent=2)}
        CONTENT STYLE: {user_preferences.get("content_style", "technical_with_business_context")}
        LOCATION: {user_intent.get("location", "Global")}

        ⚠️ CRITICAL: Match recommendations to user_interests FIRST.
        Every recommendation MUST relate to at least one interest.

        ═══════════════════════════════════════════════════════════════════
        SECONDARY FACTORS (Weight: 30%) - GITHUB CONTEXT (for technical depth):
        ═══════════════════════════════════════════════════════════════════

        Recent Activity: {json.dumps(github_context.get("recent_repos", [])[:5], indent=2)}
        Tech Stack: {json.dumps(github_context.get("repo_analysis", {}).get("top_languages", [])[:3], indent=2)}

        Note: GitHub is CONTEXT ONLY - to understand their technical level and current work.
        DO NOT prioritize GitHub repos over user's stated interests.

        ═══════════════════════════════════════════════════════════════════
        DATA SOURCES:
        ═══════════════════════════════════════════════════════════════════

        REAL GITHUB TRENDING: {json.dumps(research_data.get("trending_repos", [])[:15], indent=2)}
        REAL HACKERNEWS: {json.dumps(research_data.get("hackernews_stories", [])[:15], indent=2)}

        ═══════════════════════════════════════════════════════════════════
        MATCHING RULES (In Priority Order):
        ═══════════════════════════════════════════════════════════════════

        1. MATCH USER INTERESTS FIRST:
           - If user lists "ai/ml research" → prioritize ML research papers, AI tools, research opportunities
           - If user lists "hackathon" → prioritize ACTUAL hackathons with dates/prizes
           - If user lists "robotics" → prioritize robotics projects, competitions, hardware
           - If user lists "web3/blockchain" → blockchain repos, DeFi, crypto opportunities
           - If user lists "startup" → funding news, YC companies, startup tools

        2. MATCH OPPORTUNITY TYPES:
           - If preferences include "hackathons" → look for competitions
           - If preferences include "jobs" → look for job postings
           - If preferences include "funding" → look for grants, accelerators

        3. CONSIDER GITHUB (Secondary):
           - Use GitHub to gauge technical depth and current context
           - NOT as primary matching factor

        4. EXPERIENCE LEVEL:
           - Match complexity to their experience level
           - {user_experience} → adjust technical depth accordingly

        Categories:
        🎯 FOR YOU - Perfect match to their stated interests
        ⚡ ACT NOW - Real deadlines, time-sensitive opportunities
        🧠 LEVEL UP - Learning resources in their interest areas
        💰 OPPORTUNITY - Jobs, grants, accelerators matching preferences
        🔮 WHAT'S NEXT - Emerging trends in their interest areas

        For each item:
        1. Use REAL data from above sources
        2. Explain SPECIFIC relevance to their STATED interests (not just GitHub)
        3. Include actionable next steps with real URLs
        4. Add relevant metrics (stars, funding amounts, dates)
        5. Make it feel personally curated for THEIR interests

        Example for "ai/ml research" + "robotics" interests:
        "DeepMind released new robotics simulation framework (12K GitHub stars). Given your interests in AI/ML research AND robotics, this is highly relevant. The framework supports reinforcement learning for robot manipulation. Check out the examples at github.com/deepmind/robotics-sim"

        Return JSON array:
        [
            {{
                "category": "🎯 FOR YOU",
                "title": "Specific title from real data",
                "description": "Why this specifically matters to their STATED interests",
                "action": "Exact next step with URL",
                "relevance_score": 9,
                "source": "GitHub/HackerNews",
                "meta_info": "Real metrics/dates",
                "image_query": "search term for relevant image",
                "interest_match": "ai/ml research, robotics"
            }}
        ]

        ⚠️ REMINDER: Every item must clearly connect to at least ONE of the user's stated interests: {user_interests}
        """

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2500,
            temperature=0.3,
            system="You are a personalized opportunity curator. Always return valid JSON array with exactly 5 items.",
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            daily_5_data = json.loads(response.content[0].text)
            return daily_5_data
        except Exception as e:
            print(f"⚠️ Daily 5 matching failed: {e}")
            return self._fallback_daily_5(user_intent, research_data)

    def _fallback_daily_5(self, user_intent: dict, research_data: dict) -> list[dict[str, Any]]:
        """Fallback Daily 5 with smart matching when AI parsing fails"""

        trending_repos = research_data.get("trending_repos", [])[:10]
        hackernews_stories = research_data.get("hackernews_stories", [])[:10]
        user_interests = user_intent.get("tech_interests", ["technology"])
        github_context = research_data.get("user_context", {})

        # Smart matching based on user interests
        def matches_interests(text):
            if not text:
                return False
            text_lower = text.lower()
            interest_keywords = {
                "web3": ["blockchain", "crypto", "defi", "solana", "ethereum", "web3"],
                "ai": ["ai", "ml", "machine learning", "neural", "gpt", "llm", "pytorch"],
                "startup": ["startup", "funding", "vc", "accelerator", "yc"],
                "hackathon": ["hackathon", "competition", "contest", "prize"],
            }

            for interest in user_interests:
                if any(
                    keyword in text_lower
                    for keyword in interest_keywords.get(interest.split("/")[0], [interest.lower()])
                ):
                    return True
            return False

        daily_5 = []

        # Find most relevant repos
        relevant_repos = [
            repo
            for repo in trending_repos
            if matches_interests(repo.get("description", "") + " " + repo.get("name", ""))
        ]
        if not relevant_repos:
            relevant_repos = trending_repos[:3]

        # Find most relevant HN stories
        relevant_stories = [story for story in hackernews_stories if matches_interests(story.get("title", ""))]
        if not relevant_stories:
            relevant_stories = hackernews_stories[:2]

        # FOR YOU - Best matching repo
        if relevant_repos:
            best_repo = relevant_repos[0]
            daily_5.append(
                {
                    "category": "🎯 FOR YOU",
                    "title": best_repo.get("name", "Trending Project"),
                    "description": f"{best_repo.get('description', 'Trending repository')}. This matches your interests in {', '.join(user_interests[:2])} and could be valuable for your current projects.",
                    "action": f"Explore the repository and consider contributing: {best_repo.get('html_url', 'GitHub')}",
                    "relevance_score": 9,
                    "source": "GitHub Trending",
                    "meta_info": f"⭐ {best_repo.get('stargazers_count', 0)} stars • Language: {best_repo.get('language', 'N/A')}",
                    "image_query": f"{best_repo.get('name', 'repository')} {best_repo.get('language', 'code')}",
                }
            )

        # ACT NOW - Most relevant HN story
        if relevant_stories:
            urgent_story = relevant_stories[0]
            daily_5.append(
                {
                    "category": "⚡ ACT NOW",
                    "title": urgent_story.get("title", "Trending Discussion"),
                    "description": f"Active discussion on HackerNews about {urgent_story.get('title', 'this topic')}. This is directly relevant to your interests and the community is actively engaging with it.",
                    "action": f"Join the discussion and share your perspective: {urgent_story.get('url', 'HackerNews')}",
                    "relevance_score": 8,
                    "source": "HackerNews",
                    "meta_info": f"💬 {urgent_story.get('descendants', 0)} comments • 📈 {urgent_story.get('score', 0)} points",
                    "image_query": f"hackernews discussion {urgent_story.get('title', 'technology')[:30]}",
                }
            )

        # LEVEL UP - Learning opportunity
        if len(relevant_repos) > 1:
            learning_repo = relevant_repos[1]
            daily_5.append(
                {
                    "category": "🧠 LEVEL UP",
                    "title": learning_repo.get("name", "Learning Resource"),
                    "description": f"Advanced project: {learning_repo.get('description', 'Repository')}. Perfect for deepening your expertise in areas you're already exploring based on your GitHub activity.",
                    "action": f"Study the implementation and architecture: {learning_repo.get('html_url', 'GitHub')}",
                    "relevance_score": 7,
                    "source": "GitHub",
                    "meta_info": f"⭐ {learning_repo.get('stargazers_count', 0)} stars • Forks: {learning_repo.get('forks_count', 0)}",
                    "image_query": f"{learning_repo.get('language', 'programming')} tutorial code",
                }
            )

        # OPPORTUNITY - Career/business
        if len(relevant_stories) > 1:
            opp_story = relevant_stories[1]
            daily_5.append(
                {
                    "category": "💰 OPPORTUNITY",
                    "title": opp_story.get("title", "Industry Opportunity"),
                    "description": f"Industry insight: {opp_story.get('title', 'Opportunity')}. This could reveal new opportunities in your field of interest or provide valuable market intelligence.",
                    "action": f"Read and analyze for potential opportunities: {opp_story.get('url', 'HackerNews')}",
                    "relevance_score": 8,
                    "source": "HackerNews",
                    "meta_info": f"💬 {opp_story.get('descendants', 0)} comments • Active discussion",
                    "image_query": f"business opportunity {opp_story.get('title', 'startup')[:30]}",
                }
            )

        # WHAT'S NEXT - Future trends
        if len(relevant_repos) > 2:
            future_repo = relevant_repos[2]
            daily_5.append(
                {
                    "category": "🔮 WHAT'S NEXT",
                    "title": future_repo.get("name", "Emerging Technology"),
                    "description": f"Emerging trend: {future_repo.get('description', 'New technology')}. This represents the cutting edge of your field and could be important to track for future opportunities.",
                    "action": f"Star and follow development: {future_repo.get('html_url', 'GitHub')}",
                    "relevance_score": 7,
                    "source": "GitHub",
                    "meta_info": f"⭐ {future_repo.get('stargazers_count', 0)} stars • Recent activity",
                    "image_query": f"future technology {future_repo.get('language', 'innovation')}",
                }
            )

        return daily_5

    async def rank_opportunities(self, opportunities: list[dict], user_intent: dict) -> list[dict]:
        """Rank opportunities by relevance to user intent"""

        prompt = f"""
        Rank these opportunities by relevance to user intent:

        USER INTENT: {json.dumps(user_intent, indent=2)}
        OPPORTUNITIES: {json.dumps(opportunities, indent=2)}

        Rank each opportunity 1-10 based on:
        1. Perfect match to current intent
        2. Skill level appropriateness
        3. Time sensitivity
        4. Career/growth impact
        5. Learning value

        Return JSON with updated relevance scores and ranking.
        """

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            ranked_data = json.loads(response.content[0].text)
            return ranked_data
        except:
            # Simple fallback ranking
            return sorted(opportunities, key=lambda x: x.get("relevance_score", 5), reverse=True)

    def format_opportunity_for_email(self, opportunity: dict[str, Any]) -> dict[str, str]:
        """Format opportunity for email display"""

        return {
            "category": opportunity.get("category", "📌 OPPORTUNITY"),
            "title": opportunity.get("title", "Untitled Opportunity"),
            "description": opportunity.get("description", "No description available"),
            "action": opportunity.get("action", "Take action"),
            "timing": opportunity.get("timing", "Time-sensitive"),
            "meta_info": opportunity.get("meta_info", ""),
            "source": opportunity.get("source", "Unknown"),
        }

    async def generate_opportunity_summary(self, daily_5: list[dict], user_intent: dict) -> str:
        """Generate summary of why these 5 opportunities were selected"""

        prompt = f"""
        Generate a brief summary explaining why these 5 opportunities were selected:

        USER INTENT: {json.dumps(user_intent, indent=2)}
        SELECTED OPPORTUNITIES: {json.dumps(daily_5, indent=2)}

        Explain in 2-3 sentences why these specific opportunities match their current focus and goals.
        """

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text.strip()
