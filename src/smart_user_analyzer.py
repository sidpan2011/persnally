"""
Smart User Analyzer - Deep Interest Matching
Analyzes user profile + GitHub activity to create precise interest matching
"""

from typing import Any


class SmartUserAnalyzer:
    def __init__(self):
        pass

    def analyze_user_interests(self, user_profile: dict, github_data: dict) -> dict[str, Any]:
        """Deep analysis combining profile interests with GitHub activity"""

        profile_interests = user_profile.get("interests", [])
        github_context = github_data.get("user_context", {})

        # Extract data from GitHub
        recent_repos = github_context.get("recent_repos", [])
        starred_repos = github_context.get("interests_from_stars", [])
        repo_analysis = github_context.get("repo_analysis", {})

        # Analyze programming languages
        languages = self._extract_languages(recent_repos, starred_repos, repo_analysis)

        # Analyze project types and domains
        project_domains = self._analyze_project_domains(recent_repos, starred_repos)

        # Match profile interests with GitHub evidence
        interest_evidence = self._match_interests_with_evidence(
            profile_interests, recent_repos, starred_repos, languages, project_domains
        )

        # Determine current focus and activity level
        current_focus = self._determine_current_focus(recent_repos, interest_evidence)

        # Generate content preferences
        content_preferences = self._generate_content_preferences(interest_evidence, current_focus)

        return {
            "validated_interests": interest_evidence,
            "primary_languages": languages[:5],
            "project_domains": project_domains,
            "current_focus": current_focus,
            "content_preferences": content_preferences,
            "experience_indicators": self._assess_experience_level(recent_repos, repo_analysis),
            "opportunity_types": self._suggest_opportunity_types(interest_evidence, current_focus),
        }

    def _extract_languages(self, recent_repos: list[dict], starred_repos: list[dict], repo_analysis: dict) -> list[str]:
        """Extract and rank programming languages by usage and interest"""

        language_scores = {}

        # Score from recent repos (higher weight - what they actually code in)
        for repo in recent_repos:
            lang = repo.get("language")
            if lang:
                language_scores[lang] = language_scores.get(lang, 0) + 3

        # Score from starred repos (interest indicator)
        for repo in starred_repos:
            lang = repo.get("language")
            if lang:
                language_scores[lang] = language_scores.get(lang, 0) + 1

        # Score from repo analysis if available
        if isinstance(repo_analysis, dict) and "top_languages" in repo_analysis:
            top_langs = repo_analysis["top_languages"]
            if isinstance(top_langs, dict):
                for lang, count in top_langs.items():
                    language_scores[lang] = language_scores.get(lang, 0) + count

        # Return sorted by score
        return sorted(language_scores.items(), key=lambda x: x[1], reverse=True)

    def _analyze_project_domains(self, recent_repos: list[dict], starred_repos: list[dict]) -> list[str]:
        """Analyze what domains/areas the user is working in"""

        domain_keywords = {
            "web3": ["blockchain", "crypto", "defi", "ethereum", "solana", "web3", "smart contract"],
            "ai_ml": ["ai", "ml", "machine learning", "neural", "deep learning", "pytorch", "tensorflow", "llm"],
            "web_dev": ["react", "next", "vue", "angular", "frontend", "backend", "api", "web"],
            "mobile": ["ios", "android", "react native", "flutter", "swift", "kotlin"],
            "data": ["data", "analytics", "visualization", "pandas", "jupyter", "sql"],
            "devops": ["docker", "kubernetes", "aws", "cloud", "ci/cd", "deployment"],
            "robotics": ["robot", "ros", "automation", "iot", "embedded", "hardware"],
            "gaming": ["game", "unity", "unreal", "graphics", "engine"],
            "startup": ["startup", "business", "saas", "product", "landing", "marketing"],
        }

        domain_scores = {}
        all_repos = recent_repos + starred_repos

        for repo in all_repos:
            repo_text = (
                f"{repo.get('name', '')} {repo.get('description', '')} {' '.join(repo.get('topics', []))}".lower()
            )

            for domain, keywords in domain_keywords.items():
                for keyword in keywords:
                    if keyword in repo_text:
                        domain_scores[domain] = domain_scores.get(domain, 0) + 1

        return sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)

    def _match_interests_with_evidence(
        self,
        profile_interests: list[str],
        recent_repos: list[dict],
        starred_repos: list[dict],
        languages: list[tuple],
        project_domains: list[tuple],
    ) -> dict[str, Any]:
        """Match stated interests with GitHub evidence"""

        interest_evidence = {}

        for interest in profile_interests:
            evidence = {
                "stated_interest": interest,
                "github_evidence": [],
                "confidence_score": 0,
                "recent_activity": False,
                "learning_indicators": [],
                "building_indicators": [],
            }

            interest_lower = interest.lower()

            # Check recent repos for evidence
            for repo in recent_repos[:10]:
                repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
                if any(word in repo_text for word in interest_lower.split()):
                    evidence["github_evidence"].append(f"Recent repo: {repo.get('name')}")
                    evidence["recent_activity"] = True
                    evidence["building_indicators"].append(repo.get("name"))
                    evidence["confidence_score"] += 3

            # Check starred repos for learning/interest
            for repo in starred_repos[:15]:
                repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
                if any(word in repo_text for word in interest_lower.split()):
                    evidence["github_evidence"].append(f"Starred: {repo.get('name')}")
                    evidence["learning_indicators"].append(repo.get("name"))
                    evidence["confidence_score"] += 1

            # Check language alignment
            for lang, score in languages[:10]:
                if interest_lower in ["ai/ml research", "ai", "machine learning"] and lang.lower() in [
                    "python",
                    "jupyter notebook",
                    "r",
                ]:
                    evidence["github_evidence"].append(f"Uses {lang} (AI/ML language)")
                    evidence["confidence_score"] += 2
                elif interest_lower in ["web3", "blockchain"] and lang.lower() in ["solidity", "rust", "javascript"]:
                    evidence["github_evidence"].append(f"Uses {lang} (blockchain language)")
                    evidence["confidence_score"] += 2

            # Check project domain alignment
            for domain, score in project_domains[:10]:
                if (
                    (interest_lower in ["web3", "blockchain"] and domain == "web3")
                    or (interest_lower in ["ai/ml research", "ai"] and domain == "ai_ml")
                    or (interest_lower == "robotics" and domain == "robotics")
                ):
                    evidence["github_evidence"].append(f"Active in {domain} projects")
                    evidence["confidence_score"] += 2

            interest_evidence[interest] = evidence

        return interest_evidence

    def _determine_current_focus(self, recent_repos: list[dict], interest_evidence: dict[str, Any]) -> dict[str, Any]:
        """Determine what the user is currently focused on"""

        # Look at most recent repos (last 5)
        recent_activity = recent_repos[:5]

        current_themes = {}
        for repo in recent_activity:
            repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()

            # Check against validated interests
            for interest, evidence in interest_evidence.items():
                if evidence["recent_activity"]:
                    current_themes[interest] = current_themes.get(interest, 0) + 1

        # Determine primary focus
        if current_themes:
            primary_focus = max(current_themes, key=current_themes.get)
            return {
                "primary_focus": primary_focus,
                "focus_confidence": current_themes[primary_focus] / len(recent_activity),
                "active_areas": list(current_themes.keys()),
                "recent_projects": [repo.get("name") for repo in recent_activity],
            }
        else:
            return {"primary_focus": "exploring", "focus_confidence": 0.3, "active_areas": [], "recent_projects": []}

    def _generate_content_preferences(
        self, interest_evidence: dict[str, Any], current_focus: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate content preferences based on analysis"""

        preferences = {
            "technical_depth": "medium",
            "content_types": [],
            "avoid_topics": [],
            "priority_sources": [],
            "learning_stage": "intermediate",
        }

        # Determine technical depth based on evidence
        total_confidence = sum(evidence["confidence_score"] for evidence in interest_evidence.values())
        if total_confidence > 20:
            preferences["technical_depth"] = "high"
        elif total_confidence < 5:
            preferences["technical_depth"] = "beginner"

        # Determine preferred content types
        building_activity = any(evidence["building_indicators"] for evidence in interest_evidence.values())
        learning_activity = any(evidence["learning_indicators"] for evidence in interest_evidence.values())

        if building_activity:
            preferences["content_types"].extend(["tools", "libraries", "best_practices", "case_studies"])
        if learning_activity:
            preferences["content_types"].extend(["tutorials", "courses", "documentation", "research"])

        # Set priority sources based on interests
        for interest, evidence in interest_evidence.items():
            if evidence["confidence_score"] > 3:
                if "web3" in interest.lower():
                    preferences["priority_sources"].extend(["GitHub", "Ethereum Blog", "Solana News"])
                elif "ai" in interest.lower():
                    preferences["priority_sources"].extend(["arXiv", "Hugging Face", "OpenAI Blog"])
                elif "hackathon" in interest.lower():
                    preferences["priority_sources"].extend(["Devpost", "MLH", "ETHGlobal"])

        return preferences

    def _assess_experience_level(self, recent_repos: list[dict], repo_analysis: dict) -> dict[str, Any]:
        """Assess experience level based on GitHub activity"""

        indicators = {
            "repo_count": len(recent_repos),
            "has_complex_projects": False,
            "contributes_to_others": False,
            "uses_advanced_features": False,
            "estimated_level": "intermediate",
        }

        # Check for complex projects
        for repo in recent_repos:
            if repo.get("stargazers_count", 0) > 10 or repo.get("forks_count", 0) > 5:
                indicators["has_complex_projects"] = True
                break

        # Estimate level based on various factors
        if indicators["repo_count"] > 20 and indicators["has_complex_projects"]:
            indicators["estimated_level"] = "advanced"
        elif indicators["repo_count"] < 5:
            indicators["estimated_level"] = "beginner"

        return indicators

    def _suggest_opportunity_types(self, interest_evidence: dict[str, Any], current_focus: dict[str, Any]) -> list[str]:
        """Suggest what types of opportunities would be most relevant"""

        opportunity_types = []

        # Based on confidence and activity in different areas
        for interest, evidence in interest_evidence.items():
            if evidence["confidence_score"] > 5:
                if "hackathon" in interest.lower():
                    opportunity_types.extend(["hackathons", "competitions", "bounties"])
                elif "web3" in interest.lower():
                    opportunity_types.extend(["defi_projects", "dao_opportunities", "web3_jobs"])
                elif "ai" in interest.lower():
                    opportunity_types.extend(["ai_research", "ml_positions", "ai_tools"])
                elif "startup" in interest.lower():
                    opportunity_types.extend(["funding", "accelerators", "startup_jobs"])

        # Based on current focus
        if current_focus.get("primary_focus"):
            if current_focus["focus_confidence"] > 0.6:
                opportunity_types.append("advanced_opportunities")
            else:
                opportunity_types.append("learning_opportunities")

        return list(set(opportunity_types))  # Remove duplicates
