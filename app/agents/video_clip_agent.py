"""
Video Clip Agent
Searches Pexels and Pixabay for stock video clips matching a visual query.
Returns None if no suitable clip is found — caller falls back to ImageAgent.
"""
import logging
import httpx
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Minimum quality thresholds
MIN_DURATION_SECONDS = 3
MIN_WIDTH = 1080


class VideoClipAgent(BaseAgent):
    """
    Searches stock video APIs for cinematic clips.
    Sources: Pexels (primary), Pixabay (secondary).
    Returns None when no suitable clip is found.
    """

    def __init__(
        self,
        pexels_api_key: Optional[str] = None,
        pixabay_api_key: Optional[str] = None,
        clips_dir: Optional[Path] = None,
    ):
        super().__init__("VideoClipAgent")
        self.pexels_api_key = pexels_api_key
        self.pixabay_api_key = pixabay_api_key
        self.clips_dir = clips_dir or Path("resources/clips")
        self.clips_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for a motion overlay clip for every segment.
        Clips are used as 25% opacity overlays on top of images — not as primary visuals.
        No clip is ever used more than once.
        """
        self.log_start("Searching for motion overlay clips (all segments)")

        visual_plan = context.get("visual_plan", [])
        article_title = context.get("title", "")
        used_video_ids: set = set()
        clip_results = []

        for item in visual_plan:
            idx = item["segment_index"]
            query = self._topic_aware_query(
                item["query"], article_title, item.get("segment_type", "")
            )
            self.log_progress(f"Segment {idx}: searching overlay clip '{query}'")

            result = await self.search_video_clip(
                query, segment_index=idx, exclude_ids=used_video_ids
            )

            if result["clip_path"]:
                used_video_ids.add(result.get("video_id", str(result["clip_path"])))
                self.log_progress(f"  Overlay clip found ({result['source']})")
            else:
                self.log_progress(f"  No clip — segment will use Ken Burns only")

            clip_results.append({"segment_index": idx, **result})

        found = sum(1 for r in clip_results if r["clip_path"])
        self.log_complete(f"Overlay clips: {found}/{len(clip_results)} found")
        return {"clip_results": clip_results}

    def _topic_aware_query(self, base_query: str, article_title: str, segment_type: str) -> str:
        """
        Build a search query that combines the visual description with
        the article's actual topic so clips stay relevant.
        """
        # For hook/ending segments, the base query is usually fine
        if segment_type in ("hook", "ending"):
            return base_query

        # Extract 2-3 key topic words from the article title
        import re
        stop = {"a", "an", "the", "and", "or", "is", "are", "was", "were",
                "to", "of", "in", "on", "at", "for", "with", "this", "that",
                "it", "as", "by", "from", "how", "why", "what", "who"}
        title_words = [
            w for w in re.findall(r"[a-zA-Z]+", article_title.lower())
            if w not in stop and len(w) > 3
        ][:3]

        if title_words:
            return f"{' '.join(title_words)} {base_query}"
        return base_query

    async def search_video_clip(
        self, query: str, segment_index: int = 0, exclude_ids: set = None
    ) -> Dict[str, Any]:
        """
        Search Pexels then Pixabay for a unique clip not in exclude_ids.
        """
        empty = {"clip_path": None, "duration": None, "source": "none", "video_id": None}
        exclude_ids = exclude_ids or set()

        if self.pexels_api_key:
            result = await self._search_pexels(query, segment_index, exclude_ids)
            if result["clip_path"]:
                return result

        if self.pixabay_api_key:
            result = await self._search_pixabay(query, segment_index, exclude_ids)
            if result["clip_path"]:
                return result

        return empty

    # ------------------------------------------------------------------
    # Pexels
    # ------------------------------------------------------------------

    async def _search_pexels(
        self, query: str, segment_index: int, exclude_ids: set = None
    ) -> Dict[str, Any]:
        """Search Pexels Videos API, skipping already-used video IDs."""
        exclude_ids = exclude_ids or set()
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": self.pexels_api_key}
        params = {"query": query, "per_page": 15, "orientation": "portrait", "size": "large"}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning(f"[VideoClipAgent] Pexels search failed: {e}")
            return {"clip_path": None, "duration": None, "source": "pexels", "video_id": None}

        videos = data.get("videos", [])
        clip_url, duration, video_id = self._pick_best_pexels_clip(videos, exclude_ids)

        if not clip_url:
            return {"clip_path": None, "duration": None, "source": "pexels", "video_id": None}

        clip_path = await self._download_clip(clip_url, f"pexels_{segment_index}.mp4")
        return {"clip_path": clip_path, "duration": duration, "source": "pexels", "video_id": video_id}

    def _pick_best_pexels_clip(self, videos: List[Dict], exclude_ids: set) -> tuple:
        """Select the best vertical clip, skipping used IDs."""
        for video in videos:
            vid_id = str(video.get("id", ""))
            if vid_id in exclude_ids:
                continue
            duration = video.get("duration", 0)
            if duration < MIN_DURATION_SECONDS:
                continue
            files = video.get("video_files", [])
            for f in sorted(files, key=lambda x: x.get("width", 0), reverse=True):
                w = f.get("width", 0)
                if w >= MIN_WIDTH and f.get("link"):
                    return f["link"], float(duration), vid_id
        return None, None, None

    # ------------------------------------------------------------------
    # Pixabay
    # ------------------------------------------------------------------

    async def _search_pixabay(
        self, query: str, segment_index: int, exclude_ids: set = None
    ) -> Dict[str, Any]:
        """Search Pixabay Videos API, skipping already-used video IDs."""
        exclude_ids = exclude_ids or set()
        url = "https://pixabay.com/api/videos/"
        params = {"key": self.pixabay_api_key, "q": query, "per_page": 15, "video_type": "film"}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning(f"[VideoClipAgent] Pixabay search failed: {e}")
            return {"clip_path": None, "duration": None, "source": "pixabay", "video_id": None}

        hits = data.get("hits", [])
        clip_url, duration, video_id = self._pick_best_pixabay_clip(hits, exclude_ids)

        if not clip_url:
            return {"clip_path": None, "duration": None, "source": "pixabay", "video_id": None}

        clip_path = await self._download_clip(clip_url, f"pixabay_{segment_index}.mp4")
        return {"clip_path": clip_path, "duration": duration, "source": "pixabay", "video_id": video_id}

    def _pick_best_pixabay_clip(self, hits: List[Dict], exclude_ids: set) -> tuple:
        """Select the best clip from Pixabay results, skipping used IDs."""
        for hit in hits:
            vid_id = str(hit.get("id", ""))
            if vid_id in exclude_ids:
                continue
            duration = hit.get("duration", 0)
            if duration < MIN_DURATION_SECONDS:
                continue
            videos = hit.get("videos", {})
            for size_key in ("large", "medium", "small"):
                v = videos.get(size_key, {})
                w = v.get("width", 0)
                if w >= MIN_WIDTH and v.get("url"):
                    return v["url"], float(duration), vid_id
        return None, None, None

    # ------------------------------------------------------------------
    # Download helper
    # ------------------------------------------------------------------

    async def _download_clip(self, url: str, filename: str) -> Optional[Path]:
        """Download a video clip to the clips directory."""
        output_path = self.clips_dir / filename
        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                async with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    with open(output_path, "wb") as f:
                        async for chunk in resp.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
            logger.info(f"[VideoClipAgent] Downloaded clip: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"[VideoClipAgent] Failed to download clip {url}: {e}")
            return None
