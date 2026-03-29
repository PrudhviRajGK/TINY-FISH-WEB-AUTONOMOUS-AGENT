"""
TinyFish Web Agent
Core dependency for all live web interaction in the automation pipeline.
Responsible for article discovery, extraction, entity detection, and search.
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Real TinyFish API base URL
TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1"

NEWS_SITES = {
    "economic_times": "https://economictimes.indiatimes.com/tech",
    "techcrunch": "https://techcrunch.com",
    "reuters": "https://www.reuters.com/technology",
    "bloomberg": "https://www.bloomberg.com/technology",
    "hackernews": "https://news.ycombinator.com",
}


class TinyFishDataAgent(BaseAgent):
    """
    TinyFish Web Agent — the ONLY system responsible for live web interaction.
    All article discovery and extraction flows through this agent.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = TINYFISH_BASE_URL):
        super().__init__("TinyFishDataAgent")
        if not api_key:
            raise ValueError(
                "[AGENT] TinyFish API key is required. "
                "Set TINYFISH_API_KEY in your .env file."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Public interface used by WebAgentNewsService
    # ------------------------------------------------------------------

    async def discover_articles(self, site_url: str, site_name: str = "") -> List[Dict[str, Any]]:
        """
        Navigate to a news site and extract article links + metadata.
        Returns a list of article stubs: {title, url, summary, published_at, source}.
        """
        label = site_name or site_url
        logger.info(f"[AGENT] Opening {site_url}")
        logger.info(f"[AGENT] Extracting top article links from {label}")

        goal = (
            "Find the top 5 most recent news article headlines on this page. "
            "For each article return: title, url (absolute), summary or description, "
            "published_at (ISO string if available), category. "
            "Return as JSON array."
        )

        result = await self._run_sync(site_url, goal)

        articles = self._parse_list_result(result, site_url, label)
        logger.info(f"[AGENT] Discovered {len(articles)} articles from {label}")
        return articles

    async def extract_article(self, url: str) -> Dict[str, Any]:
        """
        Navigate to an article URL and extract full content, all images, videos, and metadata.
        Raises on failure — no silent fallback.
        """
        logger.info(f"[AGENT] Following article URL: {url}")
        logger.info(f"[AGENT] Extracting article content, images and videos")

        goal = (
            "Extract the full article from this news page. "
            "Return JSON with these exact fields: "
            "title (string), "
            "content (full article text), "
            "summary (2-3 sentence summary), "
            "published_at (ISO date string), "
            "author (string), "
            "category (string), "
            "images (array of ALL photos/images on the page — each with url (absolute https) and caption). "
            "Include the hero image, all inline article photos, and any thumbnail images. "
            "Make all image URLs absolute. Do not include videos or ads."
        )

        result = await self._run_sync(url, goal)

        article = self._parse_article_result(result, url)
        logger.info(
            f"[AGENT] Extracted: '{article.get('title', url)}' — "
            f"{len(article.get('images', []))} images"
        )
        return article

    async def search(self, query: str, site_url: str = "https://news.google.com") -> List[Dict[str, Any]]:
        """
        Search for articles matching a query via TinyFish.
        """
        logger.info(f"[AGENT] Searching for: {query}")

        goal = (
            f"Search for news articles about: {query}. "
            "Return the top 5 results as JSON array with: title, url, summary, published_at, source."
        )

        result = await self._run_sync(site_url, goal)
        articles = self._parse_list_result(result, site_url, "search")
        logger.info(f"[AGENT] Search returned {len(articles)} results")
        return articles

    async def detect_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Use TinyFish to detect named entities in article text.
        Returns {people, organizations, locations}.
        """
        logger.info(f"[AGENT] Detecting entities in article text")

        # Use a neutral page as the navigation target; goal carries the text
        goal = (
            "Ignore the page content. Instead, analyze this text and extract named entities. "
            f"Text: {text[:2000]}\n\n"
            "Return JSON: {\"people\": [], \"organizations\": [], \"locations\": []}"
        )

        result = await self._run_sync("https://agent.tinyfish.ai", goal)

        if isinstance(result, dict):
            entities = {
                "people": result.get("people", []),
                "organizations": result.get("organizations", []),
                "locations": result.get("locations", []),
            }
        else:
            entities = {"people": [], "organizations": [], "locations": []}

        logger.info(
            f"[AGENT] Detected entities — "
            f"people: {len(entities['people'])}, "
            f"orgs: {len(entities['organizations'])}, "
            f"locations: {len(entities['locations'])}"
        )
        return entities

    # ------------------------------------------------------------------
    # BaseAgent.execute — used by CoordinatorAgent for manual generation
    # ------------------------------------------------------------------

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch article content for a single URL or topic (CoordinatorAgent path).
        Raises on failure — no silent fallback.
        """
        self.log_start("Fetching article data via TinyFish Web Agent")

        article_url = context.get("article_url")
        topic = context.get("topic")

        if article_url:
            article = await self.extract_article(article_url)
        elif topic:
            results = await self.search(topic)
            if not results:
                raise RuntimeError(
                    f"[AGENT] TinyFish returned no results for topic '{topic}'. "
                    "Cannot continue without live web data."
                )
            article = await self.extract_article(results[0]["url"])
        else:
            raise ValueError("Either 'article_url' or 'topic' must be provided in context.")

        entities = await self.detect_entities(article.get("content", ""))
        article["entities"] = entities

        self.log_complete(f"Article ready: {article.get('title')}")

        return {
            "article_data": article,
            "title": article.get("title", ""),
            "summary": article.get("summary", ""),
            "content": article.get("content", ""),
            "key_points": article.get("key_points", []),
            "entities": entities,
            "topics": article.get("topics", []),
            "extracted_images": article.get("images", []),
            "metadata": article.get("metadata", {}),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_sync(self, url: str, goal: str) -> Any:
        """
        Call TinyFish using async pattern:
          POST /v1/automation/run-async  -> get run_id
          GET  /v1/runs/{run_id}         -> poll until COMPLETED
        Raises RuntimeError on failure — no silent fallback.
        """
        import asyncio

        queue_endpoint = f"{self.base_url}/automation/run-async"
        poll_base = f"{self.base_url}/runs"
        payload = {"url": url, "goal": goal}

        logger.info(f"[AGENT] Calling TinyFish API: {queue_endpoint}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(queue_endpoint, json=payload, headers=self._headers)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                raise RuntimeError(
                    f"[AGENT] TinyFish API returned HTTP {e.response.status_code}: {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                raise RuntimeError(
                    f"[AGENT] TinyFish API request failed: {type(e).__name__}: {e}"
                ) from e

        run_id = data.get("run_id")
        if not run_id:
            raise RuntimeError(
                f"[AGENT] TinyFish did not return a run_id. Response: {data}"
            )

        logger.info(f"[AGENT] TinyFish run queued: {run_id} — polling for result...")

        # Poll GET /v1/runs/{run_id} until complete (max 5 min, 3s intervals)
        poll_url = f"{poll_base}/{run_id}"
        max_attempts = 100

        async with httpx.AsyncClient(timeout=15.0) as client:
            for attempt in range(max_attempts):
                await asyncio.sleep(3)
                try:
                    poll_resp = await client.get(poll_url, headers=self._headers)
                    poll_resp.raise_for_status()
                    poll_data = poll_resp.json()
                except Exception as e:
                    logger.warning(f"[AGENT] Poll attempt {attempt + 1} failed: {e}")
                    continue

                status = poll_data.get("status", "")
                logger.info(f"[AGENT] Run {run_id} status: {status}")

                if status == "COMPLETED":
                    result = poll_data.get("result", poll_data)
                    logger.info(f"[AGENT] TinyFish run completed successfully")
                    return result
                elif status in ("FAILED", "CANCELLED"):
                    err = poll_data.get("error") or {}
                    raise RuntimeError(
                        f"[AGENT] TinyFish run {status}. "
                        f"Error: {err.get('message', 'unknown') if isinstance(err, dict) else err}"
                    )
                # PENDING or RUNNING — keep polling

        raise RuntimeError(
            f"[AGENT] TinyFish run {run_id} timed out after {max_attempts * 3}s"
        )

    def _parse_list_result(
        self, result: Any, site_url: str, source_label: str
    ) -> List[Dict[str, Any]]:
        """Normalise a TinyFish result into a list of article stubs."""
        articles = []

        if isinstance(result, list):
            raw_list = result
        elif isinstance(result, dict):
            # Common keys TinyFish might use
            for key in ("articles", "results", "items", "data", "headlines"):
                if key in result and isinstance(result[key], list):
                    raw_list = result[key]
                    break
            else:
                raw_list = [result]
        else:
            logger.warning(f"[AGENT] Unexpected result type from TinyFish: {type(result)}")
            return []

        for item in raw_list:
            if not isinstance(item, dict):
                continue
            url = item.get("url", "")
            if not url:
                continue
            # Make relative URLs absolute
            if url.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(site_url)
                url = f"{parsed.scheme}://{parsed.netloc}{url}"

            articles.append({
                "title": item.get("title", ""),
                "url": url,
                "summary": item.get("summary") or item.get("description", ""),
                "published_at": item.get("published_at") or item.get("date", ""),
                "category": item.get("category", "general"),
                "source": source_label,
                "content": item.get("content", ""),
                "images": item.get("images", []),
            })

        return articles

    def _parse_article_result(self, result: Any, url: str) -> Dict[str, Any]:
        """Normalise a TinyFish result into a full article dict with images and text."""
        if not isinstance(result, dict):
            raise RuntimeError(
                f"[AGENT] TinyFish returned unexpected format for article extraction: {type(result)}"
            )

        # Normalise images — keep only absolute https URLs
        raw_images = result.get("images", [])
        images = []
        for img in raw_images:
            if isinstance(img, str):
                img = {"url": img, "caption": ""}
            img_url = img.get("url", "")
            if img_url and img_url.startswith("http"):
                images.append({"url": img_url, "caption": img.get("caption", "")})

        return {
            "title": result.get("title", ""),
            "url": url,
            "content": result.get("content") or result.get("body", ""),
            "summary": result.get("summary") or result.get("description", ""),
            "published_at": result.get("published_at") or result.get("date", ""),
            "author": result.get("author", ""),
            "category": result.get("category", "general"),
            "images": images,
            "entities": result.get("entities", {"people": [], "organizations": [], "locations": []}),
            "key_points": result.get("key_points", []),
            "topics": result.get("topics", []),
            "metadata": result.get("metadata", {}),
            "source": result.get("source", ""),
        }
