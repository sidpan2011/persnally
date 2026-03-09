"""
Email Sender - Premium Editorial Email Delivery
"""
from jinja2 import Template, Environment, FileSystemLoader
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .image_fetcher import ImageFetcher
from .content_formatter import ContentFormatter
import re

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

class PremiumEmailSender:
    def __init__(self, config, resend_client):
        self.config = config
        self.resend_client = resend_client
        self.image_fetcher = ImageFetcher()
        self.content_formatter = ContentFormatter()
    
    async def send_daily_5_newsletter(self, user_data: dict, daily_5_content: Dict[str, Any]):
        """Send Daily 5 newsletter with behavioral intelligence"""

        # CRITICAL: Log comprehensive scores before sending
        print("\n" + "="*80)
        print("📊 RECOMMENDATION SCORING ANALYSIS (PRE-SEND)")
        print("="*80)

        self._log_comprehensive_scores(user_data, daily_5_content)

        # Skip image processing since we removed images from template

        # Generate Daily 5 email content
        html_content = self._generate_daily_5_email_html(user_data, daily_5_content)

        # Use the subject line from behavioral analysis
        subject = daily_5_content['subject_line']

        # Send via MCP orchestrator
        success = await self.resend_client.send_email_via_mcp(
            user_data['email'],
            subject,
            html_content
        )

        if success:
            print(f"✅ Daily 5 sent to {user_data['name']}")
        else:
            print(f"❌ Failed to send Daily 5 to {user_data['name']}")

        return success
    
    async def send_editorial_newsletter(self, user_data: dict, editorial_content: Dict[str, str]):
        """Send premium editorial newsletter (legacy method)"""
        
        # Generate premium email content
        html_content = self._generate_premium_email_html(user_data, editorial_content)
        
        # Create engaging subject line
        subject = self._create_premium_subject_line(user_data, editorial_content)
        
        # Send via MCP orchestrator
        success = await self.resend_client.send_email_via_mcp(
            user_data['email'],
            subject,
            html_content
        )
        
        if success:
            print(f"✅ Premium editorial sent to {user_data['name']}")
        else:
            print(f"❌ Failed to send editorial to {user_data['name']}")
        
        return success
    
    def _create_premium_subject_line(self, user_data: dict, editorial_content: Dict[str, str]) -> str:
        """Create simple subject line - no personalization"""

        current_date = datetime.now()
        date = current_date.strftime("%A, %B %d, %Y")

        # Simple, consistent subject line
        subject = f"Daily update by persnally: {date}"

        return subject
    
    def _generate_daily_5_email_html(self, user_data: dict, daily_5_content: Dict[str, Any]) -> str:
        """Generate Daily 5 HTML email with visual formatting"""

        with open(TEMPLATE_DIR / 'email.html', 'r') as f:
            template_content = f.read()

        # Format items with visual highlighting
        formatted_items = []

        # Defensive: Get user_intent safely
        user_intent = daily_5_content.get('user_intent', {})
        if isinstance(user_intent, dict):
            active_repos = user_intent.get('evidence', {}).get('active_repos', [])
        else:
            # user_intent is not a dict (might be a string), use empty list
            active_repos = []

        for item in daily_5_content.get('items', []):
            formatted_item = item.copy()

            # Apply visual formatting to content
            content = item.get('content', '')
            formatted_content = self.content_formatter.format_content(content, active_repos)

            # Add source attribution if available
            source = item.get('source', '')
            source_url = item.get('source_url', '')
            if source:
                formatted_content = self.content_formatter.add_source_attribution(
                    formatted_content,
                    source,
                    source_url
                )

            formatted_item['content'] = formatted_content
            formatted_items.append(formatted_item)

        # Create Jinja2 environment with custom markdown filter
        env = Environment()
        env.filters['markdown_to_html'] = self._markdown_to_html
        template = env.from_string(template_content)

        return template.render(
            user_name=user_data['name'],
            headline=daily_5_content['headline'],
            personalization_note=daily_5_content.get('personalization_note', ''),
            items=formatted_items,  # Use formatted items
            key_insights=daily_5_content.get('key_insights', []),
            date=daily_5_content['date']
        )
    
    def _generate_premium_email_html(self, user_data: dict, editorial_content: Dict[str, str]) -> str:
        """Generate premium HTML email (legacy method)"""
        
        with open(TEMPLATE_DIR / 'email.html', 'r') as f:
            template_content = f.read()

        template = Template(template_content)
        
        return template.render(
            user_name=user_data['name'],
            headline=editorial_content['headline'],
            intro=editorial_content.get('intro', ''),
            updates=editorial_content.get('updates', []),
            content=self._format_content_for_email(editorial_content.get('content', '')),
            key_insights=editorial_content.get('key_insights', []),
            date=editorial_content['date']
        )
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to HTML for email rendering"""
        if not markdown_text:
            return ""
        
        # Convert markdown to HTML
        html = markdown_text
        
        # Convert markdown links [text](url) to HTML <a href="url">text</a>
        # This must be done FIRST before other conversions to preserve URLs
        html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #2563eb; text-decoration: none; font-weight: normal;">\1</a>', html)
        
        # Convert **bold** to <strong> with simple styling
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Convert *italic* to <em>
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Convert line breaks to <br> and paragraphs
        html = html.replace('\n\n', '</p><p>')
        html = html.replace('\n', '<br>')
        
        # Wrap in paragraph tags if not already wrapped
        if not html.startswith('<p>'):
            html = f'<p>{html}</p>'
        
        # Convert bullet points (- item) to <ul><li>
        lines = html.split('<br>')
        converted_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                if not in_list:
                    converted_lines.append('<ul>')
                    in_list = True
                converted_lines.append(f'<li>{line[2:]}</li>')
            else:
                if in_list:
                    converted_lines.append('</ul>')
                    in_list = False
                converted_lines.append(line)
        
        if in_list:
            converted_lines.append('</ul>')
        
        html = '<br>'.join(converted_lines)
        
        # Convert numbered lists (1. item) to <ol><li>
        html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        if '<li>' in html and '<ul>' not in html:
            html = html.replace('<li>', '<ol><li>', 1)
            html = html.replace('</li>', '</li></ol>', 1)
        
        return html
    
    def _format_content_for_email(self, content: str) -> str:
        """Format content for email HTML"""
        # Split into paragraphs and wrap in <p> tags
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            if para.strip():
                # Handle basic formatting
                formatted_para = para.strip()
                
                # Add paragraph tags
                formatted_paragraphs.append(f"<p>{formatted_para}</p>")
        
        return '\n'.join(formatted_paragraphs)
    
    def _log_comprehensive_scores(self, user_data: dict, daily_5_content: Dict[str, Any]):
        """
        Log comprehensive scoring analysis to understand recommendation quality.
        This helps identify if we're properly considering:
        1. User profile (interests, goals, preferences)
        2. GitHub analysis (technicality, skills, activity)
        3. Content relevance and quality
        """

        print("\n┌─ USER PROFILE ANALYSIS")
        print("│")

        # User stated interests (SHOULD BE PRIMARY FACTOR)
        interests = user_data.get('interests', [])
        print(f"│  User Interests: {interests}")
        print(f"│  Experience Level: {user_data.get('experience_level', 'N/A')}")
        print(f"│  Location: {user_data.get('location', 'N/A')}")

        preferences = user_data.get('preferences', {})
        print(f"│  Content Style: {preferences.get('content_style', 'N/A')}")
        print(f"│  Opportunity Types: {preferences.get('opportunity_types', [])}")
        print(f"│  Prioritize Local: {preferences.get('prioritize_local', False)}")

        # GitHub analysis (SECONDARY FACTOR - for context only)
        user_intent = daily_5_content.get('user_intent', {})
        if isinstance(user_intent, dict):
            print("\n├─ GITHUB ANALYSIS (Context Only)")
            print("│")
            print(f"│  Primary Intent: {user_intent.get('primary_intent', 'N/A')}")
            print(f"│  Confidence: {user_intent.get('confidence_score', 'N/A')}")

            evidence = user_intent.get('evidence', {})
            if evidence:
                active_repos = evidence.get('active_repos', [])
                print(f"│  Active Repos: {active_repos[:3]}")
                print(f"│  Technologies Using: {evidence.get('technologies_using', [])[:3]}")
                print(f"│  Technologies Exploring: {evidence.get('technologies_exploring', [])[:3]}")

        # Recommendation scoring
        print("\n├─ RECOMMENDATION SCORES")
        print("│")

        items = daily_5_content.get('items', [])
        total_score = 0
        user_interest_matches = 0
        github_relevance = 0

        for i, item in enumerate(items, 1):
            print(f"│")
            print(f"│  [{i}] {item.get('title', 'Untitled')[:60]}")
            print(f"│      Category: {item.get('category', 'N/A')}")

            # Calculate how well this matches user interests
            interest_match_score = self._calculate_user_interest_match(item, user_data)
            print(f"│      User Interest Match: {interest_match_score}/100")

            # Calculate GitHub relevance
            github_match_score = self._calculate_github_relevance(item, user_intent)
            print(f"│      GitHub Relevance: {github_match_score}/100")

            # Content quality score (from validation or calculate)
            content_quality = item.get('confidence_score', item.get('relevance_score', None))
            if content_quality is None:
                content_quality = self._calculate_content_quality(item)
            print(f"│      Content Quality: {content_quality}/100")

            # COMPOSITE SCORE with proper weighting
            # User interests = 50%, Content Quality = 30%, GitHub = 20%
            composite_score = (
                interest_match_score * 0.50 +
                content_quality * 0.30 +
                github_match_score * 0.20
            )
            print(f"│      → Composite Score: {composite_score:.1f}/100")
            print(f"│         (50% user interests + 30% quality + 20% GitHub)")

            total_score += composite_score
            user_interest_matches += interest_match_score
            github_relevance += github_match_score

        # Overall analysis
        avg_score = total_score / len(items) if items else 0
        avg_interest_match = user_interest_matches / len(items) if items else 0
        avg_github_relevance = github_relevance / len(items) if items else 0

        print("\n└─ OVERALL ANALYSIS")
        print(f"   Average Composite Score: {avg_score:.1f}/100")
        print(f"   Average User Interest Match: {avg_interest_match:.1f}/100")
        print(f"   Average GitHub Relevance: {avg_github_relevance:.1f}/100")
        print()

        # Quality assessment
        if avg_score >= 75:
            print("   ✅ EXCELLENT - Highly personalized recommendations")
        elif avg_score >= 60:
            print("   ✓ GOOD - Decent personalization, room for improvement")
        elif avg_score >= 45:
            print("   ⚠️  FAIR - Needs better alignment with user profile")
        else:
            print("   ❌ POOR - Recommendations don't match user needs well")

        print("\n" + "="*80)

    def _calculate_user_interest_match(self, item: Dict, user_data: dict) -> float:
        """
        Calculate how well an item matches user's stated interests.
        This should be the PRIMARY factor in scoring.
        """
        interests = user_data.get('interests', [])
        if not interests:
            return 50  # Neutral if no interests specified

        content = (item.get('content', '') + ' ' +
                  item.get('description', '') + ' ' +
                  item.get('title', '') + ' ' +
                  item.get('url', '')).lower()

        # Extended keyword mapping for better matching
        interest_keywords = {
            'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 'neural', 'llm', 'gpt', 'claude', 'openai', 'anthropic'],
            'ml': ['machine learning', 'ml', 'ai', 'deep learning', 'data science', 'model', 'training', 'inference'],
            'tools': ['tool', 'sdk', 'api', 'platform', 'framework', 'library', 'developer', 'devtools'],
            'hackathon': ['hackathon', 'competition', 'challenge', 'contest', 'prize', 'devpost'],
            'product': ['product', 'launch', 'startup', 'build', 'ship', 'release'],
            'development': ['development', 'engineering', 'software', 'code', 'programming', 'developer'],
            'web3': ['blockchain', 'crypto', 'web3', 'defi', 'ethereum', 'solana', 'nft'],
            'startup': ['startup', 'founder', 'funding', 'vc', 'seed', 'series', 'yc', 'techstars'],
        }

        score = 0
        matched_interests = 0

        for interest in interests:
            interest_lower = interest.lower()
            interest_matched = False

            # Direct match (high value)
            if interest_lower in content:
                score += 25
                interest_matched = True
                matched_interests += 1
                continue

            # Split compound interests (e.g., "ai/ml tools" → ["ai", "ml", "tools"])
            interest_words = interest_lower.replace('/', ' ').split()

            for word in interest_words:
                # Skip common words
                if word in ['and', 'or', 'the', 'a', 'an', 'in', 'on', 'at']:
                    continue

                # Direct word match (medium value)
                if word in content:
                    score += 15
                    interest_matched = True

                # Extended keyword match (lower value)
                if word in interest_keywords:
                    for keyword in interest_keywords[word]:
                        if keyword in content:
                            score += 10
                            interest_matched = True
                            break

            if interest_matched:
                matched_interests += 1

        # Normalize score (0-100)
        # Give bonus for matching multiple interests
        max_possible = len(interests) * 25
        if max_possible > 0:
            base_score = min((score / max_possible) * 100, 100)
        else:
            base_score = 50

        # Boost if matches opportunity_types preference
        opportunity_types = user_data.get('preferences', {}).get('opportunity_types', [])
        for opp_type in opportunity_types:
            if opp_type.lower() in content:
                base_score = min(base_score + 10, 100)

        return round(base_score)

    def _calculate_github_relevance(self, item: Dict, user_intent: dict) -> float:
        """
        Calculate GitHub relevance. This is SECONDARY to user interests.
        Only for understanding user's technical context.
        """
        if not isinstance(user_intent, dict):
            return 60  # Slightly positive if no GitHub data

        content = (item.get('content', '') + ' ' +
                  item.get('description', '') + ' ' +
                  item.get('title', '') + ' ' +
                  item.get('url', '')).lower()

        score = 60  # Start slightly positive

        # Check primary intent
        primary_intent = user_intent.get('primary_intent', '').lower()
        if primary_intent:
            # Extract key terms from intent
            intent_keywords = primary_intent.split()
            for keyword in intent_keywords:
                if len(keyword) > 3 and keyword in content:  # Skip short words
                    score += 5

        # Check if mentions active repos (+20 points)
        evidence = user_intent.get('evidence', {})
        active_repos = evidence.get('active_repos', [])
        for repo in active_repos[:5]:  # Check top 5
            repo_lower = repo.lower()
            if repo_lower in content or any(word in content for word in repo_lower.split('-')):
                score = min(score + 15, 100)

        # Check if mentions technologies user is using (+15 points)
        tech_using = evidence.get('technologies_using', [])
        for tech in tech_using[:5]:
            if tech.lower() in content:
                score = min(score + 10, 100)

        # Check if mentions technologies user is exploring (+10 points)
        tech_exploring = evidence.get('technologies_exploring', [])
        for tech in tech_exploring[:5]:
            if tech.lower() in content:
                score = min(score + 8, 100)

        # Give credit for technical content
        tech_keywords = ['github', 'api', 'sdk', 'framework', 'library', 'release', 'version', 'open source']
        tech_mentions = sum(1 for keyword in tech_keywords if keyword in content)
        score = min(score + (tech_mentions * 3), 100)

        return round(min(score, 100))

    def _calculate_content_quality(self, item: Dict) -> float:
        """Calculate content quality based on various factors"""
        score = 50  # Start at neutral

        # Has URL? (+20)
        if item.get('url') and item.get('url') != '#':
            score += 20

        # Has good description? (+15)
        description = item.get('description', '')
        if len(description) > 100:
            score += 15
        elif len(description) > 50:
            score += 10

        # Has action? (+10)
        if item.get('action') and len(item.get('action', '')) > 10:
            score += 10

        # Has image? (+5)
        if item.get('image_url'):
            score += 5

        # From reputable source? (+10)
        source = item.get('source', '').lower()
        reputable_sources = ['github', 'techcrunch', 'anthropic', 'openai', 'hackernews', 'devpost']
        if any(rep_source in source for rep_source in reputable_sources):
            score += 10

        return round(min(score, 100))

    async def _add_images_to_items(self, items):
        """Add relevant images to each item"""
        items_with_images = []

        for item in items:
            # Get image based on the image_query if available, otherwise use title
            query = item.get('image_query', item.get('title', 'news'))
            category = item.get('category', '🎯')

            # Get relevant image
            image_url = await self.image_fetcher.get_relevant_image(query, category)

            # Add image to item
            item_with_image = item.copy()
            item_with_image['image'] = image_url
            items_with_images.append(item_with_image)

        return items_with_images
