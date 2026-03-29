"""
Economic Times Article Fetcher
Fetches latest articles from Economic Times RSS feeds
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EconomicTimesFetcher:
    """Fetches and parses Economic Times articles"""
    
    RSS_FEEDS = [
        "https://economictimes.indiatimes.com/rssfeedsdefault.cms",  # Main feed
        "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",  # Tech
        "https://economictimes.indiatimes.com/news/rssfeeds/1715249553.cms",  # Business
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Simple cache
        self._cache = {}
        self._cache_expiry = {}
        self._cache_duration = timedelta(minutes=5)
    
    def fetch_latest_articles(self, limit: int = 20, fetch_full_content: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch latest articles from all RSS feeds with caching
        
        Args:
            limit: Maximum number of articles to fetch
            fetch_full_content: If False, only fetch metadata (faster)
        
        Returns:
            List of article dictionaries
        """
        cache_key = f"articles_{limit}_{fetch_full_content}"
        
        # Check cache
        if cache_key in self._cache:
            if datetime.now() < self._cache_expiry.get(cache_key, datetime.min):
                expires_in = (self._cache_expiry[cache_key] - datetime.now()).seconds
                logger.info(f"Returning cached articles (expires in {expires_in}s)")
                return self._cache[cache_key]
        
        # Fetch fresh data
        logger.info("Fetching fresh articles from RSS feeds")
        articles = self._fetch_articles_internal(limit, fetch_full_content)
        
        # Update cache
        self._cache[cache_key] = articles
        self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
        
        return articles
    
    def _fetch_articles_internal(self, limit: int, fetch_full_content: bool) -> List[Dict[str, Any]]:
        """Internal method to fetch articles (no caching)"""
        logger.info("Fetching articles from Economic Times RSS feeds")
        
        all_articles = []
        
        for feed_url in self.RSS_FEEDS:
            try:
                articles = self._parse_rss_feed(feed_url, fetch_full_content=fetch_full_content)
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} articles from {feed_url}")
            except Exception as e:
                logger.error(f"Failed to fetch from {feed_url}: {e}")
        
        # Remove duplicates based on URL
        unique_articles = {article['url']: article for article in all_articles}
        articles_list = list(unique_articles.values())
        
        # Sort by publish time (most recent first)
        articles_list.sort(key=lambda x: x['published_time'], reverse=True)
        
        return articles_list[:limit]
    
    def _parse_rss_feed(self, feed_url: str, fetch_full_content: bool = True) -> List[Dict[str, Any]]:
        """Parse RSS feed and extract article data"""
        feed = feedparser.parse(feed_url)
        articles = []
        
        for entry in feed.entries:
            try:
                article = {
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'published_time': self._parse_publish_time(entry),
                    'category': self._extract_category(entry),
                    'content': '',
                    'images': [],
                }
                
                # Only fetch full content if requested
                if fetch_full_content:
                    full_content = self._fetch_article_content(article['url'])
                    article['content'] = full_content['content']
                    article['images'] = full_content['images']
                
                articles.append(article)
                
            except Exception as e:
                logger.warning(f"Failed to parse article: {e}")
                continue
        
        return articles
    
    def _parse_publish_time(self, entry) -> datetime:
        """Parse publish time from RSS entry"""
        try:
            if hasattr(entry, 'published_parsed'):
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed'):
                return datetime(*entry.updated_parsed[:6])
        except:
            pass
        return datetime.now()
    
    def _extract_category(self, entry) -> str:
        """Extract category from RSS entry"""
        if hasattr(entry, 'tags') and entry.tags:
            return entry.tags[0].get('term', 'general')
        return 'general'
    
    def _fetch_article_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch full article content and images from article page
        
        Args:
            url: Article URL
        
        Returns:
            Dictionary with content and images
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article content
            content = self._extract_content(soup)
            
            # Extract images
            images = self._extract_images(soup, url)
            
            return {
                'content': content,
                'images': images
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch article content from {url}: {e}")
            return {'content': '', 'images': []}
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        # Try different selectors for Economic Times
        selectors = [
            'div.artText',
            'div.article-content',
            'div.Normal',
            'article',
        ]
        
        for selector in selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # Get all paragraphs
                paragraphs = content_div.find_all('p')
                content = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                if content:
                    return content
        
        return ''
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images from article"""
        images = []
        
        # Find article images
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
            
            # Skip small images, icons, and ads
            if any(skip in src.lower() for skip in ['icon', 'logo', 'ad', 'banner']):
                continue
            
            # Make URL absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                from urllib.parse import urljoin
                src = urljoin(base_url, src)
            
            # Get alt text
            alt = img.get('alt', '')
            
            images.append({
                'url': src,
                'caption': alt,
                'type': 'article'
            })
        
        return images[:5]  # Limit to 5 images
    
    def fetch_full_content_for_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch full content for a list of articles"""
        for article in articles:
            if not article.get('content'):
                try:
                    full_content = self._fetch_article_content(article['url'])
                    article['content'] = full_content['content']
                    article['images'] = full_content['images']
                except Exception as e:
                    logger.warning(f"Failed to fetch content for {article['url']}: {e}")
        return articles
    
    def get_article_by_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch a specific article by URL
        
        Args:
            url: Article URL
        
        Returns:
            Article dictionary
        """
        logger.info(f"Fetching article: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = ''
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract summary/description
            summary = ''
            meta_desc = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
            if meta_desc:
                summary = meta_desc.get('content', '')
            
            # Extract category
            category = 'general'
            meta_section = soup.find('meta', {'name': 'section'})
            if meta_section:
                category = meta_section.get('content', 'general')
            
            # Extract full content
            full_content = self._fetch_article_content(url)
            
            return {
                'title': title,
                'summary': summary,
                'url': url,
                'published_time': datetime.now(),
                'category': category,
                'content': full_content['content'],
                'images': full_content['images'],
            }
        except Exception as e:
            logger.error(f"Failed to fetch article {url}: {e}")
            raise
