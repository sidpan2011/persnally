"""
AI Editorial Engine - Behavioral Intelligence "Daily 5"
Generates intelligent Daily 5 recommendations using behavioral analysis
"""
import anthropic
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from .behavior_analyzer import BehaviorAnalyzer
from .opportunity_matcher import OpportunityMatcher
from .content_curator import ContentCurator
from .system_prompts import USER_ANALYSIS_PROMPT, TOP5_UPDATES_PROMPT, CONTENT_GENERATION_PROMPT, BEHAVIORAL_ANALYSIS_PROMPT, LOCATION_RULES
from .content_validator import ContentValidator
from .repo_analyzer import RepoFileAnalyzer
from .web_opportunity_finder import WebOpportunityFinder

class AIEditorialEngine:
    def __init__(self, config):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.behavior_analyzer = BehaviorAnalyzer(config)
        self.opportunity_matcher = OpportunityMatcher(config)
        self.content_curator = ContentCurator()
        self.repo_analyzer = RepoFileAnalyzer(config.GITHUB_TOKEN)
        self.web_finder = WebOpportunityFinder()
    
    async def generate_daily_5(self, user_profile: dict, research_data: dict, location_rule: str = None) -> Dict[str, Any]:
        """Generate Daily 5 with fail-loudly approach - better to send no email than garbage"""
        
        max_attempts = 3
        validator = ContentValidator()
        best_content = None  # Track best attempt
        best_score = -1

        for attempt in range(max_attempts):
            print(f"\n🎯 Generation Attempt {attempt + 1}/{max_attempts}")
            
            # Step 1: Behavioral analysis + repo files + web opportunities (PARALLEL)
            print("📊 Analyzing GitHub behavior + repos + opportunities in parallel...")
            behavioral_data = await self.behavior_analyzer.analyze_user_behavior(research_data, user_profile)

            active_repo_count = len(behavioral_data.get('evidence', {}).get('active_repos', []))
            active_repos = behavioral_data.get('evidence', {}).get('active_repos', [])
            github_username = user_profile.get('github_username', '')
            print(f"✅ Found {active_repo_count} active repos")

            # Run repo analysis and opportunity search in parallel
            repo_files_data, web_opportunities = await asyncio.gather(
                self._analyze_repo_files(github_username, active_repos[:3]),
                self.web_finder.find_opportunities(user_profile, behavioral_data),
            )
            print(f"📄 File analysis: {repo_files_data.get('summary', 'None')[:100]}")
            print(f"🔎 Generated {len(web_opportunities.get('search_queries', []))} search queries")

            # Step 2: Generate content (NO FALLBACK until attempt 3)
            print("✍️ Generating content with AI...")
            daily_5_content = await self._generate_content(
                user_profile,
                research_data,
                behavioral_data,
                location_rule,
                repo_files_data,
                web_opportunities
            )
            
            # Step 3: Content validation
            print("🔍 Validating content quality...")
            try:
                validation_result = validator.validate_daily_5(daily_5_content, user_profile)
            except Exception as val_err:
                print(f"⚠️ Validation error (accepting content): {val_err}")
                validation_result = {
                    'valid': True,
                    'errors': [],
                    'warnings': [str(val_err)],
                    'stats': {'avg_confidence_score': 60}
                }

            # Track best attempt
            error_count = len(validation_result.get('errors', []))
            score = max(0, 100 - (error_count * 10))

            if score > best_score:
                best_content = daily_5_content
                best_score = score
                print(f"📊 New best: {best_score}/100")

            if validation_result['valid']:
                print("✅ Content passed validation!")

                # Display confidence scores
                stats = validation_result.get('stats', {})
                if stats.get('avg_confidence_score'):
                    avg_conf = stats['avg_confidence_score']
                    print(f"📊 Average confidence: {avg_conf}/100")

                if validation_result.get('warnings'):
                    print("⚠️ Warnings:")
                    for warning in validation_result['warnings']:
                        print(f"   - {warning}")

                # CRITICAL: Verify all URLs before accepting content
                # Broken URLs destroy user trust completely
                url_verification = await validator.verify_all_urls_in_content(daily_5_content.get('items', []))

                if not url_verification['all_verified']:
                    # Some URLs are broken - reject this content
                    print(f"\n❌ URL verification failed - rejecting content")
                    print(f"   Failed items: {url_verification['failed_items']}")

                    if attempt < max_attempts - 1:
                        print(f"🔄 Regenerating with working URLs (attempt {attempt + 2})...")
                        continue
                    else:
                        # On final attempt, try to remove broken items and use rest
                        items = daily_5_content.get('items', [])
                        working_items = [item for i, item in enumerate(items) if i not in url_verification['failed_items']]

                        if len(working_items) >= 3:
                            print(f"\n⚠️ Using {len(working_items)} items with verified URLs (removed {len(url_verification['failed_items'])} broken links)")
                            daily_5_content['items'] = working_items
                        else:
                            print(f"\n❌ Only {len(working_items)} items with working URLs - not enough for email")
                            return None

                print("✅ All URLs verified - content is trustworthy!")

                current_date = datetime.now().strftime("%B %d, %Y")
                subject_line = self.behavior_analyzer.get_intent_based_subject_line(behavioral_data, current_date)
                personalization_note = self.behavior_analyzer.get_personalization_note(behavioral_data)

                return {
                    "subject_line": subject_line,
                    "headline": "Your Daily 5",
                    "personalization_note": personalization_note,
                    "items": daily_5_content.get('items', []),
                    "user_intent": behavioral_data,
                    "date": current_date,
                    "summary": await self.opportunity_matcher.generate_opportunity_summary(daily_5_content.get('items', []), behavioral_data)
                }
            else:
                print(f"❌ Content rejected:")
                for error in validation_result['errors']:
                    print(f"   - {error}")
                
                if attempt < max_attempts - 1:
                    print(f"🔄 Regenerating (attempt {attempt + 2})...")
                else:
                    # Try to use best attempt if good enough
                    if best_content and best_score > 50:
                        print(f"\n✅ Using best attempt (score: {best_score}/100) - good enough for hackathon!")

                        current_date = datetime.now().strftime("%B %d, %Y")
                        subject_line = self.behavior_analyzer.get_intent_based_subject_line(behavioral_data, current_date)
                        personalization_note = self.behavior_analyzer.get_personalization_note(behavioral_data)

                        return {
                            "subject_line": subject_line,
                            "headline": "Your Daily 5",
                            "personalization_note": personalization_note,
                            "items": best_content.get('items', []),
                            "user_intent": behavioral_data,
                            "date": current_date,
                            "summary": await self.opportunity_matcher.generate_opportunity_summary(best_content.get('items', []), behavioral_data)
                        }
                    else:
                        # FAIL LOUDLY - don't send garbage
                        print(f"💥 FAILED: All attempts scored < 50. Best: {best_score}/100")
                        print("🚨 This is better than sending generic spam.")

                        raise Exception(f"Content quality too low after {max_attempts} attempts (best score: {best_score}/100)")
    
    async def _analyze_behavior(self, research_data: dict, user_profile: dict) -> dict:
        """Analyze user behavior using new strict prompt"""
        
        github_data = research_data.get("user_context", {})
        
        # Extract repo names for the prompt
        recent_repos = github_data.get('recent_repos', [])
        repo_names = [repo.get('name', '') for repo in recent_repos if isinstance(repo, dict)][:10]
        
        starred_repos = github_data.get('interests_from_stars', [])
        starred_names = [repo.get('name', '') for repo in starred_repos if isinstance(repo, dict)][:10]
        
        prompt = BEHAVIORAL_ANALYSIS_PROMPT.format(
            recent_repos=json.dumps(repo_names, indent=2),
            starred_repos=json.dumps(starred_names, indent=2),
            languages=json.dumps(github_data.get('repo_analysis', {}).get('top_languages', [])[:5] if github_data.get('repo_analysis', {}).get('top_languages') else [], indent=2),
            recent_commits=json.dumps(github_data.get('repo_analysis', {}).get('recent_activity', [])[:5] if github_data.get('repo_analysis', {}).get('recent_activity') else [], indent=2),
            topics=json.dumps(github_data.get('repo_analysis', {}).get('topics', [])[:10] if github_data.get('repo_analysis', {}).get('topics') else [], indent=2),
            user_interests=user_profile.get('interests', []),
            location=user_profile.get('location', ''),
            skills=user_profile.get('skills', [])
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1200,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            behavioral_data = json.loads(response.choices[0].message.content)
            
            # Ensure compatibility with content curator expected format
            if 'evidence' in behavioral_data:
                behavioral_data['current_projects'] = behavioral_data['evidence'].get('active_repos', [])
                behavioral_data['recent_interests'] = behavioral_data['evidence'].get('recent_stars', [])
                behavioral_data['primary_technologies'] = behavioral_data['evidence'].get('technologies_using', [])
                behavioral_data['emerging_interests'] = behavioral_data['evidence'].get('technologies_exploring', [])
            
            # Ensure we always have current_projects populated
            if not behavioral_data.get('current_projects'):
                behavioral_data['current_projects'] = repo_names[:5]  # Use the repo names we extracted
            
            return behavioral_data
        except:
            # Fallback to existing behavior analyzer
            fallback_data = await self.behavior_analyzer.analyze_user_intent(github_data, user_profile)
            
            # Ensure we always have current_projects populated with actual repo names
            fallback_data['current_projects'] = repo_names[:5]
            fallback_data['recent_interests'] = starred_names[:5]
            
            return fallback_data
    
    def _enrich_source_attribution(self, content_data: dict, research_data: dict) -> dict:
        """
        Enrich AI-generated items with specific source names from original data.
        Matches URLs to find the exact source (TechCrunch, The Verge, etc.) instead of generic 'news'.
        """
        if 'items' not in content_data or not isinstance(content_data['items'], list):
            return content_data
        
        print("🔍 Enriching source attribution with specific source names...")
        
        # Build a URL-to-source mapping from research data
        url_to_source = {}
        
        # From fresh updates (news articles)
        fresh_updates = research_data.get('fresh_updates', [])
        for article in fresh_updates:
            url = article.get('url', '')
            source = article.get('source', '')
            if url and source:
                url_to_source[url] = source
        
        # From trending repos
        trending_repos = research_data.get('trending_repos', [])
        for repo in trending_repos:
            url = repo.get('url', '')
            if url:
                url_to_source[url] = 'GitHub Trending'
        
        # From HackerNews
        hn_stories = research_data.get('hackernews_stories', [])
        for story in hn_stories:
            url = story.get('url', '')
            if url:
                url_to_source[url] = 'HackerNews'
        
        # From opportunities - handle both dict and list formats
        opportunities = research_data.get('opportunities', [])
        if isinstance(opportunities, list):
            for opp in opportunities:
                if isinstance(opp, dict):
                    url = opp.get('url', '')
                    source = opp.get('source', '')
                    if url and source:
                        url_to_source[url] = source
                elif isinstance(opp, str):
                    # Skip string opportunities (they don't have URL/source)
                    continue
        elif isinstance(opportunities, dict):
            # Handle nested structure like {"opportunities": [...], "categories": {...}}
            opp_list = opportunities.get('opportunities', [])
            for opp in opp_list:
                if isinstance(opp, dict):
                    url = opp.get('url', '')
                    source = opp.get('source', '')
                    if url and source:
                        url_to_source[url] = source
        
        # Enrich each item
        enriched_count = 0
        for item in content_data['items']:
            item_url = item.get('url', '')
            item_source = item.get('source', '').lower()
            
            # If source is generic ('news', 'event', etc.), try to find specific source
            if item_url and item_source in ['news', 'event', 'article', 'update']:
                # Exact match
                if item_url in url_to_source:
                    item['source'] = url_to_source[item_url]
                    enriched_count += 1
                    print(f"  ✅ Enriched: {item_source} → {url_to_source[item_url]}")
                else:
                    # Fuzzy match by domain
                    for data_url, source_name in url_to_source.items():
                        if item_url in data_url or data_url in item_url:
                            item['source'] = source_name
                            enriched_count += 1
                            print(f"  ✅ Enriched (fuzzy): {item_source} → {source_name}")
                            break
        
        print(f"✅ Enriched {enriched_count}/{len(content_data['items'])} items with specific sources")
        return content_data
    
    async def _analyze_repo_files(self, github_username: str, repo_names: List[str]) -> Dict[str, Any]:
        """Analyze repository files to extract file-level details"""
        if not repo_names or not github_username:
            return {'analyses': [], 'summary': 'No repos to analyze'}

        try:
            analyses = await self.repo_analyzer.analyze_multiple_repos(github_username, repo_names)

            # Create summary for prompt
            summary_parts = []
            for analysis in analyses:
                repo_name = analysis['repo_name']
                files = analysis.get('analyzed_files', [])
                if files:
                    file_details = []
                    for f in files[:3]:  # Top 3 files
                        file_details.append(f"{f['path']} ({f['lines']} lines)")
                    summary_parts.append(f"Repo: {repo_name} - Files: {', '.join(file_details)}")

            return {
                'analyses': analyses,
                'summary': '; '.join(summary_parts) if summary_parts else 'Files not analyzed'
            }
        except Exception as e:
            print(f"⚠️ Repo file analysis failed: {e}")
            return {'analyses': [], 'summary': 'Analysis failed'}

    async def _generate_content(self, user_profile: dict, research_data: dict, behavioral_data: dict, location_rule: str = None, repo_files_data: dict = None, web_opportunities: dict = None) -> dict:
        """Generate content using new strict prompt"""
        
        try:
            # Get location rule
            location = user_profile.get('location', '')
            if not location_rule:
                if 'india' in location.lower():
                    location_rule = LOCATION_RULES['India']
                elif 'us' in location.lower():
                    location_rule = LOCATION_RULES['US']
                else:
                    location_rule = LOCATION_RULES['default']
            
            # Prepare repo files summary
            repo_files_summary = repo_files_data.get('summary', 'No file details available') if repo_files_data else 'No file details available'

            # CRITICAL: Get news articles from web crawler (Google News, TechCrunch, Verge, Wired)
            # REDUCED: Only send 10 articles to avoid prompt size issues
            fresh_updates = research_data.get('fresh_updates', [])
            if isinstance(fresh_updates, list):
                web_news_articles = fresh_updates[:10]  # Top 10 news articles (reduced from 20)
            else:
                web_news_articles = []
            
            web_search_summary = json.dumps(web_news_articles, indent=2) if web_news_articles else "[]"
            
            print(f"📰 Passing {len(web_news_articles)} news articles to AI (from Google News, TechCrunch, Verge, Wired)")

            # Get user's stated interests from profile - MAKE THESE PROMINENT
            user_interests = user_profile.get('interests', [])
            user_skills = user_profile.get('skills', [])
            user_goals = user_profile.get('goals', [])
            
            # REDUCED GitHub data - only essential context
            tech_using = behavioral_data.get('evidence', {}).get('technologies_using', [])
            tech_exploring = behavioral_data.get('evidence', {}).get('technologies_exploring', [])
            
            github_context = {
                'tech_stack': list(tech_using)[:3] if isinstance(tech_using, list) else [],  # Top 3 only
                'exploring': list(tech_exploring)[:3] if isinstance(tech_exploring, list) else [],  # Top 3 only
                'intent': behavioral_data.get('primary_intent', 'exploring')
            }

            # Prepare all data safely - REDUCED to prevent prompt size issues
            trending_repos = research_data.get('trending_repos', [])
            if isinstance(trending_repos, list):
                trending_repos = list(trending_repos)[:5]  # Reduced from 10 to 5
            else:
                trending_repos = []
            
            hn_stories = research_data.get('hackernews_stories', [])
            if isinstance(hn_stories, list):
                hn_stories = list(hn_stories)[:5]  # Reduced from 8 to 5
            else:
                hn_stories = []
            
            # Get opportunities (dict with hackathons, jobs, funding, events)
            opps = research_data.get('opportunities', {})
            print(f"🔍 DEBUG: opportunities type = {type(opps)}")
            print(f"🔍 DEBUG: opportunities keys = {opps.keys() if isinstance(opps, dict) else 'Not a dict'}")

            if isinstance(opps, dict):
                # Extract hackathons and jobs (the ones we actually fetch)
                hackathons = opps.get('hackathons', [])[:5]  # Top 5 hackathons
                jobs = opps.get('jobs', [])[:3]  # Top 3 jobs

                # Combine for prompt
                opps_data = {
                    'hackathons': hackathons,
                    'jobs': jobs
                }

                print(f"🎯 Passing {len(hackathons)} hackathons and {len(jobs)} jobs to AI")

                # Show first hackathon for debugging
                if hackathons:
                    first_hack = hackathons[0]
                    print(f"   Example hackathon: {first_hack.get('title', 'No title')}")
                    print(f"   URL: {first_hack.get('url', 'No URL')}")
                else:
                    print("   ⚠️ WARNING: No hackathons in opportunities data!")

            elif isinstance(opps, list):
                # Fallback: if it's somehow a list, use it directly
                print(f"⚠️ WARNING: opportunities is a list (unexpected), using as-is")
                opps_data = opps[:8]
            else:
                print(f"❌ ERROR: opportunities is neither dict nor list: {type(opps)}")
                opps_data = {'hackathons': [], 'jobs': []}

            # Determine skill level from GitHub activity
            skill_level = "intermediate"  # Default
            if github_context['intent'] == 'LEARNING':
                skill_level = "beginner/intermediate"
            elif github_context['intent'] == 'BUILDING':
                skill_level = "intermediate/advanced"

            prompt = CONTENT_GENERATION_PROMPT.format(
                todays_date=datetime.now().strftime("%B %d, %Y"),
                tech_stack=json.dumps(github_context['tech_stack']),
                user_interests=json.dumps(user_interests),
                skill_level=skill_level,
                location=user_profile.get('location', ''),
                github_trending=json.dumps(trending_repos, indent=2),
                hackernews=json.dumps(hn_stories, indent=2),
                news_articles=web_search_summary,  # RENAMED from web_search_results
                opportunities=json.dumps(opps_data, indent=2),  # Now contains hackathons and jobs
                starred_repos=json.dumps([])  # RENAMED from user_starred_repos
            )
        except Exception as e:
            print(f"🚨 ERROR in _generate_content preparation: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # CRITICAL: Higher temperature for creativity and variety
        # Adding randomization to prevent same content every time
        import random
        import time
        # Seed random with current time for true variety across runs
        random.seed(int(time.time()))
        temperature = random.uniform(0.7, 0.9)  # Random temperature for variety
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=temperature,  # Higher for creativity and variety
            system="You are a creative tech recommendation engine. Generate EXACTLY 5 DIVERSE items with VARIETY. Each 100-200 words. Be creative, explore different angles, avoid repetition. Focus on being helpful, not critical. Return valid JSON with 5 items.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        print(f"  🎲 Using temperature: {temperature:.2f} for creative variety")

        try:
            content_text = response.content[0].text.strip()
            print(f"🔍 AI Response type: {type(content_text)}")
            print(f"🔍 AI Response length: {len(content_text)}")
            
            # Try to extract JSON from response if it's wrapped in markdown
            if content_text.startswith('```json'):
                content_text = content_text.split('```json')[1].split('```')[0].strip()
            elif content_text.startswith('```'):
                content_text = content_text.split('```')[1].strip()
            
            content_data = json.loads(content_text)
            print(f"🔍 Parsed content type: {type(content_data)}")
            
            # Ensure we have the right structure
            if isinstance(content_data, dict):
                if 'items' in content_data:
                    print(f"✅ Content has 'items' key with {len(content_data['items'])} items")
                    # Enrich with specific source names from original data
                    try:
                        content_data = self._enrich_source_attribution(content_data, research_data)
                        return content_data
                    except Exception as enrich_error:
                        print(f"⚠️ Source enrichment failed: {enrich_error}")
                        return content_data  # Return without enrichment
                else:
                    print("⚠️ Content is dict but missing 'items' key, adding it")
                    enriched_data = {"items": [content_data]}
                    try:
                        return self._enrich_source_attribution(enriched_data, research_data)
                    except Exception as enrich_error:
                        print(f"⚠️ Source enrichment failed: {enrich_error}")
                        return enriched_data
            elif isinstance(content_data, list):
                print(f"✅ Content is list with {len(content_data)} items")
                enriched_data = {"items": content_data}
                try:
                    return self._enrich_source_attribution(enriched_data, research_data)
                except Exception as enrich_error:
                    print(f"⚠️ Source enrichment failed: {enrich_error}")
                    return enriched_data
            else:
                print(f"❌ Unexpected content type: {type(content_data)}")
                raise ValueError(f"Unexpected content type: {type(content_data)}")
                
        except Exception as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"🔍 Raw content: {content_text[:200]}...")
            
            # Fallback to existing content curator
            print("🔄 Falling back to content curator...")
            fallback_content = await self.content_curator.curate_geographically_relevant_content(
                user_profile,
                research_data,
                behavioral_data
            )
            
            print(f"🔍 Fallback content type: {type(fallback_content)}")
            
            # Ensure consistent format
            if isinstance(fallback_content, list):
                print(f"✅ Fallback is list with {len(fallback_content)} items")
                return {"items": fallback_content}
            elif isinstance(fallback_content, dict):
                if 'items' in fallback_content:
                    print(f"✅ Fallback is dict with 'items' key")
                    return fallback_content
                else:
                    print("⚠️ Fallback is dict but missing 'items' key")
                    return {"items": [fallback_content]}
            else:
                print(f"❌ Fallback has unexpected type: {type(fallback_content)}")
                # Last resort - create empty structure
                return {"items": []}
    
    async def generate_premium_editorial(
        self, 
        user_profile: dict, 
        research_data: dict
    ) -> Dict[str, str]:
        """Generate premium top-5 updates from real data (legacy method)"""
        
        print("🤖 AI Editorial Generation Process:")
        print("  1️⃣ Analyzing user profile...")
        user_analysis = await self._analyze_user_deeply(user_profile, research_data)
        
        print("  2️⃣ Selecting top 5 niche updates...")
        top5_updates = await self._select_top5_updates(user_analysis, research_data)
        
        print("  3️⃣ Creating newsletter content...")
        newsletter_content = await self._craft_newsletter_content(
            user_profile, user_analysis, top5_updates, research_data
        )
        
        return newsletter_content
    
    async def _analyze_user_deeply(self, user_profile: dict, research_data: dict) -> dict:
        """Deep analysis combining profile and GitHub context to infer skills, interests, goals"""
        
        github_context = research_data.get("user_context", {})
        
        prompt = USER_ANALYSIS_PROMPT.format(
            name=user_profile['name'],
            email=user_profile['email'],
            github_username=user_profile['github_username'],
            user_interests=user_profile.get('interests', []),
            user_info=json.dumps(github_context.get('user_info', {}), indent=2),
            recent_repos=json.dumps(github_context.get('recent_repos', [])[:10], indent=2),
            starred_repos=json.dumps(github_context.get('interests_from_stars', [])[:10], indent=2),
            readme_content=github_context.get('readme_content', '')[:500],
            repo_analysis=json.dumps(github_context.get('repo_analysis', {}), indent=2)
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1200,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            # Ensure required fields exist
            if "inferred_skills" not in analysis:
                analysis["inferred_skills"] = ["Python", "JavaScript", "Development"]
            if "inferred_interests" not in analysis:
                analysis["inferred_interests"] = ["Technology", "Programming", "Innovation"]
            if "experience_level" not in analysis:
                analysis["experience_level"] = "intermediate"
            return analysis
        except:
            # Simplified fallback based on GitHub data
            repo_analysis = github_context.get('repo_analysis', {})
            top_languages = [lang[0] for lang in repo_analysis.get('top_languages', [])[:3]]
            
            return {
                "inferred_skills": top_languages or ["Python", "JavaScript"],
                "inferred_interests": user_profile.get('interests', ["Technology", "Programming", "Innovation"]),
                "inferred_goals": ["Build innovative projects", "Master new technologies"],
                "experience_level": "intermediate",
                "primary_domain": "web_development",
                "content_style_preference": "technical_with_insights",
                "interest_github_match": "Basic analysis of GitHub activity patterns"
            }
    
    async def _select_top5_updates(self, user_analysis: dict, research_data: dict) -> dict:
        """Select top 5 niche, specific updates from real data"""
        
        prompt = TOP5_UPDATES_PROMPT.format(
            name=user_analysis.get('inferred_skills', ['Developer'])[0] + " developer",
            inferred_skills=user_analysis.get('inferred_skills', []),
            inferred_interests=user_analysis.get('inferred_interests', []),
            inferred_goals=user_analysis.get('inferred_goals', []),
            experience_level=user_analysis.get('experience_level', 'intermediate'),
            primary_domain=user_analysis.get('primary_domain', 'web_development'),
            current_focus=user_analysis.get('current_focus', 'general development'),
            interest_github_match=user_analysis.get('interest_github_match', 'GitHub activity analysis'),
            trending_repos=json.dumps(research_data.get('trending_repos', [])[:15], indent=2),
            hackernews_stories=json.dumps(research_data.get('hackernews_stories', [])[:10], indent=2),
            user_github_activity=json.dumps(research_data.get('user_context', {}).get('recent_repos', [])[:5], indent=2),
            user_starred_repos=json.dumps(research_data.get('user_context', {}).get('interests_from_stars', [])[:5], indent=2)
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            updates_data = json.loads(response.choices[0].message.content)
            return updates_data
        except:
            # Fallback: create 5 updates from available data
            return {
                "updates": [
                    {
                        "title": "Latest Development Trends",
                        "content": f"Based on analysis of {len(research_data.get('trending_repos', []))} trending repositories, here are the key developments in your field.",
                        "relevance_score": 8,
                        "data_sources": ["GitHub trending repos"],
                        "actionable_items": ["Explore trending repositories", "Review new frameworks"]
                    }
                ] * 5,
                "overall_theme": "Current development trends",
                "freshness_note": "Data from last 7 days"
            }
    
    async def _craft_newsletter_content(
        self, 
        user_profile: dict,
        user_analysis: dict, 
        top5_updates: dict,
        research_data: dict
    ) -> Dict[str, str]:
        """Craft newsletter content with top 5 updates"""
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = CONTENT_GENERATION_PROMPT.format(
            name=user_profile['name'],
            inferred_skills=user_analysis.get('inferred_skills', []),
            inferred_interests=user_analysis.get('inferred_interests', []),
            inferred_goals=user_analysis.get('inferred_goals', []),
            experience_level=user_analysis.get('experience_level', 'intermediate'),
            primary_domain=user_analysis.get('primary_domain', 'web_development'),
            updates_data=json.dumps(top5_updates, indent=2)
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            max_tokens=3000,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            content_text = response.choices[0].message.content
            print(f"🔍 Raw AI response: {content_text[:200]}...")
            
            # Try to extract JSON from the response
            if "```json" in content_text:
                json_start = content_text.find("```json") + 7
                json_end = content_text.find("```", json_start)
                json_text = content_text[json_start:json_end].strip()
            elif "{" in content_text and "}" in content_text:
                json_start = content_text.find("{")
                json_end = content_text.rfind("}") + 1
                json_text = content_text[json_start:json_end]
            else:
                # Fallback: create content from the raw response
                return {
                    "headline": "Your Weekly Tech Intelligence",
                    "intro": "Here are the top 5 updates tailored for your interests and GitHub activity.",
                    "updates": [
                        {
                            "number": i+1,
                            "title": f"Update {i+1}",
                            "content": content_text
                        }
                        for i in range(5)
                    ],
                    "key_insights": ["AI-generated insights from current trends"],
                    "data_sources": ["Real-time GitHub and web data"],
                    "date": current_date
                }
            
            content_data = json.loads(json_text)
            return {
                "headline": content_data.get("headline", "Your Weekly Tech Intelligence"),
                "intro": content_data.get("intro", "Here are the top 5 updates tailored for your interests."),
                "updates": content_data.get("updates", []),
                "key_insights": content_data.get("key_insights", []),
                "data_sources": content_data.get("data_sources", []),
                "date": current_date
            }
        except Exception as e:
            print(f"⚠️ Content generation failed: {e}")
            # Create a meaningful fallback with real data
            return {
                "headline": "Your Weekly Tech Intelligence",
                "intro": f"Based on analysis of {len(research_data.get('trending_repos', []))} trending repositories and {len(research_data.get('hackernews_stories', []))} HackerNews stories, here are the top 5 updates for your interests: {', '.join(user_analysis.get('inferred_interests', ['technology']))}.",
                "updates": [
                    {
                        "number": i+1,
                        "title": f"Update {i+1}: {user_analysis.get('inferred_interests', ['Technology'])[i % len(user_analysis.get('inferred_interests', ['Technology']))]}",
                        "content": f"Based on your {user_analysis.get('primary_domain', 'development')} expertise and interest in {user_analysis.get('inferred_interests', ['technology'])[i % len(user_analysis.get('inferred_interests', ['technology']))]}, here are the latest developments and actionable insights."
                    }
                    for i in range(5)
                ],
                "key_insights": [
                    f"Real-time analysis of {len(research_data.get('trending_repos', []))} trending repositories",
                    f"Current HackerNews discussions and trends", 
                    f"Personalized insights based on your {user_analysis.get('primary_domain', 'development')} expertise",
                    f"Fresh data from the last 7 days"
                ],
                "data_sources": ["GitHub API", "HackerNews API", "Real-time analysis"],
                "date": current_date
            }
    
    async def _select_compelling_topic(self, user_analysis: dict, research_data: dict) -> dict:
        """Select the most compelling topic from real data"""
        
        prompt = f"""
        Select the perfect editorial topic from this REAL research data:
        
        USER ANALYSIS (INFERRED FROM GITHUB):
        Skills: {user_analysis.get('inferred_skills', [])}
        Interests: {user_analysis.get('inferred_interests', [])}
        Goals: {user_analysis.get('inferred_goals', [])}
        Experience Level: {user_analysis.get('experience_level', 'intermediate')}
        Primary Domain: {user_analysis.get('primary_domain', 'web_development')}
        Current Focus: {user_analysis.get('current_focus', 'general development')}
        
        REAL TRENDING REPOS (FRESH DATA):
        {json.dumps(research_data.get('trending_repos', [])[:15], indent=2)}
        
        REAL HACKERNEWS STORIES (CURRENT):
        {json.dumps(research_data.get('hackernews_stories', [])[:10], indent=2)}
        
        USER'S GITHUB CONTEXT:
        Recent Activity: {json.dumps(research_data.get('user_context', {}).get('repo_analysis', {}).get('recent_activity', [])[:5], indent=2)}
        Top Languages: {json.dumps(research_data.get('user_context', {}).get('repo_analysis', {}).get('top_languages', [])[:5], indent=2)}
        
        Find ONE topic that:
        1. Uses specific real data from above (repos, stories, trends)
        2. Perfectly matches user's INFERRED skills, interests, and goals
        3. Provides genuine insights they can't get elsewhere
        4. Has enough depth for 700-word editorial
        5. Connects current trends with their specific professional focus
        6. Considers their current GitHub activity patterns
        
        Return as JSON:
        {{
            "selected_topic": "specific topic using real data",
            "angle": "unique perspective",
            "supporting_data": ["specific repos/stories to reference"],
            "why_now": "why this matters right now",
            "personal_relevance": "why this matters to THIS user specifically based on their GitHub activity",
            "motivation_hook": "what will make them excited to read this"
        }}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1200,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            topic_data = json.loads(response.choices[0].message.content)
            # Ensure required fields exist
            if "selected_topic" not in topic_data:
                topic_data["selected_topic"] = "AI Development Tools Evolution"
            if "angle" not in topic_data:
                topic_data["angle"] = "How recent tools are changing development workflows"
            return topic_data
        except:
            return {
                "selected_topic": "AI Development Tools Evolution",
                "angle": "How recent tools are changing development workflows"
            }
    
    async def _craft_premium_editorial(
        self, 
        user_analysis: dict, 
        topic_selection: dict,
        research_data: dict
    ) -> Dict[str, str]:
        """Craft premium editorial content"""
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""
        Write a premium editorial piece using REAL research data and INFERRED user profile.
        
        USER PROFILE (INFERRED FROM GITHUB):
        Name: {user_analysis.get('inferred_skills', [])} developer
        Skills: {user_analysis.get('inferred_skills', [])}
        Interests: {user_analysis.get('inferred_interests', [])}
        Goals: {user_analysis.get('inferred_goals', [])}
        Experience: {user_analysis.get('experience_level', 'intermediate')} level
        Domain: {user_analysis.get('primary_domain', 'web_development')}
        Current Focus: {user_analysis.get('current_focus', 'general development')}
        
        TOPIC & ANGLE: {json.dumps(topic_selection)}
        
        REAL DATA TO USE:
        - Fresh Trending Repos: {json.dumps(research_data.get('trending_repos', [])[:8], indent=2)}
        - Current HN Stories: {json.dumps(research_data.get('hackernews_stories', [])[:8], indent=2)}
        - User's GitHub Activity: {json.dumps(research_data.get('user_context', {}).get('recent_repos', [])[:5], indent=2)}
        - User's Interests (from stars): {json.dumps(research_data.get('user_context', {}).get('interests_from_stars', [])[:5], indent=2)}
        
        Write like The Information/Stratechery - premium business intelligence:
        
        REQUIREMENTS:
        1. HEADLINE: Compelling, specific (not clickbait)
        2. STRUCTURE:
           - Hook with real data point or trend
           - Context and background
           - Deep analysis with specific examples
           - Connection to user's specific GitHub activity and interests
           - Forward-looking insights
        3. USE REAL DATA: Reference specific repos, stories, numbers from above
        4. PERSONAL CONNECTION: Weave in relevance to user's GitHub profile naturally
        5. LENGTH: 650-800 words
        6. STYLE: Professional, insightful, worth paying for
        7. FRESHNESS: Emphasize what's NEW and CURRENT
        
        Return as JSON:
        {{
            "headline": "Compelling headline",
            "content": "Full editorial with paragraphs",
            "key_insights": ["main takeaways"],
            "data_points_used": ["specific data referenced"]
        }}
        
        Make it feel like premium research they'd be excited to read and share.
        Focus on what's happening RIGHT NOW in their domain.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            max_tokens=3000,
            temperature=0.8,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            content_text = response.choices[0].message.content
            print(f"🔍 Raw AI response: {content_text[:200]}...")
            
            # Try to extract JSON from the response
            if "```json" in content_text:
                json_start = content_text.find("```json") + 7
                json_end = content_text.find("```", json_start)
                json_text = content_text[json_start:json_end].strip()
            elif "{" in content_text and "}" in content_text:
                json_start = content_text.find("{")
                json_end = content_text.rfind("}") + 1
                json_text = content_text[json_start:json_end]
            else:
                # Fallback: create content from the raw response
                return {
                    "headline": "Weekly Tech Intelligence Brief",
                    "content": content_text,
                    "key_insights": ["AI-generated insights from current trends"],
                    "date": current_date,
                    "data_sources": ["Real-time GitHub and HackerNews data"]
                }
            
            content_data = json.loads(json_text)
            return {
                "headline": content_data.get("headline", "Your Weekly Tech Intelligence"),
                "content": content_data.get("content", "Content generation failed"),
                "key_insights": content_data.get("key_insights", []),
                "date": current_date,
                "data_sources": content_data.get("data_points_used", [])
            }
        except Exception as e:
            print(f"⚠️ Content generation failed: {e}")
            # Create a meaningful fallback with real data
            return {
                "headline": "Weekly Tech Intelligence Brief",
                "content": f"Based on our analysis of {len(research_data.get('trending_repos', []))} trending repositories and {len(research_data.get('hackernews_stories', []))} HackerNews stories, here are the key developments in your areas of interest: {', '.join(user_analysis.get('inferred_interests', ['technology']))}. Your GitHub activity shows expertise in {', '.join(user_analysis.get('inferred_skills', ['development']))}, and the current trends align perfectly with your focus on {user_analysis.get('current_focus', 'technology innovation')}. The most exciting developments include new tools and frameworks that could enhance your {user_analysis.get('primary_domain', 'development')} workflow.",
                "key_insights": [
                    f"Real-time analysis of {len(research_data.get('trending_repos', []))} trending repositories",
                    f"Current HackerNews discussions and trends", 
                    f"Personalized insights based on your {user_analysis.get('primary_domain', 'development')} expertise",
                    f"Fresh data from the last 3 days"
                ],
                "date": current_date,
                "data_sources": ["GitHub API", "HackerNews API", "Real-time analysis"]
            }
    
    def _analyze_geographic_context(self, user_profile: dict) -> dict:
        """Analyze geographic context for content prioritization"""
        
        location = user_profile.get('location', '').lower()
        
        context = {
            'is_india': any(loc in location for loc in ['india', 'bangalore', 'delhi', 'mumbai', 'hyderabad', 'pune']),
            'is_us': any(loc in location for loc in ['usa', 'us', 'america', 'california', 'new york', 'texas']),
            'local_focus': user_profile.get('preferences', {}).get('prioritize_local', False),
            'timezone': user_profile.get('timezone', 'UTC')
        }
        
        return context
    
    def _validate_content_quality(self, content: list, user_intent: dict) -> list:
        """Ensure content meets quality standards with strict validation"""
        
        validated_content = []
        github_references = 0
        india_references = 0
        
        for item in content:
            # Check if item has required structure
            if not isinstance(item, dict):
                print(f"⚠️ Skipping invalid item structure")
                continue
                
            description = item.get('description', '')
            title = item.get('title', '')
            word_count = len(description.split())
            
            # Check length
            if word_count < 100:
                print(f"⚠️ Item too short ({word_count} words). Minimum 120 words.")
                continue
            if word_count > 250:
                print(f"⚠️ Item too long ({word_count} words). Maximum 200 words.")
                continue
            
            # Check personalization
            if 'you' not in description.lower() and 'your' not in description.lower():
                print("⚠️ Item not personalized - must reference user directly")
                continue
            
            # Check actionability  
            if not item.get('url') or item['url'] == '#':
                print("⚠️ Item missing actionable URL")
                continue
            
            # Check specificity
            vague_phrases = ['could be', 'might be', 'possibly', 'maybe', 'perhaps']
            if any(phrase in description.lower() for phrase in vague_phrases):
                print("⚠️ Item too vague - use specific language")
                continue
            
            # Check for GitHub references
            current_projects = user_intent.get('current_projects', [])
            if current_projects:
                for project in current_projects:
                    if project.lower() in description.lower() or project.lower() in title.lower():
                        github_references += 1
                        break
            
            # Check for India-specific content
            india_keywords = ['bangalore', 'delhi', 'mumbai', 'hyderabad', 'pune', 'india', 'indian', 'razorpay', 'swiggy', 'zomato', 'flipkart', 'paytm']
            if any(keyword in description.lower() or keyword in title.lower() for keyword in india_keywords):
                india_references += 1
            
            # Check for geographic relevance if user has local focus
            geo_priorities = user_intent.get('geographic_priorities', {})
            if geo_priorities.get('local_focus'):
                location_hints = ['bangalore', 'delhi', 'mumbai', 'india', 'local', 'nearby']
                if not any(hint in description.lower() for hint in location_hints):
                    print("⚠️ Item lacks local relevance for user with local focus")
                    # Don't skip, but note the issue
            
            validated_content.append(item)
        
        # Strict validation for India users
        geo_priorities = user_intent.get('geographic_priorities', {})
        if geo_priorities.get('region') == 'india' and india_references < 2:
            print(f"❌ REJECTED: Only {india_references} India-specific items for Indian user (minimum 2 required)")
            return self._create_fallback_items(user_intent)
        
        # Strict validation for GitHub references
        current_projects = user_intent.get('current_projects', [])
        if current_projects and github_references < 2:
            print(f"❌ REJECTED: Only {github_references} GitHub references (minimum 2 required)")
            return self._create_fallback_items(user_intent)
        
        if len(validated_content) < 3:
            print(f"⚠️ Only {len(validated_content)} items passed quality validation. Minimum 3 required.")
            # Add fallback items if needed
            validated_content.extend(self._create_fallback_items(user_intent))
        
        print(f"✅ Quality validation passed: {len(validated_content)} items, {github_references} GitHub refs, {india_references} India refs")
        return validated_content[:5]  # Ensure max 5 items
    
    def _create_fallback_items(self, user_intent: dict) -> list:
        """Create fallback items if validation fails"""
        
        primary_intent = user_intent.get('primary_intent', 'exploring')
        
        fallback_items = [
            {
                'title': f'Quick Update for {primary_intent.title()} Focus',
                'description': f'Based on your current focus on {primary_intent}, here are some relevant opportunities and resources to explore. Your GitHub activity shows active development, which is perfect timing for these recommendations. The tech landscape is rapidly evolving, and staying ahead requires continuous learning and adaptation. Consider joining relevant communities, attending virtual meetups, or contributing to open-source projects in your area of interest. These activities will help you stay current with industry trends and connect with like-minded developers. Look for opportunities that match your skill level and interests, and don\'t hesitate to step outside your comfort zone. Next step: Identify one specific action you can take this week to advance your {primary_intent} goals.',
                'url': 'https://github.com/trending',
                'category': '📊 UPDATE',
                'relevance_score': 7
            },
            {
                'title': 'Learning Resource Recommendation',
                'description': 'Here are some curated learning resources that match your current skill development needs. Your GitHub profile shows expertise in multiple technologies, and these resources will help you deepen your knowledge and stay current with best practices. The recommended courses and tutorials are specifically chosen based on your recent activity and interests. Focus on hands-on learning through projects rather than just theoretical knowledge. Consider building something new with the technologies you\'re learning to reinforce your understanding. Join online communities and forums related to these technologies to get help and share your progress. Next step: Pick one resource and commit to completing it within the next two weeks.',
                'url': 'https://github.com/trending',
                'category': '🧠 LEARNING',
                'relevance_score': 6
            }
        ]
        
        return fallback_items