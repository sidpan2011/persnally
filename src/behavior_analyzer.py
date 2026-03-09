"""
Behavioral Intelligence Engine
Analyzes user behavior patterns to predict intent and needs
"""

import json
from datetime import UTC
from typing import Any

import anthropic


class BehaviorAnalyzer:
    def __init__(self, config):
        # Use Claude instead of OpenAI to avoid quota issues
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    async def analyze_user_intent(self, github_data: dict, user_profile: dict) -> dict[str, Any]:
        """Deep behavioral analysis with confidence scores and variety"""

        prompt = f"""
        Analyze this developer's ACTUAL behavior patterns and interests.

        GITHUB ACTIVITY (REAL DATA):
        Recent Repos: {github_data.get("recent_repos", [])}
        Recent Stars: {github_data.get("starred_repos", [])}
        Languages Used: {github_data.get("languages", [])}
        Recent Commits: {github_data.get("recent_activity", [])}
        Contribution Pattern: {github_data.get("contribution_pattern", {})}

        USER STATED INTERESTS: {user_profile["interests"]}
        USER LOCATION: {user_profile.get("location", "Unknown")}
        SKILL LEVEL: {user_profile.get("experience_level", "intermediate")}

        DEEP ANALYSIS REQUIRED:

        1. CURRENT FOCUS (with evidence):
           - What are they ACTUALLY building right now? (look at recent commits/repos)
           - What technologies are they actively using? (not just interested in)
           - What problems are they trying to solve? (infer from repo names/descriptions)

        2. EXPLORATION PATTERNS:
           - What new areas are they researching? (stars outside their main stack)
           - What technologies are they considering adopting? (tutorial repos starred)
           - What companies/projects are they following? (who they star)

        3. SKILL GAPS & LEARNING:
           - Where are they struggling? (incomplete projects, forked tutorials)
           - What are they trying to learn? (educational repos, courses starred)
           - What's their next skill progression? (based on current → starred gap)

        4. CAREER SIGNALS:
           - Are they job hunting? (portfolio updates, resume repos)
           - Building side projects? (new personal projects)
           - Preparing for launch? (marketing, docs, deployment activity)

        5. GEOGRAPHIC CONTEXT:
           - Location: {user_profile.get("location", "Unknown")}
           - Prioritize local opportunities, events, communities
           - Local tech ecosystem, startups, job markets

        Return detailed JSON with:
        - primary_intent: most likely current focus
        - confidence_score: 0-1 based on evidence strength
        - specific_evidence: actual repos/activity supporting this
        - skill_level_assessment: based on code complexity
        - immediate_needs: what they need RIGHT NOW
        - geographic_priorities: local vs global relevance
        - learning_gaps: specific skills to develop next
        - project_stage: idea/building/launching/maintaining
        """

        # Use Claude API format instead of OpenAI
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            temperature=0.3,
            system="You are a developer behavior analyst. Always return valid JSON. Be precise and evidence-based in your analysis.",
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            # Claude response format is different from OpenAI
            content = response.content[0].text.strip()

            # Try to extract JSON from response if it's wrapped in markdown
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].strip()

            intent_data = json.loads(content)

            # Validate that we have the required fields
            if "primary_intent" in intent_data and "confidence_score" in intent_data:
                return intent_data
            else:
                print("⚠️ Intent analysis missing required fields, using fallback")
                return self._fallback_intent_analysis(github_data, user_profile)

        except Exception as e:
            print(f"⚠️ Intent analysis failed: {e}")
            # Fallback analysis based on GitHub data
            return self._fallback_intent_analysis(github_data, user_profile)

    def _fallback_intent_analysis(self, github_data: dict, user_profile: dict) -> dict[str, Any]:
        """Enhanced fallback intent analysis with better confidence calculation"""

        # Analyze recent activity patterns
        recent_repos = github_data.get("recent_repos", [])
        starred_repos = github_data.get("interests_from_stars", [])
        repo_analysis = github_data.get("repo_analysis", {})
        user_interests = user_profile.get("interests", [])

        # Calculate confidence based on data availability
        confidence_factors = []
        base_confidence = 0.5

        # Recent activity boosts confidence
        if len(recent_repos) > 0:
            base_confidence += 0.1
            confidence_factors.append("Has recent repository activity")

        # Starred repos show interests
        if len(starred_repos) > 5:
            base_confidence += 0.1
            confidence_factors.append("Active in exploring new repositories")

        # User provided interests
        if len(user_interests) > 0:
            base_confidence += 0.2
            confidence_factors.append("User provided specific interests")

        # Language diversity indicates expertise
        top_languages = repo_analysis.get("top_languages", [])
        if isinstance(top_languages, list) and len(top_languages) > 2:
            base_confidence += 0.1
            confidence_factors.append("Multi-language developer")
        elif isinstance(top_languages, dict) and len(top_languages) > 2:
            base_confidence += 0.1
            confidence_factors.append("Multi-language developer")

        # Cap confidence at reasonable level
        final_confidence = min(base_confidence, 0.85)

        # Determine primary intent with better logic
        intent_score = {"building": 0, "exploring": 0, "learning": 0, "launching": 0}

        # Recent repos indicate building
        if len(recent_repos) > 3:
            intent_score["building"] += 3

        # Starred repos indicate exploring
        if len(starred_repos) > 8:
            intent_score["exploring"] += 2

        # Mixed activity indicates learning
        if len(recent_repos) > 0 and len(starred_repos) > 5:
            intent_score["learning"] += 2

        # Check for launch indicators (docs, websites, marketing repos)
        launch_keywords = ["docs", "website", "landing", "marketing", "demo"]
        for repo in recent_repos[:5]:
            repo_name = repo.get("name", "").lower()
            repo_desc = repo.get("description", "").lower()
            if any(keyword in repo_name or keyword in repo_desc for keyword in launch_keywords):
                intent_score["launching"] += 2

        # Default to exploring if no clear pattern
        if all(score == 0 for score in intent_score.values()):
            intent_score["exploring"] = 1

        primary_intent = max(intent_score, key=intent_score.get)

        # Extract tech interests more robustly
        tech_interests = []

        # From languages
        if isinstance(top_languages, list):
            tech_interests.extend([lang[0] if isinstance(lang, tuple) else lang for lang in top_languages[:5]])
        elif isinstance(top_languages, dict):
            tech_interests.extend(list(top_languages.keys())[:5])

        # From user interests
        tech_interests.extend(user_interests)

        # Remove duplicates
        tech_interests = list(set(tech_interests))

        return {
            "primary_intent": primary_intent,
            "confidence_score": round(final_confidence, 2),
            "specific_evidence": confidence_factors
            + [
                f"Recent activity: {len(recent_repos)} repositories",
                f"Starred repos: {len(starred_repos)} items",
                f"Intent indicators: {primary_intent} scored highest",
            ],
            "skill_level_assessment": self._assess_skill_level(recent_repos, starred_repos, top_languages),
            "immediate_needs": self._identify_immediate_needs(primary_intent, user_interests),
            "geographic_priorities": self._assess_geographic_priorities(user_profile),
            "learning_gaps": self._identify_learning_gaps(user_interests, recent_repos, starred_repos),
            "project_stage": self._assess_project_stage(recent_repos, repo_analysis),
            "tech_interests": tech_interests,
            "current_projects": self._get_active_project_names(github_data, recent_repos),
            "growth_areas": tech_interests[:3],
            "career_stage": self._assess_career_stage(recent_repos, repo_analysis),
            "opportunity_preferences": self._suggest_opportunity_types(user_interests, primary_intent),
            "specific_interests": self._analyze_specific_interests(user_interests, recent_repos, starred_repos),
        }

    def _assess_skill_level(self, recent_repos: list, starred_repos: list, top_languages) -> str:
        """Assess developer skill level based on activity"""

        repo_count = len(recent_repos)
        star_count = len(starred_repos)

        if isinstance(top_languages, (list, dict)):
            lang_count = len(top_languages)
        else:
            lang_count = 0

        # Simple heuristic
        if repo_count > 10 and star_count > 20 and lang_count > 3:
            return "advanced developer"
        elif repo_count > 3 and star_count > 8:
            return "intermediate developer"
        else:
            return "developing skills"

    def _assess_career_stage(self, recent_repos: list, repo_analysis: dict) -> str:
        """Assess career stage based on repository patterns"""

        # Look for indicators in repo names/descriptions
        business_keywords = ["startup", "company", "business", "saas", "product"]
        learning_keywords = ["tutorial", "learning", "course", "practice", "exercise"]

        business_count = 0
        learning_count = 0

        for repo in recent_repos[:10]:
            repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()

            if any(keyword in repo_text for keyword in business_keywords):
                business_count += 1

            if any(keyword in repo_text for keyword in learning_keywords):
                learning_count += 1

        if business_count > learning_count:
            return "entrepreneur/founder"
        elif learning_count > business_count:
            return "learning/growing"
        else:
            return "professional developer"

    def _suggest_opportunity_types(self, user_interests: list, primary_intent: str) -> list:
        """Suggest opportunity types based on interests and intent"""

        opportunities = []

        # Based on interests
        for interest in user_interests:
            if "hackathon" in interest.lower():
                opportunities.append("hackathons")
            if "startup" in interest.lower():
                opportunities.extend(["funding", "accelerators"])
            if "ai" in interest.lower() or "ml" in interest.lower():
                opportunities.extend(["ai_tools", "research_opportunities"])
            if "web3" in interest.lower() or "blockchain" in interest.lower():
                opportunities.extend(["web3_opportunities", "crypto_projects"])

        # Based on intent
        if primary_intent == "building":
            opportunities.extend(["hackathons", "open_source"])
        elif primary_intent == "exploring":
            opportunities.extend(["learning_resources", "communities"])
        elif primary_intent == "launching":
            opportunities.extend(["funding", "marketing_tools"])

        return list(set(opportunities))

    def _analyze_specific_interests(self, user_interests: list, recent_repos: list, starred_repos: list) -> dict:
        """Analyze specific interest areas with evidence"""

        interests = {}

        for interest in user_interests:
            interest_lower = interest.lower()
            evidence_count = 0

            # Check recent repos
            for repo in recent_repos[:10]:
                repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
                if any(word in repo_text for word in interest_lower.split()):
                    evidence_count += 2

            # Check starred repos
            for repo in starred_repos[:20]:
                repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
                if any(word in repo_text for word in interest_lower.split()):
                    evidence_count += 1

            # Determine involvement level
            if evidence_count >= 5:
                level = "highly involved"
            elif evidence_count >= 2:
                level = "moderately involved"
            elif evidence_count >= 1:
                level = "exploring"
            else:
                level = "interested"

            interests[interest] = level

        return interests

    def _identify_immediate_needs(self, primary_intent: str, user_interests: list) -> list:
        """Identify what the user needs RIGHT NOW based on intent"""

        needs = []

        if primary_intent == "building":
            needs.extend(["development tools", "documentation", "testing frameworks"])
        elif primary_intent == "exploring":
            needs.extend(["learning resources", "community access", "mentorship"])
        elif primary_intent == "learning":
            needs.extend(["structured courses", "hands-on projects", "peer learning"])
        elif primary_intent == "launching":
            needs.extend(["marketing tools", "funding opportunities", "user feedback"])

        # Add interest-specific needs
        for interest in user_interests:
            if "ai" in interest.lower() or "ml" in interest.lower():
                needs.extend(["GPU access", "datasets", "model APIs"])
            elif "web3" in interest.lower() or "blockchain" in interest.lower():
                needs.extend(["testnet access", "development tools", "community"])
            elif "startup" in interest.lower():
                needs.extend(["market research", "funding", "mentorship"])

        return list(set(needs))

    def _assess_geographic_priorities(self, user_profile: dict) -> dict:
        """Assess geographic priorities based on user location"""

        location = user_profile.get("location", "").lower()

        priorities = {"local_focus": False, "region": "global", "local_opportunities": [], "timezone_preference": "UTC"}

        # Check for India
        if any(loc in location for loc in ["india", "bangalore", "delhi", "mumbai", "hyderabad", "pune"]):
            priorities.update(
                {
                    "local_focus": True,
                    "region": "india",
                    "local_opportunities": ["hackathons", "startups", "tech_events", "job_market"],
                    "timezone_preference": "Asia/Kolkata",
                }
            )
        # Check for US
        elif any(loc in location for loc in ["usa", "us", "america", "california", "new york", "texas"]):
            priorities.update(
                {
                    "local_focus": True,
                    "region": "usa",
                    "local_opportunities": ["funding", "accelerators", "tech_events", "job_market"],
                    "timezone_preference": "America/New_York",
                }
            )

        return priorities

    def _identify_learning_gaps(self, user_interests: list, recent_repos: list, starred_repos: list) -> list:
        """Identify specific skills the user needs to develop next"""

        gaps = []

        # Analyze starred repos for learning patterns
        tutorial_keywords = ["tutorial", "learn", "course", "guide", "example"]
        for repo in starred_repos[:10]:
            repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
            if any(keyword in repo_text for keyword in tutorial_keywords):
                # Extract technology from repo name/description
                tech_keywords = ["react", "python", "javascript", "ai", "ml", "blockchain", "web3"]
                for tech in tech_keywords:
                    if tech in repo_text and tech not in gaps:
                        gaps.append(tech)

        # Add interest-based gaps
        for interest in user_interests:
            if "ai" in interest.lower() and "python" not in gaps:
                gaps.append("python")
            if "web3" in interest.lower() and "solidity" not in gaps:
                gaps.append("solidity")
            if "startup" in interest.lower() and "business" not in gaps:
                gaps.append("business")

        return gaps[:5]  # Limit to top 5 gaps

    def _assess_project_stage(self, recent_repos: list, repo_analysis: dict) -> str:
        """Assess what stage the user's projects are in"""

        # Look for indicators in repo names and descriptions
        idea_keywords = ["idea", "concept", "planning", "research"]
        building_keywords = ["development", "building", "progress", "wip"]
        launching_keywords = ["launch", "release", "production", "deploy"]
        maintaining_keywords = ["maintenance", "update", "fix", "improve"]

        stage_scores = {"idea": 0, "building": 0, "launching": 0, "maintaining": 0}

        for repo in recent_repos[:10]:
            repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()

            if any(keyword in repo_text for keyword in idea_keywords):
                stage_scores["idea"] += 1
            if any(keyword in repo_text for keyword in building_keywords):
                stage_scores["building"] += 1
            if any(keyword in repo_text for keyword in launching_keywords):
                stage_scores["launching"] += 1
            if any(keyword in repo_text for keyword in maintaining_keywords):
                stage_scores["maintaining"] += 1

        # Return the stage with highest score, default to building
        if all(score == 0 for score in stage_scores.values()):
            return "building"

        return max(stage_scores, key=stage_scores.get)

    async def analyze_engagement_patterns(self, github_data: dict) -> dict[str, Any]:
        """Analyze engagement patterns for optimal content timing"""

        prompt = f"""
        Analyze GitHub engagement patterns to optimize content delivery:

        GITHUB DATA: {json.dumps(github_data, indent=2)}

        Determine:
        1. Optimal content timing (when they're most active)
        2. Preferred content depth (quick reads vs deep dives)
        3. Engagement style (hands-on vs theoretical)
        4. Learning preferences (tutorials vs examples vs documentation)
        5. Communication style (technical vs business-focused)

        Return JSON:
        {{
            "optimal_timing": "morning/afternoon/evening",
            "content_depth": "quick/medium/deep",
            "engagement_style": "hands-on/theoretical/mixed",
            "learning_preference": "tutorials/examples/docs",
            "communication_style": "technical/business/mixed",
            "attention_span": "short/medium/long",
            "interaction_preference": "read-only/hands-on/collaborative"
        }}
        """

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            temperature=0.3,
            system="You are a developer behavior analyst. Return valid JSON.",
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            content = response.content[0].text.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].strip()
            engagement_data = json.loads(content)
            return engagement_data
        except:
            return {
                "optimal_timing": "evening",
                "content_depth": "medium",
                "engagement_style": "hands-on",
                "learning_preference": "examples",
                "communication_style": "technical",
                "attention_span": "medium",
                "interaction_preference": "hands-on",
            }

    def get_intent_based_subject_line(self, user_intent: dict, date: str) -> str:
        """Generate simple subject line - no personalization"""

        # Simple, consistent subject line
        subject = f"Daily update by persnally: {date}"

        return subject

    def get_personalization_note(self, user_intent: dict) -> str:
        """Generate personalization note for email"""

        intent_notes = {
            "exploring": "Based on your exploration focus",
            "building": "Based on your active development phase",
            "learning": "Based on your skill development journey",
            "launching": "Based on your launch preparation",
            "pivoting": "Based on your tech stack evolution",
            "scaling": "Based on your growth phase",
        }

        primary_intent = user_intent.get("primary_intent", "exploring")
        return intent_notes.get(primary_intent, "Based on your current focus")

    def _get_active_project_names(self, github_data: dict, recent_repos: list) -> list:
        """Get active project names prioritizing active repos over recent repos"""
        # Try to get active repos first
        active_repos = github_data.get("active_repos", [])
        if active_repos:
            project_names = [repo.get("name", "Unknown") for repo in active_repos[:5]]
            print(f"📊 Using {len(project_names)} active repos for current projects")
            return project_names

        # Fallback to recent repos
        project_names = [repo.get("name", "Unknown") for repo in recent_repos[:3]]
        print(f"📊 Using {len(project_names)} recent repos for current projects (fallback)")
        return project_names

    async def analyze_user_behavior(self, research_data: dict, user_profile: dict) -> dict:
        """Enhanced behavior analysis that properly extracts active repos"""

        github_data = research_data.get("user_context", {})

        # Extract active repos with proper structure
        active_repos = []

        # Try different possible data structures
        repos_data = github_data.get("user_repos") or github_data.get("recent_repos") or []

        if repos_data:
            for repo in repos_data:
                # Handle both dict and string formats
                if isinstance(repo, dict):
                    pushed_at = repo.get("pushed_at") or repo.get("updated_at")
                    repo_name = repo.get("name", "Unknown")
                    repo_language = repo.get("language")
                    repo_description = repo.get("description")
                    repo_url = repo.get("html_url") or repo.get("url")
                else:
                    # If repo is just a string/name
                    pushed_at = None
                    repo_name = str(repo)
                    repo_language = None
                    repo_description = None
                    repo_url = None

                if pushed_at:
                    try:
                        from datetime import datetime

                        pushed_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                        days_ago = (datetime.now(UTC) - pushed_date).days

                        if days_ago <= 30:  # Active in last 30 days
                            active_repos.append(
                                {
                                    "name": repo_name,
                                    "language": repo_language,
                                    "description": repo_description,
                                    "pushed_at": pushed_at,
                                    "days_ago": days_ago,
                                    "url": repo_url,
                                }
                            )
                    except Exception as e:
                        print(f"⚠️ Error parsing repo date: {e}")
                        continue
                else:
                    # If no date info, assume it's recent if it's in recent_repos
                    if "recent_repos" in github_data:
                        active_repos.append(
                            {
                                "name": repo_name,
                                "language": repo_language,
                                "description": repo_description,
                                "pushed_at": "recent",
                                "days_ago": 7,  # Assume recent
                                "url": repo_url,
                            }
                        )

        print(f"🔍 Active repos extracted: {len(active_repos)}")
        for repo in active_repos[:3]:
            print(f"   - {repo['name']} ({repo['days_ago']} days ago)")

        # Get the existing intent analysis
        intent_data = await self.analyze_user_intent(github_data, user_profile)

        # Defensive: Ensure intent_data is a dict
        if not isinstance(intent_data, dict):
            print(f"⚠️ WARNING: intent_data is {type(intent_data)}, expected dict. Using defaults.")
            intent_data = {}

        # Defensive: Get values and ensure they're lists before slicing
        tech_interests = intent_data.get("tech_interests", [])
        if not isinstance(tech_interests, list):
            tech_interests = []

        learning_gaps = intent_data.get("learning_gaps", [])
        if not isinstance(learning_gaps, list):
            learning_gaps = []

        interests_from_stars = github_data.get("interests_from_stars", [])
        if not isinstance(interests_from_stars, list):
            interests_from_stars = []

        # Add structured behavior data
        behavior_data = {
            "primary_intent": intent_data.get("primary_intent", "exploring"),
            "evidence": {
                "active_repos": [repo["name"] for repo in active_repos],
                "recent_stars": interests_from_stars[:10],
                "technologies_using": tech_interests[:5],
                "technologies_exploring": learning_gaps[:5],
            },
            "current_projects": [repo["name"] for repo in active_repos],
            "recent_interests": interests_from_stars[:5],
            "primary_technologies": tech_interests[:5],
            "emerging_interests": learning_gaps[:5],
            "confidence_score": intent_data.get("confidence_score", 0.7),
            "geographic_priorities": intent_data.get("geographic_priorities", {}),
            "immediate_needs": intent_data.get("immediate_needs", []),
            "project_stage": intent_data.get("project_stage", "building"),
        }

        return behavior_data
