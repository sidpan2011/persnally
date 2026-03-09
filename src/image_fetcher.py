"""
Image Fetcher for Daily 5 Content
Fetches relevant images for each news/article item
"""

from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


class ImageFetcher:
    def __init__(self):
        self.unsplash_access_key = None  # We'll use placeholder images for now

    async def get_relevant_image(self, query: str, category: str, article_url: str = None) -> str | None:
        """Get relevant image URL for the given query and category"""

        # First try to scrape image from the actual article
        if article_url:
            scraped_image = await self.scrape_article_image(article_url)
            if scraped_image:
                return scraped_image

        # Fallback to curated images based on content

        category_images = {
            "🎯": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=200&fit=crop",  # Target/focus
            "⚡": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=200&fit=crop",  # Lightning/urgent
            "🧠": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=200&fit=crop",  # Brain/learning
            "💰": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400&h=200&fit=crop",  # Money/opportunity
            "🔮": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&h=200&fit=crop",  # Future/crystal ball
        }

        # Get category emoji from category string
        category_emoji = category.split()[0] if category else "🎯"

        # Use specific images based on query keywords
        query_lower = query.lower()

        if any(word in query_lower for word in ["blockchain", "crypto", "web3", "bitcoin", "ethereum"]):
            return "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=400&h=200&fit=crop"
        elif any(word in query_lower for word in ["ai", "machine learning", "neural", "gpt", "ml"]):
            return "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=200&fit=crop"
        elif any(word in query_lower for word in ["startup", "funding", "venture", "accelerator"]):
            return "https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=400&h=200&fit=crop"
        elif any(word in query_lower for word in ["hackathon", "competition", "coding", "programming"]):
            return "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=400&h=200&fit=crop"
        elif any(word in query_lower for word in ["github", "repository", "code", "development"]):
            return "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=400&h=200&fit=crop"
        else:
            # Fallback to category-based image
            return category_images.get(category_emoji, category_images["🎯"])

    def get_placeholder_image(self, width: int = 400, height: int = 200, text: str = "News") -> str:
        """Get a placeholder image with text"""
        # Using placeholder.com service
        return f"https://via.placeholder.com/{width}x{height}/667eea/ffffff?text={text.replace(' ', '+')}"

    async def fetch_unsplash_image(self, query: str) -> str | None:
        """Fetch image from Unsplash API (requires API key)"""
        if not self.unsplash_access_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.unsplash.com/search/photos",
                    params={"query": query, "per_page": 1, "orientation": "landscape"},
                    headers={"Authorization": f"Client-ID {self.unsplash_access_key}"},
                )

                if response.status_code == 200:
                    data = response.json()
                    if data["results"]:
                        return data["results"][0]["urls"]["small"]
        except Exception as e:
            print(f"⚠️ Failed to fetch Unsplash image: {e}")

        return None

    async def scrape_article_image(self, url: str) -> str | None:
        """Scrape the main image from an article URL"""

        if not url or url == "#":
            return None

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0),
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
            ) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    return None

                soup = BeautifulSoup(response.text, "html.parser")

                # Try different methods to find the main article image
                image_url = None

                # Method 1: Open Graph image
                og_image = soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    image_url = og_image["content"]

                # Method 2: Twitter Card image
                if not image_url:
                    twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
                    if twitter_image and twitter_image.get("content"):
                        image_url = twitter_image["content"]

                # Method 3: First article image
                if not image_url:
                    # Look for images in common article containers
                    article_selectors = [
                        "article img",
                        ".post-content img",
                        ".entry-content img",
                        ".article-content img",
                        ".content img",
                        "main img",
                    ]

                    for selector in article_selectors:
                        img_tags = soup.select(selector)
                        for img in img_tags:
                            src = img.get("src") or img.get("data-src")
                            if src and self._is_valid_image(src):
                                image_url = src
                                break
                        if image_url:
                            break

                # Method 4: Any large image on the page
                if not image_url:
                    all_imgs = soup.find_all("img")
                    for img in all_imgs:
                        src = img.get("src") or img.get("data-src")
                        if src and self._is_valid_image(src):
                            # Skip small images (likely icons/logos)
                            width = img.get("width")
                            height = img.get("height")
                            if width and height:
                                try:
                                    if int(width) > 200 and int(height) > 100:
                                        image_url = src
                                        break
                                except:
                                    pass
                            else:
                                # No dimensions specified, assume it might be good
                                image_url = src
                                break

                # Convert relative URLs to absolute
                if image_url:
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url
                    elif image_url.startswith("/"):
                        image_url = urljoin(url, image_url)
                    elif not image_url.startswith("http"):
                        image_url = urljoin(url, image_url)

                return image_url

        except Exception as e:
            print(f"⚠️ Failed to scrape image from {url}: {e}")
            return None

    def _is_valid_image(self, src: str) -> bool:
        """Check if the image source is valid and not an icon/logo"""

        if not src:
            return False

        # Skip common non-article images
        skip_patterns = [
            "logo",
            "icon",
            "avatar",
            "profile",
            "badge",
            "button",
            "ad",
            "banner",
            "footer",
            "header",
            "nav",
            "sidebar",
            "pixel",
            "tracking",
            "analytics",
            "social",
        ]

        src_lower = src.lower()
        if any(pattern in src_lower for pattern in skip_patterns):
            return False

        # Must be a common image format
        if not any(ext in src_lower for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
            return False

        # Skip very small images (likely icons)
        if any(size in src_lower for size in ["16x16", "32x32", "64x64", "100x100"]):
            return False

        return True
