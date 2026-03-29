"""
News Automation Service
Fully automated TinyFish Web Agent → news-to-video pipeline.
TinyFish is the ONLY source of live web content. No RSS fallback.
"""
import logging
import asyncio
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings
from app.services.web_agent_news_service import WebAgentNewsService
from content_sources.trend_analyzer import TrendAnalyzer
from app.agents.viral_script_agent import ViralScriptAgent
from app.agents.visual_planner_agent import VisualPlannerAgent
from app.agents.video_clip_agent import VideoClipAgent
from app.agents.image_agent import ImageGeneratorAgent
from app.agents.motion_assembly_agent import MotionAssemblyAgent
from app.agents.elevenlabs_tts_agent import ElevenLabsTTSAgent
from app.agents.audio_agent import AudioGeneratorAgent  # Kokoro fallback
from app.agents.thumbnail_agent import ThumbnailAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.publishing_agent import PublishingAgent

logger = logging.getLogger(__name__)


class NewsAutomationService:
    """
    Automated news-to-video pipeline.
    Data acquisition is exclusively handled by WebAgentNewsService (TinyFish).
    """

    def __init__(self):
        # TinyFish-powered web agent — required dependency
        self.web_agent_service = WebAgentNewsService()
        self.trend_analyzer = TrendAnalyzer()
        self.viral_script_agent = ViralScriptAgent(api_key=settings.OPENAI_API_KEY)
        # Motion visual pipeline
        self.visual_planner = VisualPlannerAgent(api_key=settings.OPENAI_API_KEY)
        self.video_clip_agent = VideoClipAgent(
            pexels_api_key=settings.PEXELS_API_KEY,
            pixabay_api_key=settings.PIXABAY_API_KEY,
            clips_dir=settings.CLIPS_DIR,
        )
        self.image_agent = ImageGeneratorAgent(api_key=settings.OPENAI_API_KEY)
        # ElevenLabs is primary TTS; Kokoro fallback is handled inside ElevenLabsTTSAgent
        if settings.ELEVENLABS_API_KEY:
            self.audio_agent = ElevenLabsTTSAgent(
                api_key=settings.ELEVENLABS_API_KEY,
                audio_dir=settings.AUDIO_DIR,
            )
        else:
            logger.warning("[TTS] ELEVENLABS_API_KEY not set — using Kokoro TTS only")
            self.audio_agent = AudioGeneratorAgent()
        self.assembly_agent = MotionAssemblyAgent()
        self.thumbnail_agent = ThumbnailAgent()
        self.metadata_agent = MetadataAgent(api_key=settings.OPENAI_API_KEY)
        self.publishing_agent = PublishingAgent(
            openai_api_key=settings.OPENAI_API_KEY,
            youtube_credentials={
                "api_key": settings.YOUTUBE_API_KEY,
                "access_token": settings.YOUTUBE_ACCESS_TOKEN,
            },
        )

    async def run_automation(
        self,
        top_n: int = 3,
        auto_publish: bool = False,
        article_urls: Optional[List[str]] = None,
        language: str = "en",
    ) -> List[Dict[str, Any]]:
        """
        Run the full TinyFish → video pipeline.

        Flow:
          TinyFish discovers articles → trend scoring → top N selected
          → for each: script → images → audio → assembly → thumbnail → metadata → publish
        """
        logger.info("=" * 60)
        logger.info("STARTING TINYFISH WEB AGENT NEWS-TO-VIDEO PIPELINE")
        logger.info(f"Language: {language.upper()}")
        logger.info("=" * 60)

        results = []

        try:
            # ── Step 1: Article acquisition via TinyFish ──────────────
            if article_urls:
                logger.info(f"\n[STEP 1] TinyFish extracting {len(article_urls)} specific articles...")
                top_articles = []
                for url in article_urls:
                    logger.info(f"[AGENT] Extracting article: {url}")
                    article = await self.web_agent_service.extract_full_article(url)
                    # Provide a default trend_score so _process_article doesn't KeyError
                    article.setdefault("trend_score", 0.0)
                    top_articles.append(article)
                logger.info(f"✓ TinyFish extracted {len(top_articles)} articles")

            else:
                logger.info("\n[STEP 1] TinyFish scanning news sites for trending articles...")
                articles = await self.web_agent_service.discover_trending_articles(limit=20)
                logger.info(f"✓ TinyFish discovered {len(articles)} articles")

                # ── Step 2: Trend scoring ──────────────────────────────
                logger.info("\n[STEP 2] Scoring articles by trend potential...")
                top_articles = self.trend_analyzer.select_top_articles(articles, count=top_n)
                logger.info(f"✓ Selected top {len(top_articles)} trending articles")

                # ── Step 3: Enrich top articles with full content ──────
                logger.info("\n[STEP 3] TinyFish extracting full content for top articles...")
                top_articles = await self.web_agent_service.enrich_articles(top_articles)
                logger.info(f"✓ Full content extracted for {len(top_articles)} articles")

            # ── Step 4: Process each article through the video pipeline ─
            for i, article in enumerate(top_articles, 1):
                logger.info(f"\n{'=' * 60}")
                logger.info(f"PROCESSING ARTICLE {i}/{len(top_articles)}")
                logger.info(f"Title: {article['title']}")
                if article.get("trend_score"):
                    logger.info(f"Trend Score: {article['trend_score']:.2f}")
                logger.info(f"{'=' * 60}")

                try:
                    result = await self._process_article(article, auto_publish, language)
                    results.append(result)
                    logger.info(f"✓ Article {i} processed successfully")
                except Exception as e:
                    logger.error(f"✗ Failed to process article {i}: {e}")
                    results.append({
                        "success": False,
                        "article": article.get("title", ""),
                        "error": str(e),
                    })

            # ── Summary ───────────────────────────────────────────────
            logger.info("\n" + "=" * 60)
            logger.info("TINYFISH PIPELINE COMPLETE")
            logger.info("=" * 60)
            successful = sum(1 for r in results if r.get("success"))
            logger.info(f"✓ Successfully processed: {successful}/{len(results)}")
            logger.info(f"✗ Failed: {len(results) - successful}/{len(results)}")

            return results

        except Exception as e:
            logger.error(f"Automation pipeline failed: {e}", exc_info=True)
            raise

    async def _process_article(self, article: Dict[str, Any], auto_publish: bool, language: str = "en") -> Dict[str, Any]:
        """Process a single article through the full video generation pipeline."""

        from app.api.v1.automation import automation_state
        automation_state["current_article"] = article["title"]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_id = f"tf_{timestamp}"

        self._cleanup_temp_files()

        context = {
            "article": article,
            "title": article["title"],
            "content": article.get("content", ""),
            "summary": article.get("summary", ""),
            "category": article.get("category", "general"),
            "images": article.get("images", []),
            "extracted_images": article.get("images", []),  # for ImageAgent
            "video_id": video_id,
            "trend_score": article.get("trend_score", 0.0),
            "language": language,
        }

        # 1 — Viral script
        automation_state["progress"] = "Generating viral script..."
        logger.info("  [1/8] Generating viral script...")
        script_result = await self.viral_script_agent.execute(context)
        context.update(script_result)
        logger.info("  ✓ Viral script generated")

        # 2 — Visual plan (query per segment)
        automation_state["progress"] = "Planning visuals..."
        logger.info("  [2/8] Building visual plan...")
        plan_result = await self.visual_planner.execute(context)
        context.update(plan_result)
        logger.info(f"  ✓ Visual plan: {len(context.get('visual_plan', []))} queries")

        # 3 — Stock video clips
        automation_state["progress"] = "Searching for video clips..."
        logger.info("  [3/8] Searching stock video clips...")
        clip_result = await self.video_clip_agent.execute(context)
        context.update(clip_result)
        clips_found = sum(1 for r in context.get("clip_results", []) if r.get("clip_path"))
        logger.info(f"  ✓ Clips found: {clips_found}/{len(context.get('clip_results', []))}")

        # 4 — Image fallback for segments without clips
        automation_state["progress"] = "Generating fallback images..."
        logger.info("  [4/8] Generating fallback images for remaining segments...")
        context["script_path"] = self._save_script(context["script"], video_id)
        context["image_folder"] = settings.IMAGES_DIR
        context["images_dir"] = settings.IMAGES_DIR
        image_result = await self.image_agent.execute(context)
        context.update(image_result)
        logger.info("  ✓ Fallback images ready")

        # 5 — Audio
        automation_state["progress"] = "Generating audio narration..."
        logger.info("  [5/8] Generating audio narration...")
        context["audio_folder"] = settings.AUDIO_DIR
        context["audio_dir"] = settings.AUDIO_DIR
        audio_result = await self.audio_agent.execute(context)
        context.update(audio_result)
        logger.info("  ✓ Audio generated")

        # 6 — Motion assembly (clips + Ken Burns)
        automation_state["progress"] = "Assembling video with motion visuals..."
        logger.info("  [6/8] Assembling video with motion visuals...")
        context["output_file"] = settings.VIDEO_OUTPUT_DIR / f"{video_id}.mp4"
        # Choose font based on language
        if language == "hi" and settings.HINDI_FONT_PATH.exists():
            context["font_path"] = settings.HINDI_FONT_PATH
        elif language == "te" and settings.TELUGU_FONT_PATH.exists():
            context["font_path"] = settings.TELUGU_FONT_PATH
        else:
            context["font_path"] = settings.FONT_PATH
        context["intro_image_path"] = settings.INTRO_IMAGE_PATH
        context["subtitle_path"] = settings.SUBTITLE_OUTPUT_DIR / f"{video_id}.srt"
        context["with_subtitles"] = True
        context["fps"] = 24
        assembly_result = await self.assembly_agent.execute(context)
        context.update(assembly_result)
        logger.info("  ✓ Video assembled")

        # Copy to static dir
        static_video_dir = settings.STATIC_DIR / "videos"
        static_video_dir.mkdir(parents=True, exist_ok=True)
        static_video_path = static_video_dir / f"{video_id}.mp4"
        if context["video_path"].exists():
            shutil.copy2(context["video_path"], static_video_path)

        # 7 — Thumbnail
        automation_state["progress"] = "Generating thumbnail..."
        logger.info("  [7/8] Generating thumbnail...")
        context["key_visual_path"] = context["image_paths"][0] if context.get("image_paths") else None
        context["output_path"] = settings.VIDEO_OUTPUT_DIR / f"{video_id}_thumbnail.jpg"
        thumbnail_result = await self.thumbnail_agent.execute(context)
        context.update(thumbnail_result)
        logger.info("  ✓ Thumbnail generated")

        static_thumbnail_path = settings.STATIC_DIR / "videos" / f"{video_id}_thumbnail.jpg"
        if context["thumbnail_path"].exists():
            shutil.copy2(context["thumbnail_path"], static_thumbnail_path)

        # 8 — Metadata (was 6)
        automation_state["progress"] = "Generating metadata..."
        logger.info("  [8/8] Generating metadata...")
        metadata_result = await self.metadata_agent.execute(context)
        context.update(metadata_result)
        logger.info("  ✓ Metadata generated")

        # 9 — Publish
        if auto_publish:
            automation_state["progress"] = "Publishing to platforms..."
            logger.info("  [9/8] Publishing to platforms...")
            context["platforms"] = ["youtube"]
            context["pregenerated_metadata"] = context.get("metadata")
            publish_result = await self.publishing_agent.execute(context)
            context.update(publish_result)
            logger.info("  ✓ Published successfully")
        else:
            logger.info("  [9/8] Skipping publish (auto_publish=False)")

        return {
            "success": True,
            "article_title": article["title"],
            "video_id": video_id,
            "video_path": str(context["video_path"]),
            "thumbnail_path": str(context["thumbnail_path"]),
            "metadata": context["metadata"],
            "trend_score": article.get("trend_score", 0.0),
            "published": auto_publish,
            "publish_results": context.get("published", {}) if auto_publish else None,
        }

    def _save_script(self, script: Dict[str, Any], video_id: str) -> Path:
        import json
        script_path = settings.SCRIPT_DIR / f"{video_id}_script.json"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        with open(script_path, "w") as f:
            json.dump(script, f, indent=2)
        return script_path

    def _cleanup_temp_files(self):
        logger.info("Cleaning up temporary files...")
        cleanup_dirs = [
            settings.IMAGES_DIR,
            settings.AUDIO_DIR,
            settings.SCRIPT_DIR,
            settings.SUBTITLE_OUTPUT_DIR,
        ]
        files_removed = 0
        for directory in cleanup_dirs:
            if not directory.exists():
                continue
            for file_path in directory.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        files_removed += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")
        logger.info(f"✓ Cleaned up {files_removed} temporary files")

    def cleanup_old_videos(self, keep_latest: int = 10):
        logger.info(f"Cleaning up old videos (keeping latest {keep_latest})...")
        for directory in [settings.VIDEO_OUTPUT_DIR, settings.STATIC_DIR / "videos"]:
            if not directory.exists():
                continue
            video_files = [
                (p, p.stat().st_mtime)
                for p in directory.iterdir()
                if p.is_file() and p.suffix.lower() in (".mp4", ".webm", ".mov", ".avi")
            ]
            video_files.sort(key=lambda x: x[1], reverse=True)
            for file_path, _ in video_files[keep_latest:]:
                try:
                    file_path.unlink()
                    thumb = file_path.with_name(file_path.stem + "_thumbnail.jpg")
                    if thumb.exists():
                        thumb.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")
        logger.info("✓ Old videos cleaned up")
