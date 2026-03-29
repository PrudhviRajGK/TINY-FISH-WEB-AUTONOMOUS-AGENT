"""
Web Agent News Service
Hybrid architecture:
  - RSS feeds for fast article DISCOVERY (< 2 seconds)
  - TinyFish Web Agent for deep article EXTRACTION (content + entities)

TinyFish does the meaningful AI work. RSS just gives us URLs quickly.
"""
import logging
import feedparser
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.agents.tinyfish_agent import TinyFishDataAgent

logger = logging.getLogger(__name__)

# RSS feeds for fast discovery
RSS_FEEDS = [
    ("economic_times_tech", "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"),
    ("economic_times_main", "https://economictimes.indiatimes.com/rssfeedsdefault.cms"),
    ("economic_times_biz",  "https://economictimes.indiatimes.com/news/rssfeeds/1715249553.cms"),
]


class WebAgentNewsService:
    """
    Fast discovery via RSS + deep extraction via TinyFish Web Agent.
    TinyFish is used for the work that matters: reading and understanding articles.
    """

    def __init__(self):
        self.agent = TinyFishDataAgent(
            api_key=settings.TINYFISH_API_KEY,
            base_url=settings.TINYFISH_BASE_URL,
        )

    # ------------------------------------------------------------------
    # DISCOVERY — fast RSS (< 2s)
    # ------------------------------------------------------------------

    async def discover_trending_articles(
        self,
        limit: int = 20,
        sites: Optional[List[tuple]] = None,  # kept for API compat, unused
    ) -> List[Dict[str, Any]]:
        """
        Fetch article stubs from RSS feeds in under 2 seconds.
        Returns list of {title, url, summary, category, published_time, source}.
        """
        logger.info("[AGENT] Discovering articles via RSS feeds (fast path)")

        all_articles: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            for feed_name, feed_url in RSS_FEEDS:
                try:
                    logger.info(f"[AGENT] Fetching RSS: {feed_name}")
                    resp = await client.get(feed_url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; FragmentBot/1.0)"
                    })
                    feed = feedparser.parse(resp.text)
                    articles = self._parse_feed(feed, feed_name)
                    all_articles.extend(articles)
                    logger.info(f"[AGENT] {feed_name}: {len(articles)} articles")
                except Exception as e:
                    logger.warning(f"[AGENT] RSS fetch failed for {feed_name}: {e}")

        if not all_articles:
            raise RuntimeError(
                "[AGENT] RSS discovery returned no articles. Check network connectivity."
            )

        # Deduplicate by URL
        seen: set = set()
        unique: List[Dict[str, Any]] = []
        for a in all_articles:
            if a["url"] and a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)

        unique.sort(key=lambda x: x["published_time"], reverse=True)
        logger.info(f"[AGENT] Discovery complete — {len(unique)} unique articles")
        return unique[:limit]

    def _parse_feed(self, feed, source: str) -> List[Dict[str, Any]]:
        articles = []
        for entry in feed.entries:
            try:
                articles.append({
                    "title":          entry.get("title", ""),
                    "url":            entry.get("link", ""),
                    "summary":        entry.get("summary", ""),
                    "content":        entry.get("summary", ""),
                    "category":       self._extract_category(entry),
                    "source":         source,
                    "images":         [],
                    "published_time": self._parse_entry_time(entry),
                    "published_at":   "",
                })
            except Exception:
                continue
        return articles

    # ------------------------------------------------------------------
    # EXTRACTION — TinyFish Web Agent (deep, per article)
    # ------------------------------------------------------------------

    async def extract_full_article(self, url: str) -> Dict[str, Any]:
        """
        Use TinyFish to extract full content + entities from a single article URL.
        This is where the AI agent does real work on the live web.
        """
        logger.info(f"[AGENT] TinyFish extracting article: {url}")
        article = await self.agent.extract_article(url)

        logger.info(f"[AGENT] TinyFish detecting entities")
        entities = await self.agent.detect_entities(article.get("content", ""))
        article["entities"] = entities
        article["published_time"] = self._parse_datetime(article.get("published_at", ""))
        article.setdefault("category", "general")
        article.setdefault("summary", "")

        imgs = len(article.get("images", []))
        vids = len(article.get("videos", []))
        logger.info(f"[AGENT] Article media: {imgs} images, {vids} videos")
        return article

    async def enrich_articles(self, stubs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use TinyFish to extract full content for the top-scored articles only.
        Called after trend scoring so we only deep-extract what we actually need.
        """
        logger.info(f"[AGENT] TinyFish enriching {len(stubs)} top articles")
        enriched = []
        for stub in stubs:
            try:
                full = await self.extract_full_article(stub["url"])
                enriched.append(full)
            except Exception as e:
                logger.error(f"[AGENT] Enrichment failed for {stub['url']}: {e}")
                enriched.append(stub)
        return enriched

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_category(entry) -> str:
        if hasattr(entry, "tags") and entry.tags:
            return entry.tags[0].get("term", "general")
        return "general"

    @staticmethod
    def _parse_entry_time(entry) -> datetime:
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            if hasattr(entry, "updated_parsed") and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
        except Exception:
            pass
        return datetime.now()

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        if not value:
            return datetime.now()
        for fmt in (
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return datetime.now()
