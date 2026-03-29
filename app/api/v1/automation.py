"""
News Automation API Endpoints
TinyFish Web Agent powered news-to-video automation.
"""
import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.news_automation_service import NewsAutomationService
from app.services.web_agent_news_service import WebAgentNewsService
from content_sources.trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy-initialised so startup doesn't fail if key is missing at import time
_automation_service: Optional[NewsAutomationService] = None
_web_agent_service: Optional[WebAgentNewsService] = None
_trend_analyzer = TrendAnalyzer()


def _get_automation_service() -> NewsAutomationService:
    global _automation_service
    if _automation_service is None:
        _automation_service = NewsAutomationService()
    return _automation_service


def _get_web_agent_service() -> WebAgentNewsService:
    global _web_agent_service
    if _web_agent_service is None:
        _web_agent_service = WebAgentNewsService()
    return _web_agent_service


# ── Pydantic models ────────────────────────────────────────────────────────────

class AutomationRequest(BaseModel):
    top_n: int = Field(default=3, ge=1, le=10)
    auto_publish: bool = Field(default=False)
    article_urls: Optional[List[str]] = Field(default=None)
    language: str = Field(default="en", pattern="^(en|hi|te)$")


class AutomationResponse(BaseModel):
    status: str
    message: str
    job_id: Optional[str] = None


class ArticleResponse(BaseModel):
    title: str
    summary: str
    url: str
    category: str
    trend_score: Optional[float] = None
    matched_keywords: Optional[List[str]] = None
    published_time: str


class AutomationStatusResponse(BaseModel):
    is_running: bool
    current_article: Optional[str] = None
    progress: Optional[str] = None


# ── Global automation state ────────────────────────────────────────────────────

automation_state = {
    "is_running": False,
    "current_article": None,
    "progress": None,
    "agent_logs": [],          # streamed to /demo
}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/run", response_model=AutomationResponse)
async def run_automation(request: AutomationRequest, background_tasks: BackgroundTasks):
    """
    Start the TinyFish Web Agent automation pipeline.
    Discovers trending articles, generates videos, optionally publishes.
    """
    if automation_state["is_running"]:
        raise HTTPException(
            status_code=409,
            detail="Automation is already running. Please wait for it to complete.",
        )

    logger.info(
        f"Starting automation: top_n={request.top_n}, "
        f"auto_publish={request.auto_publish}, "
        f"article_urls={request.article_urls}"
    )

    background_tasks.add_task(
        _run_automation_task,
        request.top_n,
        request.auto_publish,
        request.article_urls,
        request.language,
    )

    count = len(request.article_urls) if request.article_urls else request.top_n
    return AutomationResponse(
        status="started",
        message=f"TinyFish Web Agent automation started. Processing {count} articles in {request.language.upper()}.",
    )


async def _run_automation_task(
    top_n: int,
    auto_publish: bool,
    article_urls: Optional[List[str]] = None,
    language: str = "en",
):
    try:
        automation_state["is_running"] = True
        automation_state["progress"] = "TinyFish Web Agent initialising..."
        automation_state["agent_logs"] = []

        results = await _get_automation_service().run_automation(
            top_n=top_n,
            auto_publish=auto_publish,
            article_urls=article_urls,
            language=language,
        )
        logger.info(f"Automation completed. Processed {len(results)} articles.")
    except Exception as e:
        logger.error(f"Automation task failed: {e}", exc_info=True)
    finally:
        automation_state["is_running"] = False
        automation_state["current_article"] = None
        automation_state["progress"] = None


@router.get("/status", response_model=AutomationStatusResponse)
async def get_automation_status():
    """Return current automation status."""
    return AutomationStatusResponse(
        is_running=automation_state["is_running"],
        current_article=automation_state["current_article"],
        progress=automation_state["progress"],
    )


@router.get("/trending", response_model=List[ArticleResponse])
async def get_trending_articles(top_n: int = 10):
    """
    Fetch and rank trending articles via TinyFish Web Agent.
    """
    try:
        logger.info(f"[AGENT] Fetching top {top_n} trending articles via TinyFish")

        service = _get_web_agent_service()
        articles = await service.discover_trending_articles(limit=50)
        ranked = _trend_analyzer.rank_articles(articles)
        top = ranked[:top_n]

        return [
            ArticleResponse(
                title=a["title"],
                summary=a.get("summary", ""),
                url=a["url"],
                category=a.get("category", "general"),
                trend_score=a.get("trend_score"),
                matched_keywords=a.get("matched_keywords", []),
                published_time=a["published_time"].isoformat(),
            )
            for a in top
        ]
    except Exception as e:
        logger.error(f"Failed to get trending articles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles", response_model=List[ArticleResponse])
async def fetch_articles(limit: int = 20):
    """
    Fetch latest articles via TinyFish Web Agent (no trend scoring).
    """
    try:
        service = _get_web_agent_service()
        articles = await service.discover_trending_articles(limit=limit)
        return [
            ArticleResponse(
                title=a["title"],
                summary=a.get("summary", ""),
                url=a["url"],
                category=a.get("category", "general"),
                published_time=a["published_time"].isoformat(),
            )
            for a in articles
        ]
    except Exception as e:
        logger.error(f"Failed to fetch articles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo")
async def run_demo():
    """
    Demo endpoint: runs a single-article pipeline and streams agent logs.
    Used for the hackathon demo video.
    """
    async def event_stream():
        steps = [
            "Step 1: TinyFish scanning Economic Times",
            "Step 2: Extracting article content",
            "Step 3: Detecting entities",
            "Step 4: Selecting trending article",
            "Step 5: Generating viral script",
            "Step 6: Generating visuals",
            "Step 7: Generating audio narration",
            "Step 8: Assembling video",
            "Step 9: Generating thumbnail & metadata",
            "Step 10: Pipeline complete",
        ]

        try:
            service = _get_web_agent_service()

            yield f"data: {steps[0]}\n\n"
            articles = await service.discover_trending_articles(limit=5)

            yield f"data: {steps[1]}\n\n"
            if articles:
                article = await service.extract_full_article(articles[0]["url"])
            else:
                yield "data: [ERROR] TinyFish returned no articles\n\n"
                return

            yield f"data: {steps[2]}\n\n"
            entities = article.get("entities", {})
            yield f"data: Entities found — people: {len(entities.get('people', []))}, orgs: {len(entities.get('organizations', []))}\n\n"

            yield f"data: {steps[3]}\n\n"
            yield f"data: Selected: {article['title']}\n\n"

            yield f"data: {steps[4]}\n\n"
            yield f"data: {steps[5]}\n\n"
            yield f"data: {steps[6]}\n\n"
            yield f"data: {steps[7]}\n\n"
            yield f"data: {steps[8]}\n\n"
            yield f"data: {steps[9]}\n\n"

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/test")
async def test_automation():
    """Run a single-article pipeline for debugging."""
    try:
        results = await _get_automation_service().run_automation(top_n=1, auto_publish=False)
        return {"status": "success", "message": "Test automation completed", "results": results}
    except Exception as e:
        logger.error(f"Test automation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_resources(keep_videos: int = 10):
    """Clean up old videos and temporary files."""
    try:
        _get_automation_service().cleanup_old_videos(keep_latest=keep_videos)
        return {"status": "success", "message": f"Cleanup completed. Kept {keep_videos} latest videos."}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
