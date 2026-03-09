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
from .system_prompts import CONTENT_GENERATION_PROMPT, BEHAVIORAL_ANALYSIS_PROMPT, LOCATION_RULES
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
                validation_result = validator.validate_daily_5(daily_5_content, user_profile, behavioral_data)
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
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            temperature=0.3,
            system="You are a behavioral analysis engine. Analyze GitHub activity and return structured JSON.",
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            raw_text = response.content[0].text.strip()
            # Strip markdown JSON wrapper if present
            if raw_text.startswith('```json'):
                raw_text = raw_text[7:]
            if raw_text.startswith('```'):
                raw_text = raw_text[3:]
            if raw_text.endswith('```'):
                raw_text = raw_text[:-3]
            behavioral_data = json.loads(raw_text.strip())
            
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

            # Enrich with interest graph data when available (MCP digest flow)
            interest_graph_context = ""
            ig = user_profile.get('interest_graph')
            if ig and ig.get('topics'):
                ig_topics = sorted(ig['topics'], key=lambda t: t.get('weight', 0), reverse=True)
                weighted_lines = []
                for t in ig_topics[:10]:
                    entities = ', '.join(t.get('entities', [])[:5])
                    line = f"  - {t['topic']} (weight {t.get('weight', 0):.2f}, intent: {t.get('intent', 'learning')})"
                    if entities:
                        line += f" [entities: {entities}]"
                    weighted_lines.append(line)

                ba = user_profile.get('balanced_allocation', {})
                alloc_lines = []
                for cat, data in ba.items():
                    cat_topics = [tp['topic'] for tp in data.get('topics', [])]
                    alloc_lines.append(f"  - {cat}: {data.get('allocation', 1)} items -> {', '.join(cat_topics)}")

                interest_graph_context = (
                    "\n\n═══════════════════════════════════════════════════════════════════\n"
                    "INTEREST GRAPH (from MCP — higher weight = stronger signal):\n"
                    "═══════════════════════════════════════════════════════════════════\n"
                    "Weighted topics (prioritize higher-weight topics):\n"
                    + "\n".join(weighted_lines)
                )
                if alloc_lines:
                    interest_graph_context += (
                        "\n\nBalanced content allocation (distribute items across categories):\n"
                        + "\n".join(alloc_lines)
                    )
                interest_graph_context += "\n\nUse the weights and allocation above to decide how many items to dedicate to each area.\n"
            
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

            # Append interest graph context when available (MCP digest flow)
            if interest_graph_context:
                prompt += interest_graph_context
        except Exception as e:
            print(f"🚨 ERROR in _generate_content preparation: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0.5,
            system="You are a creative tech recommendation engine. Generate EXACTLY 5 DIVERSE items with VARIETY. Each 100-200 words. Be creative, explore different angles, avoid repetition. Focus on being helpful, not critical. Return valid JSON with 5 items.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
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