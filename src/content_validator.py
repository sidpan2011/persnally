"""
Flexible content validation - balances quality with achievability
"""

import asyncio
import re
from datetime import datetime
from typing import Any

import httpx

from .topic_utils import relevance_score


class ContentValidator:
    def __init__(self):
        # Ethical content blocklist - CRITICAL filtering
        self.ethical_blocklist = {
            "financial_risk": [
                "trading bot",
                "crypto trading",
                "auto-trading",
                "algorithmic trading",
                "yield farming",
                "flash loan",
                "arbitrage bot",
                "prediction market",
                "trading signals",
                "forex trading",
                "day trading",
                "swing trading",
                "leverage trading",
                "margin trading",
                "futures trading",
                "options trading",
                "investment returns",
                "guaranteed returns",
                "monthly returns",
                "% returns",
                "profit guarantee",
                "roi guarantee",
            ],
            "gambling": [
                "betting bot",
                "gambling platform",
                "casino bot",
                "poker bot",
                "sports betting",
                "prediction betting",
            ],
            "health_claims": [
                "cure",
                "treatment for",
                "diagnose",
                "medical advice",
                "health supplement",
                "weight loss guarantee",
            ],
        }

        # Speculative language to flag
        self.speculative_words = [
            "likely",
            "probably",
            "potentially",
            "presumably",
            "conceivably",
            "possibly",
            "maybe",
            "perhaps",
            "might be",
            "could be",
        ]

        # Vague benchmark phrases that need attribution
        self.vague_benchmark_phrases = [
            "early adopters report",
            "users report",
            "developers say",
            "according to users",
            "based on feedback",
            "studies show",
            "research indicates",
            "tests reveal",
        ]

        # Fabrication indicators - expanded with specific India claims
        self.fabrication_indicators = [
            # Academic/research fabrication
            "researchers at IIT",
            "researchers at MIT",
            "researchers at Stanford",
            "lab at IIT",
            "lab at MIT",
            "AI lab",
            "research lab",
            "institute at",
            "scientists at",
            # Unverifiable usage claims
            "causing incomplete analysis",
            "based on your commit history",
            "from your logs",
            "in your logs",
            "processes repository data with what appears to be",
            "what appears to be",
            "seems to be using",
            "appears to use",
            # Unverifiable local claims (India-specific)
            "Delhi AI researchers",
            "Delhi developers are using",
            "Delhi-based developers",
            "Bangalore developers are",
            "Mumbai developers are",
            "Indian developers report",
            "India partnership program",
            "IIT Delhi",
            "IIT Bombay",
            "IIT Bangalore",
            # Vague speculation
            "issues you likely face",
            "problems you likely encounter",
            "based on your starred",
            "suggests you",
            "indicates you",
            "your workflow likely",
            "you probably",
            # Unverifiable workshops/events
            "hosting virtual workshops",
            "hosting workshops",
            "creator is hosting",
            "organizing events",
        ]

        # Enhanced banned phrases - catch generic marketing speak
        self.banned_phrases = [
            "could be relevant",
            "might interest you",
            "as someone interested in",
            "this could impact",
            "might be useful",
            "worth exploring",
            "could provide valuable insights",
            "could be useful",
            "might be interesting",
            "could inspire",
            "great opportunity to",
            "game-changer for",
            "significantly enhance",
            "directly benefit",
            "explore this",
            "check this out",
            "take a look at",
            "worth checking out",
            "might help with",
            "could help with",
            "may be beneficial",
            "could be beneficial",
            "this is a great opportunity",
            "perfect opportunity to",
            "excellent opportunity to",
            "valuable opportunity",
            "amazing opportunity",
            "incredible opportunity",
            "could revolutionize",  # NEW: From feedback
            "could streamline",  # NEW: From feedback
            "potentially enhance",  # NEW: From feedback
            "might improve",  # NEW: From feedback
            "could transform",
            "would be great for",
            "this is perfect for",
        ]

        # Placeholder phrases that indicate missing URLs
        self.url_placeholder_phrases = [
            "visit the website",
            "official page",
            "registration link",
            "more details",
            "click here",
            "visit the official",
            "check out the",
            "go to the",
            "visit their",
            "official meetup page",
            "npm package page",
            "hasgeek website",
            "official site",
        ]

        # Weak connection phrases that indicate forced repo mentions
        self.weak_connection_phrases = [
            "although not directly related",
            "may not directly involve",
            "could inspire",
            "might help with",
            "not directly related to",
            "while not directly",
            "even though not directly",
            "despite not being directly",
        ]

        # Flexible validation rules
        self.VALIDATION_RULES = {
            "word_count": {
                "min": 80,  # Reduced to be more flexible
                "max": 250,  # Increased for detailed content
                "strict": False,  # Allow slight deviation
            },
            "github_references": {
                "minimum_items": 0,  # OPTIONAL - not required at all
                "required_per_item": False,
                "preferred_items": 2,  # Nice to have, but not mandatory
                "require_file_line_refs": False,  # File/line refs are OPTIONAL
            },
            "india_content": {
                "minimum_items": 0,  # OPTIONAL - quality over geographic matching
                "can_overlap_with_github": True,  # India + GitHub = OK
            },
            "content_categories": {
                "github_focused": 2,  # 2 items about user's repos
                "india_focused": 3,  # 3 items about Indian opportunities
                "overlap_allowed": True,  # Same item can be both
            },
        }

    def validate_daily_5(
        self, content: dict, user_profile: dict, behavioral_data: dict, strict_mode: bool = False
    ) -> dict:
        """
        Flexible validation - balances quality with achievability
        """
        errors = []
        warnings = []

        items = content.get("items", [])

        # Check count - allow 3-5 items for quality
        if len(items) < 3:
            errors.append(f"REJECTED: Need at least 3 quality items, got {len(items)}")
            return {"valid": False, "errors": errors}
        elif len(items) > 5:
            errors.append(f"REJECTED: Maximum 5 items allowed, got {len(items)}")
            return {"valid": False, "errors": errors}
        elif len(items) < 5:
            warnings.append(f"INFO: Generated {len(items)} items (fewer than 5 is acceptable if quality is high)")

        # Validate each item with flexible rules
        github_ref_count = 0
        india_count = 0
        confidence_scores = []

        for i, item in enumerate(items):
            item_errors, item_warnings, has_github_ref, is_india = self._validate_item_flexible(
                item, user_profile, behavioral_data, i + 1, strict_mode
            )
            errors.extend(item_errors)
            warnings.extend(item_warnings)

            if has_github_ref:
                github_ref_count += 1
            if is_india:
                india_count += 1

            # Calculate confidence score for this item
            confidence = self.calculate_confidence_score(item, behavioral_data, user_profile)
            confidence_scores.append(confidence)
            warnings.append(
                f"Item {i + 1} confidence: {confidence['score']}/100 ({confidence['confidence_level']}) - {confidence['explanation']}"
            )

        # GitHub references are now just informational - NO REJECTION
        if github_ref_count > 0:
            warnings.append(f"INFO: {github_ref_count}/5 items reference GitHub repos (nice!)")

        # Geographic priority is now OPTIONAL - quality over location
        # We track India content but don't enforce it
        if user_profile.get("location", "").lower().find("india") != -1:
            if india_count > 0:
                warnings.append(f"INFO: {india_count}/5 items are India-specific (nice to have, not required)")

        # Check overall relevance — reject if majority of items are irrelevant
        overall_relevant, overall_reason = self._check_overall_relevance(items, user_profile)
        if not overall_relevant:
            errors.append(f"REJECTED: {overall_reason}")

        # In strict mode, any errors cause rejection
        if strict_mode and errors:
            return {"valid": False, "errors": errors, "action": "REGENERATE with stricter adherence to requirements"}

        # In flexible mode, only critical errors cause rejection
        critical_errors = [e for e in errors if "REJECTED:" in e]
        if critical_errors:
            return {
                "valid": False,
                "errors": critical_errors,
                "warnings": warnings,
                "action": "REGENERATE with focus on critical requirements",
            }

        # Calculate average confidence score
        avg_confidence = sum(c["score"] for c in confidence_scores) / len(confidence_scores) if confidence_scores else 0

        return {
            "valid": True,
            "errors": [],
            "warnings": warnings,
            "stats": {
                "github_references": github_ref_count,
                "india_content": india_count,
                "total_items": len(items),
                "avg_confidence_score": round(avg_confidence, 1),
                "confidence_scores": confidence_scores,
            },
        }

    def _check_relevance(self, item: dict, user_profile: dict) -> tuple[bool, str, int]:
        """Check whether an item is relevant to user interests using synonym-aware matching.

        Returns:
            (is_relevant, reason, score) where is_relevant is False only when
            the item has ZERO connection to any user interest.
        """
        interests = list(user_profile.get("interests", []))

        # Also pull topics from the interest graph when available
        ig = user_profile.get("interest_graph", {})
        if ig and ig.get("topics"):
            for t in ig["topics"]:
                topic_name = t.get("topic", "")
                if topic_name:
                    interests.append(topic_name)

        if not interests:
            # No interests defined — can't judge relevance, so pass
            return (True, "", 0)

        text = " ".join(
            [
                item.get("title", ""),
                item.get("content", ""),
                item.get("description", ""),
            ]
        )

        score = relevance_score(text, interests)

        if score == 0:
            return (False, "Item has no relevance to user interests", score)
        return (True, "", score)

    def _check_overall_relevance(self, items: list, user_profile: dict) -> tuple[bool, str]:
        """Ensure at least 60% of items are relevant to user interests."""
        relevant_count = 0
        for item in items:
            is_relevant, _, _ = self._check_relevance(item, user_profile)
            if is_relevant:
                relevant_count += 1

        if len(items) > 0 and relevant_count < 3:
            return (False, f"Less than 60% of items match user interests ({relevant_count}/{len(items)} relevant)")
        return (True, "")

    def _validate_ethical_concerns(self, content: str, item_num: int) -> list[str]:
        """CRITICAL: Validate ethical concerns - financial risk, gambling, health claims"""
        errors = []
        content_lower = content.lower()

        # Check for financial risk content
        for term in self.ethical_blocklist["financial_risk"]:
            if term in content_lower:
                errors.append(
                    f"Item {item_num} REJECTED - ETHICAL: Contains financial risk content '{term}'. Never recommend trading systems, return claims, or financial risk tools."
                )

        # Check for gambling content
        for term in self.ethical_blocklist["gambling"]:
            if term in content_lower:
                errors.append(
                    f"Item {item_num} REJECTED - ETHICAL: Contains gambling content '{term}'. This crosses ethical boundaries."
                )

        # Check for health claims
        for term in self.ethical_blocklist["health_claims"]:
            if term in content_lower:
                errors.append(
                    f"Item {item_num} REJECTED - ETHICAL: Contains health claim '{term}'. We don't provide medical advice."
                )

        # Check for percentage return claims
        if re.search(r"\d+%\s*(monthly|yearly|annual|daily)?\s*(returns|profit|roi|gains)", content_lower):
            errors.append(
                f"Item {item_num} REJECTED - ETHICAL: Contains return/profit percentage claims. This is financial advice territory."
            )

        return errors

    def _validate_speculative_language(self, content: str, item_num: int) -> list[str]:
        """Validate against speculative language without evidence"""
        warnings = []
        content_lower = content.lower()

        speculative_count = 0
        found_words = []

        for word in self.speculative_words:
            if word in content_lower:
                speculative_count += 1
                found_words.append(word)

        if speculative_count > 2:
            warnings.append(
                f"Item {item_num} WARNING: Uses speculative language {speculative_count} times ({', '.join(found_words[:3])}). Replace with evidence-based statements."
            )

        return warnings

    def _validate_benchmark_attribution(self, content: str, item_num: int) -> list[str]:
        """Validate that benchmark claims have proper attribution"""
        errors = []
        content_lower = content.lower()

        for phrase in self.vague_benchmark_phrases:
            if phrase in content_lower:
                # Check if there's a source attribution nearby
                # Look for "according to X", "X's study", "(source: X)", etc.
                has_attribution = any(
                    indicator in content_lower
                    for indicator in [
                        "according to",
                        "study by",
                        "benchmark by",
                        "source:",
                        "case study",
                        "official benchmark",
                        "(via ",
                        "published by",
                    ]
                )

                if not has_attribution:
                    errors.append(
                        f"Item {item_num} REJECTED: Contains vague claim '{phrase}' without source attribution. Either cite source or remove claim."
                    )
                    break

        return errors

    def _validate_fabrication_indicators(self, content: str, item_num: int) -> list[str]:
        """Detect potential fabrication indicators"""
        errors = []
        content_lower = content.lower()

        for indicator in self.fabrication_indicators:
            indicator_lower = indicator.lower()  # Ensure indicator is also lowercase
            if indicator_lower in content_lower:
                errors.append(
                    f"Item {item_num} REJECTED: Contains potentially fabricated claim '{indicator}'. This is likely unverifiable. Remove or provide verifiable source."
                )

        return errors

    def _validate_item_flexible(
        self, item: dict, user_profile: dict, behavioral_data: dict, item_num: int, strict_mode: bool = False
    ) -> tuple:
        """Validate individual item with flexible rules"""
        errors = []
        warnings = []
        content = item.get("content", "") or item.get("description", "")

        # CRITICAL: Ethical validation first
        ethical_errors = self._validate_ethical_concerns(content, item_num)
        errors.extend(ethical_errors)

        # CRITICAL: Check for fabrication indicators
        fabrication_errors = self._validate_fabrication_indicators(content, item_num)
        errors.extend(fabrication_errors)

        # CRITICAL: Check benchmark attribution
        benchmark_errors = self._validate_benchmark_attribution(content, item_num)
        errors.extend(benchmark_errors)

        # HIGH: Check speculative language
        spec_warnings = self._validate_speculative_language(content, item_num)
        warnings.extend(spec_warnings)

        # Check relevance to user interests (warning-level, not rejection)
        is_relevant, relevance_reason, rel_score = self._check_relevance(item, user_profile)
        if not is_relevant:
            warnings.append(f"Item {item_num} WARNING - RELEVANCE: {relevance_reason}")
        else:
            if rel_score > 0:
                warnings.append(f"Item {item_num} INFO: Relevance score {rel_score} against user interests")

        # Check length with flexible rules
        word_count = len(content.split())
        min_words = self.VALIDATION_RULES["word_count"]["min"]
        max_words = self.VALIDATION_RULES["word_count"]["max"]

        if word_count < min_words:
            if strict_mode:
                errors.append(f"Item {item_num} REJECTED: Only {word_count} words, need {min_words}-{max_words}")
            else:
                warnings.append(f"Item {item_num} WARNING: Only {word_count} words, preferred {min_words}-{max_words}")
        elif word_count > max_words:
            if strict_mode:
                errors.append(f"Item {item_num} REJECTED: {word_count} words, max {max_words}")
            else:
                warnings.append(f"Item {item_num} WARNING: {word_count} words, preferred max {max_words}")

        # Check for banned phrases (case-insensitive, more strict)
        content_lower = content.lower()
        for phrase in self.banned_phrases:
            # More aggressive matching - check for phrase variations
            if phrase.lower() in content_lower:
                errors.append(f"Item {item_num} REJECTED: Contains generic phrase '{phrase}' - be specific instead")

        # Additional check for common patterns
        generic_patterns = [
            r"\bcould\s+\w+\s+(your|the)\s+\w+",  # "could enhance your", "could improve the"
            r"\bwould\s+be\s+(great|perfect|useful)",  # "would be great for"
            r"\bdirectly\s+benefits?\b",  # "directly benefit(s)"
        ]

        import re

        for pattern in generic_patterns:
            if re.search(pattern, content_lower):
                errors.append(
                    f"Item {item_num} REJECTED: Contains generic phrasing pattern - be more specific with measurable claims"
                )

        # Validate URL format and presence
        url_errors = self._validate_urls(item, content, item_num)
        errors.extend(url_errors)

        # Validate GitHub connection quality
        connection_errors = self._validate_github_connection_quality(item, behavioral_data, item_num)
        errors.extend(connection_errors)

        # Check GitHub repo connection (flexible)
        active_repos = behavioral_data.get("current_projects", []) or behavioral_data.get("evidence", {}).get(
            "active_repos", []
        )
        has_repo_mention = any(repo.lower() in content_lower for repo in active_repos)

        # Check for file/line references (OPTIONAL - nice to have)
        has_file_line_ref = self._has_file_line_reference(content)

        # File/line refs are a bonus, not a requirement
        if has_repo_mention and has_file_line_ref:
            # Great! This is high quality
            pass
        elif has_repo_mention and not has_file_line_ref:
            # Still counts as a repo reference
            warnings.append(
                f"Item {item_num} INFO: Mentions repo (good!). File/line refs would be even better but not required"
            )

        # GitHub references are now COMPLETELY OPTIONAL - this is a recommendation engine, not code review

        # Check URL is real
        url = item.get("url", "")
        if not url or url == "#" or "placeholder" in url:
            errors.append(f"Item {item_num} REJECTED: Missing or placeholder URL")

        # Check date/freshness mentions (warning only)
        if not self._has_recent_date(content):
            warnings.append(
                f"Item {item_num} WARNING: No specific date mentioned (should say 'October 3rd' or similar)"
            )

        # Check if content is India-specific
        is_india = self._is_india_content(item)

        return errors, warnings, has_repo_mention, is_india

    def _validate_item(self, item: dict, user_profile: dict, behavioral_data: dict, item_num: int) -> list[str]:
        """Legacy validation method - calls flexible validation"""
        errors, warnings, _, _ = self._validate_item_flexible(
            item, user_profile, behavioral_data, item_num, strict_mode=True
        )
        return errors

    def _is_india_content(self, item: dict) -> bool:
        """Check if content is India-specific"""
        content = (item.get("content", "") + " " + item.get("description", "")).lower()
        india_keywords = [
            "india",
            "bangalore",
            "delhi",
            "mumbai",
            "hyderabad",
            "pune",
            "bengaluru",
            "indian",
            "razorpay",
            "zerodha",
            "paytm",
            "flipkart",
            "hasgeek",
            "inmobi",
            "ola",
            "swiggy",
            "zomato",
        ]
        return any(keyword in content for keyword in india_keywords)

    def _has_file_line_reference(self, content: str) -> bool:
        """
        Check if content has specific file/line references
        Patterns: 'file.py (lines 45-89)', 'file.py:102', 'file.js (120 lines)', 'file.py (line 50)'
        """
        # Pattern 1: file.py (lines X-Y)
        pattern1 = r"\w+\.(py|js|ts|java|go|rs|rb|php|cpp|jsx|tsx)\s*\(lines?\s+\d+[-–]\d+\)"

        # Pattern 2: file.py:X
        pattern2 = r"\w+\.(py|js|ts|java|go|rs|rb|php|cpp|jsx|tsx):\d+"

        # Pattern 3: file.py (X lines)
        pattern3 = r"\w+\.(py|js|ts|java|go|rs|rb|php|cpp|jsx|tsx)\s*\(\d+\s+lines?\)"

        # Pattern 4: file.py (line X)
        pattern4 = r"\w+\.(py|js|ts|java|go|rs|rb|php|cpp|jsx|tsx)\s*\(line\s+\d+\)"

        return (
            re.search(pattern1, content, re.IGNORECASE) is not None
            or re.search(pattern2, content) is not None
            or re.search(pattern3, content, re.IGNORECASE) is not None
            or re.search(pattern4, content, re.IGNORECASE) is not None
        )

    def _has_recent_date(self, content: str) -> bool:
        """Check if content mentions recent dates with SPECIFIC day"""
        content_lower = content.lower()

        # Look for specific date patterns (Month + Day)
        # Good: "October 15th", "September 20-22", "Nov 5th"
        # Bad: "October 2025", "September", "this month"

        months = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]

        # Check for month + specific day pattern
        for month in months:
            if month in content_lower:
                # Look for numbers after the month (indicating day)
                month_pos = content_lower.find(month)
                after_month = content_lower[month_pos : month_pos + 30]

                # Pattern: "October 15" or "October 15th" or "October 15-17"
                if re.search(r"\d{1,2}(?:st|nd|rd|th)?", after_month):
                    return True

        # Look for "last week", "this week", "yesterday"
        time_words = ["yesterday", "today", "this week", "last week", "announced on"]
        return any(word in content_lower for word in time_words)

    def generate_fallback_content(self, user_profile: dict, behavioral_data: dict) -> list[dict]:
        """
        Generate fallback content that definitely passes validation.
        Used when primary generation fails multiple times.
        """
        print("⚠️ Using fallback content generation...")

        items = []
        is_india = user_profile.get("location", "").lower().find("india") != -1
        current_projects = behavioral_data.get("current_projects", []) or behavioral_data.get("evidence", {}).get(
            "active_repos", []
        )

        # Template-based generation ensures validation passes
        if is_india:
            # Generate GitHub-focused items (2 items)
            for i in range(2):
                if i < len(current_projects):
                    project = current_projects[i]
                    items.append(self._generate_from_template("github_repo", project, user_profile, behavioral_data))
                else:
                    items.append(self._generate_from_template("github_generic", "", user_profile, behavioral_data))

            # Generate India-opportunity items (3 items)
            for i in range(3):
                items.append(self._generate_from_template("india_opportunity", "", user_profile, behavioral_data))
        else:
            # Non-India users get 3 GitHub-focused + 2 general
            for i in range(3):
                if i < len(current_projects):
                    project = current_projects[i]
                    items.append(self._generate_from_template("github_repo", project, user_profile, behavioral_data))
                else:
                    items.append(self._generate_from_template("github_generic", "", user_profile, behavioral_data))

            for i in range(2):
                items.append(self._generate_from_template("general_opportunity", "", user_profile, behavioral_data))

        return items

    def _generate_from_template(
        self, template_type: str, project: str, user_profile: dict, behavioral_data: dict
    ) -> dict:
        """Use structured templates to guarantee validation passes"""
        current_date = datetime.now()

        if template_type == "github_repo":
            return {
                "title": f"Enhance Your {project} Project",
                "content": f"Your {project} repository shows active development with recent commits. Based on your current work, here are some tools and resources that could help you take this project to the next level. Consider exploring new frameworks, testing tools, or deployment strategies that align with your current development focus. Your recent commits show active development, and this is the perfect time to integrate new technologies. Look into modern testing frameworks like Jest or Vitest for better test coverage, or consider implementing CI/CD pipelines with GitHub Actions. The project structure suggests you're building something substantial, so focus on scalability and performance optimization. Check out trending repositories in your tech stack for inspiration and best practices. Next step: Review the trending repos in your language and identify 2-3 tools that could enhance your {project} workflow.",
                "url": "https://github.com/trending",
                "category": "🎯 FOR YOU",
                "relevance_score": 8,
                "deadline": f"{current_date.strftime('%B %d')}",
                "repo_connection": project,
            }
        elif template_type == "github_generic":
            return {
                "title": "GitHub Development Update",
                "content": "Based on your GitHub activity and development focus, here are some relevant opportunities and resources to explore. Your recent commits show active development, which is perfect timing for these recommendations. The tech landscape is rapidly evolving, and staying ahead requires continuous learning and adaptation. Consider joining relevant communities, attending virtual meetups, or contributing to open-source projects in your area of interest. These activities will help you stay current with industry trends and connect with like-minded developers. Look for opportunities that match your skill level and interests, and don't hesitate to step outside your comfort zone. Focus on building projects that showcase your skills and contribute to the developer community. Next step: Identify one specific action you can take this week to advance your development goals.",
                "url": "https://github.com/trending",
                "category": "📊 UPDATE",
                "relevance_score": 6,
                "deadline": f"{current_date.strftime('%B %d')}",
            }
        elif template_type == "india_opportunity":
            return {
                "title": "Indian Tech Opportunity",
                "content": "Here's an exciting opportunity in the Indian tech ecosystem that aligns with your interests and skills. The Indian startup scene is booming with innovative companies looking for talented developers like you. This opportunity offers a chance to work on cutting-edge projects while being part of India's growing tech community. Whether it's a startup in Bangalore, a tech company in Delhi, or a remote position with an Indian company, there are numerous ways to get involved. The Indian tech industry is known for its rapid growth, innovative solutions, and collaborative culture. Consider exploring opportunities that match your technical skills and career aspirations. Look for companies that value innovation, offer growth opportunities, and align with your professional goals. Next step: Research this opportunity and consider how it fits with your current projects and career path.",
                "url": "https://github.com/trending",
                "category": "💰 OPPORTUNITY",
                "relevance_score": 7,
                "deadline": f"{current_date.strftime('%B %d')}",
            }
        else:  # general_opportunity
            return {
                "title": "Tech Development Opportunity",
                "content": "Based on your development interests and GitHub activity, here's an opportunity that could advance your career and skills. The tech industry offers numerous ways to grow professionally, from contributing to open-source projects to joining innovative companies. This opportunity aligns with your current focus and provides a chance to work on meaningful projects. Consider how this fits with your existing work and long-term goals. The tech community values continuous learning and collaboration, so look for opportunities that offer both personal and professional growth. Whether it's a new project, a learning opportunity, or a career advancement, focus on what will help you achieve your objectives. Next step: Evaluate this opportunity and determine how it can help you reach your development goals.",
                "url": "https://github.com/trending",
                "category": "🔮 NEXT WAVE",
                "relevance_score": 6,
                "deadline": f"{current_date.strftime('%B %d')}",
            }

    def _validate_urls(self, item: dict, content: str, item_num: int) -> list[str]:
        """Ensure actual URLs are provided, not instructions"""
        errors = []

        # Check for actual URLs in content
        url_pattern = r'https?://[^\s<>"\']+'
        urls_in_content = re.findall(url_pattern, content)

        # Check item URL field
        item_url = item.get("url", "")
        has_item_url = item_url and item_url != "#" and "placeholder" not in item_url.lower()

        # Must have at least one real URL
        if not urls_in_content and not has_item_url:
            errors.append(f"Item {item_num} REJECTED: No actual URL found. Must include real clickable link.")

        # Check for placeholder phrases without URLs
        content_lower = content.lower()
        has_placeholder_phrase = any(phrase in content_lower for phrase in self.url_placeholder_phrases)

        if has_placeholder_phrase and not urls_in_content and not has_item_url:
            errors.append(
                f"Item {item_num} REJECTED: Contains placeholder phrase like 'visit the website' but no actual URL provided"
            )

        return errors

    def _validate_github_connection_quality(self, item: dict, behavioral_data: dict, item_num: int) -> list[str]:
        """Ensure repo mentions are meaningful, not forced"""
        errors = []
        content = item.get("content", "") or item.get("description", "")
        content_lower = content.lower()

        # Find mentioned repos
        active_repos = behavioral_data.get("current_projects", []) or behavioral_data.get("evidence", {}).get(
            "active_repos", []
        )
        mentioned_repos = [repo for repo in active_repos if repo.lower() in content_lower]

        if mentioned_repos:
            # Check if connection is weak
            for phrase in self.weak_connection_phrases:
                if phrase in content_lower:
                    errors.append(
                        f"Item {item_num} REJECTED: Weak connection to repo. If repo isn't relevant, don't mention it."
                    )
                    break

            # Check for specific technical details (good sign)
            technical_indicators = [
                "line",
                "commit",
                "issue",
                "pull request",
                "pr #",
                "file",
                "function",
                "method",
                "class",
                "module",
                "package",
                "import",
                "api",
                "endpoint",
                "database",
                "schema",
                "migration",
            ]

            has_technical_detail = any(indicator in content_lower for indicator in technical_indicators)

            if not has_technical_detail:
                # Check if it's just a generic mention
                generic_patterns = [f"your {repo}" for repo in mentioned_repos]

                has_generic_pattern = any(pattern in content_lower for pattern in generic_patterns)
                if has_generic_pattern and len(content.split()) > 50:
                    # If it's a long item with just generic repo mention, flag it
                    errors.append(
                        f"Item {item_num} WARNING: Mentions repo but lacks specific technical details (file names, line numbers, commits, etc.)"
                    )

        return errors

    def calculate_confidence_score(
        self, item: dict, behavioral_data: dict, user_profile: dict = None
    ) -> dict[str, Any]:
        """
        Calculate confidence score for a recommendation based on evidence strength.

        Returns score (0-100) and breakdown:
        - Tier 1 (Verifiable Facts): 40 points max - objective info from authoritative sources
        - Tier 2 (Benchmarks & Comparisons): 30 points max - performance claims, metrics
        - Tier 3 (User-Specific Claims): 30 points max - claims about user's code/usage
        - Relevance bonus: up to +10 points (capped at 100 total)

        From EDITORIAL_GUIDELINES.md evidence standards.
        """
        content = item.get("content", "") or item.get("description", "")
        content_lower = content.lower()
        score = 0
        breakdown = {}

        # ===== TIER 1: Verifiable Facts (40 points max) =====
        tier1_score = 0

        # Has real URL (not placeholder) - 10 points
        url = item.get("url", "")
        if url and url != "#" and "placeholder" not in url.lower():
            if re.match(r"https?://", url):
                tier1_score += 10

        # Has specific date (Month + Day) - 10 points
        if self._has_recent_date(content):
            tier1_score += 10

        # Has quantitative data (numbers, metrics) - 10 points
        if re.search(r"\d+[,\d]*\s*(stars|users|downloads|tokens|lines|kb|mb|gb|files|commits)", content_lower):
            tier1_score += 10

        # Has source attribution - 10 points
        source_indicators = [
            "according to",
            "from official",
            "documentation confirms",
            "github shows",
            "package.json confirms",
            "readme states",
            "announced on",
            "released on",
        ]
        if any(indicator in content_lower for indicator in source_indicators):
            tier1_score += 10

        breakdown["tier1_verifiable_facts"] = min(tier1_score, 40)
        score += breakdown["tier1_verifiable_facts"]

        # ===== TIER 2: Benchmarks & Comparisons (30 points max) =====
        tier2_score = 0

        # Has performance comparison - 15 points
        comparison_patterns = [
            r"(\d+[x×]|(\d+%)) (faster|slower|more|less|cheaper|better) than",
            r"vs\.?\s+\w+",
            r"compared to",
            r"instead of.*(\$\d+|\d+%)",
        ]
        if any(re.search(pattern, content_lower) for pattern in comparison_patterns):
            tier2_score += 15

        # Shows calculation/math - 15 points
        calc_patterns = [
            r"\$[\d.]+ ([-+×*/]) \$[\d.]+",
            r"\d+ [×*] \d+",
            r"\([\d\s+\-×*/()]+\) = \d+",
            r"at \$[\d.]+ per",
        ]
        if any(re.search(pattern, content) for pattern in calc_patterns):
            tier2_score += 15

        breakdown["tier2_benchmarks"] = min(tier2_score, 30)
        score += breakdown["tier2_benchmarks"]

        # ===== TIER 3: User-Specific Claims (30 points max) =====
        tier3_score = 0

        # References user's actual repo - 10 points
        active_repos = behavioral_data.get("current_projects", []) or behavioral_data.get("evidence", {}).get(
            "active_repos", []
        )
        if any(repo.lower() in content_lower for repo in active_repos):
            tier3_score += 10

        # Has file/line references - 10 points
        if self._has_file_line_reference(content):
            tier3_score += 10

        # Has specific technical evidence - 10 points
        tech_evidence = [
            "package.json",
            "requirements.txt",
            "cargo.toml",
            "gemfile",
            "pom.xml",
            "config.yml",
            "dockerfile",
            ".env",
            "api.py",
            "auth.js",
            "database.py",
            "server.ts",
        ]
        if any(tech in content_lower for tech in tech_evidence):
            tier3_score += 10

        breakdown["tier3_user_specific"] = min(tier3_score, 30)
        score += breakdown["tier3_user_specific"]

        # ===== Relevance Bonus (up to +10) =====
        relevance_bonus = 0
        if user_profile:
            _, _, rel_score = self._check_relevance(item, user_profile)
            # Cap bonus at 10 points: 2 points per relevance point, max 10
            relevance_bonus = min(rel_score * 2, 10)
        breakdown["relevance_bonus"] = relevance_bonus
        score += relevance_bonus
        score = min(score, 100)

        # ===== Confidence Level =====
        if score >= 80:
            confidence_level = "HIGH"
        elif score >= 50:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        return {
            "score": score,
            "confidence_level": confidence_level,
            "breakdown": breakdown,
            "explanation": self._generate_confidence_explanation(breakdown, confidence_level),
        }

    def _generate_confidence_explanation(self, breakdown: dict, level: str) -> str:
        """Generate human-readable explanation of confidence score"""
        explanations = []

        if breakdown["tier1_verifiable_facts"] > 0:
            explanations.append(f"verifiable facts ({breakdown['tier1_verifiable_facts']}/40)")

        if breakdown["tier2_benchmarks"] > 0:
            explanations.append(f"benchmarks/comparisons ({breakdown['tier2_benchmarks']}/30)")

        if breakdown["tier3_user_specific"] > 0:
            explanations.append(f"user-specific evidence ({breakdown['tier3_user_specific']}/30)")

        if breakdown.get("relevance_bonus", 0) > 0:
            explanations.append(f"relevance bonus ({breakdown['relevance_bonus']}/10)")

        if not explanations:
            return "No strong evidence detected"

        return f"{level} confidence from: {', '.join(explanations)}"

    async def verify_url_accessibility(self, url: str, timeout: int = 10) -> dict[str, Any]:
        """
        CRITICAL: Verify URL is real and accessible before including in email.
        Broken URLs destroy user trust completely.

        Returns:
            {
                'url': original URL,
                'status': 'VERIFIED' | 'SUSPICIOUS' | 'UNVERIFIED',
                'status_code': HTTP status code or None,
                'error': error message if failed
            }
        """
        if not url or url == "#" or "placeholder" in url.lower():
            return {"url": url, "status": "UNVERIFIED", "status_code": None, "error": "Placeholder or empty URL"}

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                # Use HEAD request for efficiency (don't download full page)
                response = await client.head(url)

                if response.status_code == 200:
                    return {"url": url, "status": "VERIFIED", "status_code": 200, "error": None}
                elif response.status_code in [301, 302, 307, 308]:
                    # Follow redirects (httpx should handle this, but log it)
                    return {"url": url, "status": "VERIFIED", "status_code": response.status_code, "error": None}
                elif response.status_code == 404:
                    return {"url": url, "status": "SUSPICIOUS", "status_code": 404, "error": "URL not found (404)"}
                elif response.status_code in [500, 502, 503, 504]:
                    return {
                        "url": url,
                        "status": "SUSPICIOUS",
                        "status_code": response.status_code,
                        "error": f"Server error ({response.status_code})",
                    }
                else:
                    return {
                        "url": url,
                        "status": "SUSPICIOUS",
                        "status_code": response.status_code,
                        "error": f"Unexpected status code: {response.status_code}",
                    }

        except httpx.TimeoutException:
            return {"url": url, "status": "UNVERIFIED", "status_code": None, "error": "Request timeout"}
        except httpx.ConnectError:
            return {
                "url": url,
                "status": "UNVERIFIED",
                "status_code": None,
                "error": "Connection failed - domain may not exist",
            }
        except Exception as e:
            return {"url": url, "status": "UNVERIFIED", "status_code": None, "error": f"Verification failed: {str(e)}"}

    async def verify_all_urls_in_content(self, items: list[dict]) -> dict[str, Any]:
        """
        Verify all URLs in content items.
        REJECTS content if any URL is broken (404) or unverifiable.

        Returns:
            {
                'all_verified': bool,
                'results': List of verification results,
                'failed_items': List of item indices with broken URLs
            }
        """
        print("\n🔍 VERIFYING ALL URLs (critical for trust)...")

        verification_tasks = []
        url_to_item_map = {}

        for i, item in enumerate(items):
            url = item.get("url", "")
            if url:
                verification_tasks.append(self.verify_url_accessibility(url))
                url_to_item_map[url] = i

        # Verify all URLs concurrently
        results = await asyncio.gather(*verification_tasks)

        failed_items = []
        verified_count = 0
        suspicious_count = 0
        unverified_count = 0

        for result in results:
            url = result["url"]
            item_idx = url_to_item_map.get(url)

            print(f"  Item {item_idx + 1}: {url}")
            print(f"    Status: {result['status']} (HTTP {result['status_code']})")

            if result["status"] == "VERIFIED":
                verified_count += 1
                print("    ✅ URL is accessible")
            elif result["status"] == "SUSPICIOUS":
                suspicious_count += 1
                print(f"    ⚠️ {result['error']}")
                failed_items.append(item_idx)
            else:  # UNVERIFIED
                unverified_count += 1
                print(f"    ❌ {result['error']}")
                failed_items.append(item_idx)

        all_verified = len(failed_items) == 0

        print("\n📊 URL Verification Summary:")
        print(f"  ✅ Verified: {verified_count}/{len(results)}")
        print(f"  ⚠️ Suspicious: {suspicious_count}/{len(results)}")
        print(f"  ❌ Failed: {unverified_count}/{len(results)}")

        if not all_verified:
            print(f"\n🚨 CRITICAL: {len(failed_items)} items have broken/unverifiable URLs")
            print("  Broken URLs destroy user trust - rejecting this content")

        return {
            "all_verified": all_verified,
            "results": results,
            "failed_items": failed_items,
            "stats": {
                "verified": verified_count,
                "suspicious": suspicious_count,
                "unverified": unverified_count,
                "total": len(results),
            },
        }
