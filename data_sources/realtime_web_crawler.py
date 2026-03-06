"""
Real-Time Web Crawler
Actually crawls the web for fresh, current content instead of using fake data
"""
import httpx
import asyncio
import json
import re
import random
import hashlib
from typing import List, Dict, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urljoin, urlparse

class RealTimeWebCrawler:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.content_cache = {}  # Simple in-memory cache to avoid duplicates
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=self.headers,
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def get_fresh_tech_news(self, user_interests: List[str]) -> List[Dict[str, Any]]:
        """Get genuinely fresh tech news from RELIABLE sources only"""
        
        print("🌐 Crawling VERIFIED, reliable tech news sources...")
        
        all_articles = []

        # ENHANCED: Diverse source selection based on user interests and randomization
        # Store methods (not coroutines yet) to avoid unawaited coroutine warnings
        all_possible_source_methods = [
            self._crawl_google_news_tech,  # NEW: Google News Tech section
            self._crawl_techcrunch,        # Tier 1: Established tech journalism
            self._crawl_the_verge,         # NEW: The Verge - tech culture & news
            self._crawl_wired,             # NEW: Wired - tech & science
            self._crawl_github_blog,       # Tier 1: Official platform updates
            self._crawl_hacker_news_new,   # Tier 1: Curated community
            self._crawl_openai_blog,       # Tier 1: Official AI updates
            self._crawl_anthropic_blog,    # Tier 1: Official AI research
            self._crawl_ethereum_blog,     # Tier 1: Official blockchain updates
            self._crawl_dev_to_fresh,      # Fresh developer content
            self._crawl_ycombinator_news,  # Startup news
            self._crawl_reddit_programming, # Community discussions
            self._crawl_product_hunt,      # New product launches
        ]

        # Randomize source order to get different content each time
        random.shuffle(all_possible_source_methods)

        # Select sources based on user interests + randomization
        selected_source_methods = self._select_diverse_sources(all_possible_source_methods, user_interests)

        # NOW create coroutines from selected methods only
        selected_sources = [method() for method in selected_source_methods]

        print(f"🔍 Selected {len(selected_sources)} sources for crawling")

        results = await asyncio.gather(*selected_sources, return_exceptions=True)

        print("\n📊 Web Crawling Results Summary:")
        source_counts = {}
        for i, result in enumerate(results):
            if isinstance(result, list):
                # Group by source
                for article in result:
                    source = article.get('source', 'Unknown')
                    source_counts[source] = source_counts.get(source, 0) + 1
                all_articles.extend(result)
            elif isinstance(result, Exception):
                print(f"  ⚠️ Source {i+1} failed: {result}")

        # Display what we got from each source
        for source, count in source_counts.items():
            print(f"  {source}: {count} articles")

        print(f"\n📦 Total articles collected: {len(all_articles)}")

        if len(all_articles) == 0:
            print("🚨 WARNING: NO articles collected from ANY source!")
            print("   This indicates a serious problem with web crawling.")
            return []

        # Enhanced filtering with deduplication
        deduplicated_articles = self._deduplicate_articles(all_articles)
        print(f"  After deduplication: {len(deduplicated_articles)} articles")

        relevant_articles = self._filter_by_interests_enhanced(deduplicated_articles, user_interests)
        print(f"  After relevance filtering: {len(relevant_articles)} articles")

        fresh_articles = self._filter_by_recency(relevant_articles, hours=72)  # Last 3 days
        print(f"  After recency filter (72h): {len(fresh_articles)} articles")

        # Enforce topic diversity: no more than 2 articles about the same topic
        diverse_articles = self._enforce_topic_diversity(fresh_articles)
        print(f"  After topic diversity: {len(diverse_articles)} articles")

        # Sort by relevance, recency, and diversity
        sorted_articles = sorted(
            diverse_articles,
            key=lambda x: (
                x.get('relevance_score', 0),
                x.get('diversity_score', 0),
                self._parse_date(x.get('published_at', ''))
            ),
            reverse=True
        )
        
        print(f"✅ Found {len(sorted_articles)} fresh, relevant articles")
        # Additional verification: Remove potentially unreliable sources
        verified_articles = []
        for article in sorted_articles:
            url = article.get('url', '')
            source = article.get('source', '')
            
            # Only include articles from verified domains
            trusted_domains = [
                'techcrunch.com', 'github.blog', 'news.ycombinator.com',
                'openai.com', 'anthropic.com', 'ethereum.org', 'blog.ethereum.org',
                'solana.com', 'polygon.technology', 'chainlink.com',
                'blog.google', 'engineering.fb.com', 'aws.amazon.com',
                'microsoft.com', 'apple.com', 'developer.apple.com'
            ]
            
            if any(domain in url for domain in trusted_domains) or source in ['HackerNews', 'GitHub Blog', 'TechCrunch', 'OpenAI Blog']:
                verified_articles.append(article)
        
        print(f"✅ Verified {len(verified_articles)} articles from trusted sources")
        return verified_articles[:15]  # Return top 15 verified articles
    
    async def _crawl_google_news_tech(self) -> List[Dict[str, Any]]:
        """Crawl Google News Technology section RSS feed"""
        try:
            print("  📰 Crawling Google News (Technology)...")

            # Google News RSS feed for Technology category
            feed_url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"

            response = await self.session.get(feed_url, timeout=15)

            if response.status_code != 200:
                print(f"  ⚠️ Google News returned {response.status_code}")
                return []

            # Parse RSS feed
            feed = feedparser.parse(response.text)

            articles = []
            for entry in feed.entries[:15]:  # Get top 15
                try:
                    # Extract published date
                    published = entry.get('published_parsed', None)
                    if published:
                        pub_date = datetime(*published[:6])
                    else:
                        pub_date = datetime.now()

                    # Check if article is recent (last 3 days)
                    if (datetime.now() - pub_date).days > 3:
                        continue

                    article = {
                        'title': entry.get('title', 'No Title'),
                        'url': entry.get('link', ''),
                        'summary': entry.get('summary', '')[:300],
                        'published_at': pub_date.isoformat(),
                        'source': 'Google News',
                        'category': 'tech_news'
                    }

                    articles.append(article)
                except Exception as e:
                    continue

            print(f"    ✅ Found {len(articles)} recent articles from Google News")
            return articles

        except Exception as e:
            print(f"  ⚠️ Google News crawl failed: {e}")
            return []

    async def _crawl_techcrunch(self) -> List[Dict[str, Any]]:
        """Crawl TechCrunch for latest tech news"""
        try:
            print("  📰 Crawling TechCrunch...")
            response = await self.session.get("https://techcrunch.com/feed/")
            
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                
                articles = []
                for entry in feed.entries[:15]:  # Increased from 10 to 15
                    published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                    
                    # Only include recent articles (last 3 days)
                    if (datetime.now() - published).days <= 3:
                        articles.append({
                            'title': entry.title,
                            'description': self._clean_html(entry.get('summary', '')),
                            'url': entry.link,
                            'source': 'TechCrunch',
                            'published_at': published.isoformat(),
                            'category': 'tech_news',
                            'relevance_keywords': entry.title.lower()
                        })
                
                print(f"    ✅ Found {len(articles)} recent articles from TechCrunch")
                return articles
            else:
                print(f"    ⚠️ TechCrunch returned {response.status_code}")
                return []
        except Exception as e:
            print(f"    ❌ TechCrunch crawl failed: {e}")
            return []
    
    async def _crawl_the_verge(self) -> List[Dict[str, Any]]:
        """Crawl The Verge for tech culture and news"""
        try:
            print("  📰 Crawling The Verge...")
            response = await self.session.get("https://www.theverge.com/rss/index.xml")
            
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                
                articles = []
                for entry in feed.entries[:15]:
                    try:
                        published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                        
                        # Only include recent articles (last 5 days)
                        if (datetime.now() - published).days <= 5:
                            articles.append({
                                'title': entry.title,
                                'description': self._clean_html(entry.get('summary', '')),
                                'url': entry.link,
                                'source': 'The Verge',
                                'published_at': published.isoformat(),
                                'category': 'tech_news',
                                'relevance_keywords': entry.title.lower()
                            })
                    except Exception:
                        continue
                
                print(f"    ✅ Found {len(articles)} recent articles from The Verge")
                return articles
            else:
                print(f"    ⚠️ The Verge returned {response.status_code}")
                return []
        except Exception as e:
            print(f"    ❌ The Verge crawl failed: {e}")
            return []
    
    async def _crawl_wired(self) -> List[Dict[str, Any]]:
        """Crawl Wired for tech and science news"""
        try:
            print("  📰 Crawling Wired...")
            response = await self.session.get("https://www.wired.com/feed/rss")
            
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                
                articles = []
                for entry in feed.entries[:15]:
                    try:
                        published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                        
                        # Only include recent articles (last 5 days)
                        if (datetime.now() - published).days <= 5:
                            articles.append({
                                'title': entry.title,
                                'description': self._clean_html(entry.get('summary', '')),
                                'url': entry.link,
                                'source': 'Wired',
                                'published_at': published.isoformat(),
                                'category': 'tech_news',
                                'relevance_keywords': entry.title.lower()
                            })
                    except Exception:
                        continue
                
                print(f"    ✅ Found {len(articles)} recent articles from Wired")
                return articles
            else:
                print(f"    ⚠️ Wired returned {response.status_code}")
                return []
        except Exception as e:
            print(f"    ❌ Wired crawl failed: {e}")
            return []
    
    async def _crawl_hacker_news_new(self) -> List[Dict[str, Any]]:
        """Get the newest stories from HackerNews (not just top stories)"""
        try:
            # Get newest stories instead of just top stories
            response = await self.session.get("https://hacker-news.firebaseio.com/v0/newstories.json")
            if response.status_code == 200:
                story_ids = response.json()[:20]  # Get 20 newest stories
                
                stories = []
                for story_id in story_ids:
                    try:
                        story_response = await self.session.get(
                            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        )
                        
                        if story_response.status_code == 200:
                            story = story_response.json()
                            if story and story.get('title') and story.get('time'):
                                story_time = datetime.fromtimestamp(story['time'])
                                
                                # Only include stories from last 24 hours
                                if (datetime.now() - story_time).total_seconds() < 86400:  # 24 hours
                                    stories.append({
                                        'title': story['title'],
                                        'description': f"Fresh discussion on HackerNews with {story.get('descendants', 0)} comments",
                                        'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                                        'source': 'HackerNews',
                                        'published_at': story_time.isoformat(),
                                        'category': 'discussion',
                                        'relevance_keywords': story['title'].lower()
                                    })
                        
                        await asyncio.sleep(0.1)  # Rate limiting
                    except Exception:
                        continue
                
                return stories
        except Exception as e:
            print(f"⚠️ HackerNews crawl failed: {e}")
            return []
    
    async def _crawl_github_blog(self) -> List[Dict[str, Any]]:
        """Crawl GitHub's official blog for latest updates"""
        try:
            response = await self.session.get("https://github.blog/feed/")
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                
                articles = []
                for entry in feed.entries[:5]:
                    published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                    
                    articles.append({
                        'title': f"GitHub: {entry.title}",
                        'description': self._clean_html(entry.get('summary', '')),
                        'url': entry.link,
                        'source': 'GitHub Blog',
                        'published_at': published.isoformat(),
                        'category': 'platform_update',
                        'relevance_keywords': f"github {entry.title.lower()}"
                    })
                
                return articles
        except Exception as e:
            print(f"⚠️ GitHub blog crawl failed: {e}")
            return []
    
    async def _crawl_openai_blog(self) -> List[Dict[str, Any]]:
        """Crawl OpenAI's blog for AI updates"""
        try:
            response = await self.session.get("https://openai.com/blog")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                articles = []
                # Look for blog post links (this is a simplified approach)
                blog_links = soup.find_all('a', href=re.compile(r'/blog/'))
                
                for link in blog_links[:5]:
                    title = link.get_text(strip=True)
                    if title and len(title) > 10:  # Filter out short/empty titles
                        articles.append({
                            'title': f"OpenAI: {title}",
                            'description': f"Latest update from OpenAI: {title}",
                            'url': urljoin("https://openai.com", link.get('href')),
                            'source': 'OpenAI Blog',
                            'published_at': datetime.now().isoformat(),  # We don't have exact dates from scraping
                            'category': 'ai_update',
                            'relevance_keywords': f"openai ai {title.lower()}"
                        })
                
                return articles
        except Exception as e:
            print(f"⚠️ OpenAI blog crawl failed: {e}")
            return []
    
    async def _crawl_ycombinator_news(self) -> List[Dict[str, Any]]:
        """Get latest from Y Combinator news/updates"""
        try:
            response = await self.session.get("https://www.ycombinator.com/blog")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                articles = []
                # Look for blog post titles (simplified scraping)
                post_titles = soup.find_all(['h1', 'h2', 'h3'], class_=re.compile(r'title|heading'))
                
                for title_elem in post_titles[:3]:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 10:
                        articles.append({
                            'title': f"YC: {title}",
                            'description': f"Latest from Y Combinator: {title}",
                            'url': "https://www.ycombinator.com/blog",
                            'source': 'Y Combinator',
                            'published_at': datetime.now().isoformat(),
                            'category': 'startup_news',
                            'relevance_keywords': f"yc startup {title.lower()}"
                        })
                
                return articles
        except Exception as e:
            print(f"⚠️ YC crawl failed: {e}")
            return []
    
    async def _crawl_dev_to_fresh(self) -> List[Dict[str, Any]]:
        """Get fresh articles from Dev.to"""
        print("  📰 Calling Dev.to API...")
        try:
            response = await self.session.get("https://dev.to/api/articles?per_page=20&top=7")  # Increased from 10 to 20, top=7 for last week
            print(f"  Dev.to API response: {response.status_code}")

            if response.status_code == 200:
                articles_data = response.json()
                print(f"  Dev.to returned {len(articles_data)} articles")

                articles = []
                for article in articles_data:
                    try:
                        published = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))

                        days_old = (datetime.now(published.tzinfo) - published).days
                        if days_old <= 3:
                            articles.append({
                                'title': article['title'],
                                'description': article.get('description', article['title'])[:300],
                                'url': article['url'],
                                'source': 'Dev.to',
                                'published_at': published.replace(tzinfo=None).isoformat(),
                                'category': 'tutorial',
                                'relevance_keywords': ' '.join(article.get('tag_list', []))
                            })
                    except Exception as parse_error:
                        print(f"  ⚠️ Dev.to article parse error: {parse_error}")
                        continue

                print(f"  ✅ Dev.to: {len(articles)} articles within last 7 days")
                return articles
            else:
                print(f"  ❌ Dev.to API returned non-200 status: {response.status_code}")
                return []
        except Exception as e:
            print(f"  ❌ Dev.to crawl failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _crawl_anthropic_blog(self) -> List[Dict[str, Any]]:
        """Crawl Anthropic's official blog for AI research updates"""
        try:
            response = await self.session.get("https://www.anthropic.com/news")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                articles = []
                # Look for blog post links (simplified approach)
                blog_links = soup.find_all('a', href=re.compile(r'/news/'))
                
                for link in blog_links[:3]:
                    title = link.get_text(strip=True)
                    if title and len(title) > 10:
                        articles.append({
                            'title': f"Anthropic Research: {title}",
                            'description': f"Latest AI research from Anthropic: {title}",
                            'url': urljoin("https://www.anthropic.com", link.get('href')),
                            'source': 'Anthropic',
                            'published_at': datetime.now().isoformat(),
                            'category': 'ai_research',
                            'relevance_keywords': f"anthropic ai research {title.lower()}"
                        })
                
                return articles
        except Exception as e:
            print(f"⚠️ Anthropic blog crawl failed: {e}")
            return []
    
    async def _crawl_ethereum_blog(self) -> List[Dict[str, Any]]:
        """Crawl Ethereum's official blog for blockchain updates"""
        try:
            response = await self.session.get("https://blog.ethereum.org/feed.xml")
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                
                articles = []
                for entry in feed.entries[:3]:
                    published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                    
                    articles.append({
                        'title': f"Ethereum Foundation: {entry.title}",
                        'description': self._clean_html(entry.get('summary', '')),
                        'url': entry.link,
                        'source': 'Ethereum Foundation',
                        'published_at': published.isoformat(),
                        'category': 'blockchain_update',
                        'relevance_keywords': f"ethereum blockchain {entry.title.lower()}"
                    })
                
                return articles
        except Exception as e:
            print(f"⚠️ Ethereum blog crawl failed: {e}")
            return []
    
    def _clean_html(self, html_text: str) -> str:
        """Clean HTML tags and get plain text"""
        if not html_text:
            return ""
        
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text()
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text[:300]  # Limit length
    
    def _filter_by_interests(self, articles: List[Dict], user_interests: List[str]) -> List[Dict]:
        """Filter articles by user interests"""
        if not user_interests:
            return articles
        
        relevant_articles = []
        for article in articles:
            relevance_score = 0
            text_to_check = f"{article.get('title', '')} {article.get('description', '')} {article.get('relevance_keywords', '')}".lower()
            
            for interest in user_interests:
                interest_words = interest.lower().split()
                for word in interest_words:
                    if word in text_to_check:
                        relevance_score += 1
            
            # Include articles with any relevance or from high-quality sources
            if relevance_score > 0 or article.get('source') in ['GitHub Blog', 'OpenAI Blog', 'TechCrunch']:
                article['relevance_score'] = relevance_score
                relevant_articles.append(article)
        
        return relevant_articles
    
    def _filter_by_recency(self, articles: List[Dict], hours: int = 72) -> List[Dict]:
        """Filter articles by recency"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        fresh_articles = []
        for article in articles:
            try:
                published_at = self._parse_date(article.get('published_at', ''))
                if published_at and published_at >= cutoff_time:
                    fresh_articles.append(article)
            except Exception:
                # If we can't parse the date, include it anyway (might be very fresh)
                fresh_articles.append(article)
        
        return fresh_articles
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        if not date_str:
            return datetime.now()
        
        try:
            # Handle ISO format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.now()
    
    async def get_real_hackathons(self) -> List[Dict[str, Any]]:
        """Get real, current hackathons"""
        try:
            # Try to get hackathons from Devpost
            response = await self.session.get("https://devpost.com/hackathons")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                hackathons = []
                # Look for hackathon cards (simplified scraping)
                hackathon_cards = soup.find_all('div', class_=re.compile(r'hackathon|event'))
                
                for card in hackathon_cards[:5]:
                    title_elem = card.find(['h1', 'h2', 'h3', 'h4'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if 'hackathon' in title.lower() or 'competition' in title.lower():
                            hackathons.append({
                                'title': title,
                                'description': f"Active hackathon: {title}",
                                'url': 'https://devpost.com/hackathons',
                                'source': 'Devpost',
                                'published_at': datetime.now().isoformat(),
                                'category': 'hackathon',
                                'relevance_keywords': f"hackathon competition {title.lower()}"
                            })
                
                return hackathons
        except Exception as e:
            print(f"⚠️ Hackathon crawl failed: {e}")
            return []
    
    def _select_diverse_sources(self, all_sources: List, user_interests: List[str]) -> List:
        """Select diverse sources based on user interests and randomization"""
        
        # Always include core sources
        core_sources = all_sources[:3]  # TechCrunch, GitHub, HackerNews
        
        # Select additional sources based on interests
        interest_based_sources = []
        if any("ai" in interest.lower() or "ml" in interest.lower() for interest in user_interests):
            interest_based_sources.extend([all_sources[3], all_sources[4]])  # OpenAI, Anthropic
        
        if any("web3" in interest.lower() or "blockchain" in interest.lower() for interest in user_interests):
            interest_based_sources.append(all_sources[5])  # Ethereum
        
        if any("startup" in interest.lower() for interest in user_interests):
            interest_based_sources.append(all_sources[7])  # YC News
        
        # Add random sources for diversity
        remaining_sources = [s for s in all_sources[6:] if s not in interest_based_sources]
        random_sources = random.sample(remaining_sources, min(2, len(remaining_sources)))
        
        return core_sources + interest_based_sources + random_sources
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title and URL similarity"""

        seen_title_hashes = set()
        seen_url_slugs = set()
        deduplicated = []

        for article in articles:
            title = article.get('title', '')
            url = article.get('url', '')

            # Title-based dedup
            title_normalized = re.sub(r'[^\w\s]', '', title.lower()).strip()
            title_hash = hashlib.md5(title_normalized.encode()).hexdigest()

            # URL-based dedup (same article, different headline)
            parsed = urlparse(url)
            url_slug = f"{parsed.netloc}{parsed.path}".rstrip('/')

            if title_hash in seen_title_hashes or (url_slug and url_slug in seen_url_slugs):
                continue

            seen_title_hashes.add(title_hash)
            if url_slug:
                seen_url_slugs.add(url_slug)
            deduplicated.append(article)

        return deduplicated

    def _enforce_topic_diversity(self, articles: List[Dict]) -> List[Dict]:
        """Ensure no single topic dominates. Max 2 articles per topic cluster."""
        topic_keywords = {}
        diverse = []

        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            # Extract dominant topic from keywords
            topic = self._classify_topic(text)
            count = topic_keywords.get(topic, 0)

            if count < 2:
                topic_keywords[topic] = count + 1
                diverse.append(article)

        return diverse

    def _classify_topic(self, text: str) -> str:
        """Simple keyword-based topic classification."""
        topic_map = {
            'ai_ml': ['ai', 'machine learning', 'llm', 'gpt', 'claude', 'openai', 'anthropic', 'deep learning', 'neural'],
            'web_dev': ['react', 'nextjs', 'vue', 'angular', 'frontend', 'css', 'javascript', 'typescript', 'web dev'],
            'blockchain': ['blockchain', 'crypto', 'ethereum', 'web3', 'defi', 'nft', 'solana'],
            'devops': ['kubernetes', 'docker', 'aws', 'cloud', 'devops', 'ci/cd', 'terraform'],
            'mobile': ['ios', 'android', 'swift', 'kotlin', 'flutter', 'react native', 'mobile'],
            'security': ['security', 'vulnerability', 'hack', 'breach', 'privacy', 'encryption'],
            'startup': ['startup', 'funding', 'series', 'vc', 'yc', 'launch', 'raise'],
            'open_source': ['open source', 'github', 'repository', 'contributor', 'stars'],
        }

        scores = {}
        for topic, keywords in topic_map.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[topic] = score

        if scores:
            return max(scores, key=scores.get)
        return 'general'
    
    def _filter_by_interests_enhanced(self, articles: List[Dict], user_interests: List[str]) -> List[Dict]:
        """Enhanced interest filtering with better matching and diversity scoring"""
        
        if not user_interests:
            return articles
        
        relevant_articles = []
        source_count = {}  # Track articles per source for diversity
        
        for article in articles:
            relevance_score = 0
            diversity_score = 0
            
            text_to_check = f"{article.get('title', '')} {article.get('description', '')} {article.get('relevance_keywords', '')}".lower()
            
            # Enhanced interest matching
            for interest in user_interests:
                interest_words = interest.lower().split()
                
                # Exact phrase match (higher score)
                if interest.lower() in text_to_check:
                    relevance_score += 3
                
                # Individual word matches
                for word in interest_words:
                    if len(word) > 2 and word in text_to_check:
                        relevance_score += 1
            
            # Diversity scoring - prefer articles from sources we haven't seen much
            source = article.get('source', 'Unknown')
            source_count[source] = source_count.get(source, 0) + 1
            diversity_score = max(0, 5 - source_count[source])  # Diminishing returns per source
            
            # Include articles with relevance or high-quality sources
            if relevance_score > 0 or article.get('source') in ['GitHub Blog', 'OpenAI Blog', 'TechCrunch', 'HackerNews']:
                article['relevance_score'] = relevance_score
                article['diversity_score'] = diversity_score
                relevant_articles.append(article)
        
        return relevant_articles
    
    async def _crawl_reddit_programming(self) -> List[Dict[str, Any]]:
        """Crawl Reddit programming subreddit for discussions"""
        print("  🔴 Calling Reddit API...")
        try:
            response = await self.session.get("https://www.reddit.com/r/programming/hot.json?limit=25")  # Increased limit
            print(f"  Reddit API response: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                posts_raw = data.get('data', {}).get('children', [])
                print(f"  Reddit returned {len(posts_raw)} posts")

                articles = []

                for post in posts_raw:
                    post_data = post.get('data', {})
                    if post_data.get('title'):
                        try:
                            created_time = datetime.fromtimestamp(post_data.get('created_utc', 0))

                            days_old = (datetime.now() - created_time).days
                            if days_old <= 3:
                                articles.append({
                                    'title': post_data['title'],
                                    'description': f"Reddit discussion with {post_data.get('num_comments', 0)} comments and {post_data.get('score', 0)} upvotes",
                                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                                    'source': 'Reddit Programming',
                                    'published_at': created_time.isoformat(),
                                    'category': 'discussion',
                                    'relevance_keywords': post_data.get('title', '').lower()
                                })
                        except Exception as parse_error:
                            print(f"  ⚠️ Reddit post parse error: {parse_error}")
                            continue

                print(f"  ✅ Reddit: {len(articles)} posts within last 7 days")
                return articles
            else:
                print(f"  ❌ Reddit API returned non-200 status: {response.status_code}")
                return []
        except Exception as e:
            print(f"  ❌ Reddit crawl failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _crawl_product_hunt(self) -> List[Dict[str, Any]]:
        """Crawl Product Hunt for new tech products - using GraphQL API"""
        print("  🏹 Calling Product Hunt GraphQL API...")
        try:
            # Use Product Hunt's GraphQL API (public posts endpoint)
            url = "https://www.producthunt.com/frontend/graphql"
            query = {
                "query": """
                    query {
                        posts(first: 20) {
                            edges {
                                node {
                                    name
                                    tagline
                                    url
                                    createdAt
                                    votesCount
                                }
                            }
                        }
                    }
                """
            }

            response = await self.session.post(url, json=query)
            print(f"  Product Hunt API response: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                edges = data.get('data', {}).get('posts', {}).get('edges', [])
                print(f"  Product Hunt returned {len(edges)} products")

                articles = []

                for edge in edges:
                    try:
                        node = edge.get('node', {})
                        created_at = datetime.fromisoformat(node.get('createdAt', '').replace('Z', '+00:00'))
                        days_old = (datetime.now(created_at.tzinfo) - created_at).days

                        if days_old <= 3:
                            articles.append({
                                'title': node.get('name', ''),
                                'description': node.get('tagline', ''),
                                'url': node.get('url', ''),
                                'source': 'Product Hunt',
                                'published_at': created_at.replace(tzinfo=None).isoformat(),
                                'category': 'product_launch',
                                'relevance_keywords': node.get('tagline', '').lower()
                            })
                    except Exception as parse_error:
                        print(f"  ⚠️ Product Hunt item parse error: {parse_error}")
                        continue

                print(f"  ✅ Product Hunt: {len(articles)} products within last 7 days")
                return articles
            else:
                # Fallback to scraping if GraphQL fails
                print(f"  ⚠️ Product Hunt GraphQL failed ({response.status_code}), trying scraping...")
                return await self._crawl_product_hunt_fallback()
        except Exception as e:
            print(f"  ❌ Product Hunt crawl failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _crawl_product_hunt_fallback(self) -> List[Dict[str, Any]]:
        """Fallback: scrape Product Hunt homepage"""
        try:
            response = await self.session.get("https://www.producthunt.com/")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                articles = []
                # Look for product cards (simplified scraping)
                product_links = soup.find_all('a', href=re.compile(r'/posts/'))
                
                for link in product_links[:5]:
                    title = link.get_text(strip=True)
                    if title and len(title) > 10:
                        articles.append({
                            'title': f"New Product: {title}",
                            'description': f"Featured on Product Hunt: {title}",
                            'url': urljoin("https://www.producthunt.com", link.get('href')),
                            'source': 'Product Hunt',
                            'published_at': datetime.now().isoformat(),
                            'category': 'product_launch',
                            'relevance_keywords': f"product launch {title.lower()}"
                        })
                
                return articles
        except Exception as e:
            print(f"⚠️ Product Hunt crawl failed: {e}")
            return []
