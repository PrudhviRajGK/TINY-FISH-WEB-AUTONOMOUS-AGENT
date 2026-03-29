# TINY-FISH-WEB-AUTONOMOUS-AGENT



> **Powered by TinyFish Web Agent API** — TINY-FISH-WEB-AUTONOMOUS-AGENT doesn't summarize news. It *hunts* it. A fully autonomous pipeline that deploys a real browser agent into the live web, navigates news sites, extracts breaking stories, and publishes vertical video to YouTube Shorts — zero human input required.

---

## The Problem We're Solving

Every day, thousands of viral news moments go uncaptured by creators who lack the time to monitor, script, produce, and publish fast enough to catch the trend wave. Human-run channels require editors, writers, voice artists, and video producers working in sync. By the time a team coordinates, the story is old news.

TINY-FISH-WEB-AUTONOMOUS-AGENT eliminates that bottleneck entirely.

---

## Why This Requires a Real Web Agent

> *If your application can be built without a web agent navigating real websites, it's not a fit.*

TINY-FISH-WEB-AUTONOMOUS-AGENT cannot function without TinyFish. Here's why:

**The news web is not an API.** Economic Times, Reuters, Bloomberg — these are dynamic, JavaScript-rendered pages with paywalls, anti-scraping measures, lazy-loaded content, cookie consent popups, and constantly shifting DOM structures. A static scraper breaks every time the layout changes. A web agent *navigates* — it handles cookie banners, waits for JS rendering, scrolls to load content, and adapts.

**Multi-step agentic workflows, not single requests:**
1. TinyFish navigates to live news RSS feeds and homepage carousels
2. Agent extracts article links while managing pagination and infinite scroll
3. Agent follows each top-ranked link, bypasses soft paywalls where permitted, and reads full article body
4. Agent detects named entities (people, organizations, locations) in context — not just keyword matching
5. All state is managed session-by-session across different domains, headers, and redirect chains

This is genuine browser infrastructure labor — the kind that currently costs media companies hours of manual curation daily.

---

## Live Demo

```
✓ Video ID : isuGi9gZM5c
✓ URL      : https://youtube.com/shorts/isuGi9gZM5c
```

One pipeline run. One click. Live on YouTube Shorts.

---

## Full Autonomous Pipeline

```
TinyFish Web Agent
  → Navigates live news sites (Economic Times, RSS feeds)
  → Handles JS rendering, cookie popups, soft paywalls
  → Extracts trending article links + metadata
        ↓
Trend Scoring Engine (100-point AI system)
  → Recency, keyword density, category multipliers, virality signals
  → Top 3 articles selected per run
        ↓
TinyFish Deep Extraction
  → Follows article links, reads full body content
  → Named entity detection: people, orgs, locations
        ↓
GPT-4 Viral Script Generation
  → HOOK → NEWS → WHY IT MATTERS → KEY FACT → CALL TO ACTION
  → Optimized for 30–36 second retention arcs
        ↓
Hybrid Visual Sourcing
  → Pulls article images directly (TinyFish navigates image assets)
  → DALL-E 3 fallback for missing or low-quality imagery
        ↓
Kokoro TTS Voice Narration
  → Local inference, zero API cost, natural prosody
        ↓
MoviePy Video Assembly
  → 1080×1920 @ 24fps, burned-in subtitles, transitions
        ↓
PIL Thumbnail Generation
  → Bold text overlay, platform-optimized 1280×720 JPEG
        ↓
GPT-4 Metadata Generation
  → SEO title, description, hashtag set
        ↓
YouTube Data API v3 Upload
  → Resumable upload, Shorts-compliant vertical format
  → Live on YouTube in under 4 minutes from trigger
```

---

## Trend Scoring System

Every article is scored out of 100 before selection. Only the top 3 per run proceed to production.

| Component | Max Points | Scoring Logic |
|-----------|-----------|---------------|
| **Recency** | 30 | < 1hr = 30pts · < 6hr = 25pts · < 12hr = 20pts |
| **Keywords** | 40 | AI=10 · IPO=9 · Startup=8 · Funding=8 · Big Tech=7 |
| **Category Multiplier** | 20 | AI ×1.5 · Startup ×1.4 · Tech ×1.3 |
| **Virality Signals** | 10 | Numbers in title, "breaking", "exclusive", "shocking" |

---

## Script Structure

Every video follows a battle-tested viral format tuned for Shorts retention:

```
HOOK          0–3s    "OpenAI just shocked the AI world again..."
THE NEWS      3–13s   "Here's exactly what happened..."
WHY IT MATTERS 13–23s "This changes everything because..."
KEY FACT      23–31s  "The number you cannot ignore..."
CALL TO ACTION 31–36s "Follow for daily business intelligence."
```

---

## Video Specifications

| Property | Value |
|----------|-------|
| Resolution | 1080 × 1920 (9:16 vertical) |
| Format | MP4 — H.264 |
| Frame Rate | 24 FPS |
| Duration | 30–45 seconds |
| Subtitles | Burned-in, centered, word-by-word sync |
| Thumbnail | 1280 × 720 JPEG with bold text overlay |

---

## Project Structure

```
TINY-FISH-WEB-AUTONOMOUS-AGENT/
├── app/
│   ├── agents/
│   │   ├── base_agent.py             # Abstract agent interface
│   │   ├── viral_script_agent.py     # GPT-4 viral script generation
│   │   ├── image_agent.py            # Hybrid sourcing: article imgs + DALL-E 3
│   │   ├── audio_agent.py            # Kokoro TTS narration
│   │   ├── assembly_agent.py         # MoviePy video assembly
│   │   ├── thumbnail_agent.py        # PIL thumbnail generation
│   │   ├── metadata_agent.py         # GPT-4 platform metadata (title, tags, desc)
│   │   ├── publishing_agent.py       # YouTube / Instagram / TikTok / LinkedIn
│   │   ├── coordinator.py            # Pipeline orchestrator
│   │   └── tinyfish_agent.py         # ★ TinyFish web agent integration
│   ├── api/v1/
│   │   ├── automation.py             # POST /automation/run · GET /automation/trending
│   │   ├── videos.py                 # GET /videos/list · POST /videos/generate
│   │   └── upload.py                 # File upload endpoints
│   ├── services/
│   │   ├── news_automation_service.py  # Full automation orchestration
│   │   └── video_service.py            # Manual video generation service
│   └── core/
│       └── config.py                 # Pydantic settings from .env
│
├── content_sources/
│   ├── economic_times_fetcher.py     # RSS parsing + TinyFish article scraping
│   └── trend_analyzer.py             # 100-point trend scoring algorithm
│
├── new-frontend/
│   └── src/
│       ├── features/dashboard/
│       │   ├── AutomationPanel.jsx     # Run automation, view trending articles
│       │   ├── DashboardPage.jsx       # Main orchestration
│       │   ├── DashboardHero.jsx       # Hero section
│       │   ├── PipelineSection.jsx     # Live pipeline status
│       │   └── VideoLibrarySection.jsx # Generated video library
│       └── services/
│           ├── automationApi.js        # Automation API client
│           └── videoApi.js             # Video API client
│
├── resources/
│   ├── scripts/    # Generated JSON scripts
│   ├── images/     # Sourced / DALL-E generated images
│   ├── audio/      # TTS audio segments
│   ├── video/      # Assembled MP4s
│   ├── subtitles/  # SRT files
│   ├── font/       # font.ttf
│   └── intro/      # intro.jpg
│
├── static/videos/  # Videos served to frontend
├── tts/            # Kokoro TTS integration
├── assembly/       # MoviePy assembly scripts
├── imagegen/       # DALL-E image generation
├── .env            # API keys and configuration
└── requirements.txt
```

---

## Tech Stack

### Agent Infrastructure
- **TinyFish Web Agent API** — live web navigation, session management, entity extraction *(required dependency)*

### Backend
- Python 3.10+ · FastAPI · Uvicorn · Pydantic v2

### AI & Generation
- **OpenAI GPT-4** — script writing, platform metadata generation
- **OpenAI DALL-E 3** — AI image generation fallback
- **Kokoro TTS** — local voice narration (no API cost per run)

### Video Processing
- **MoviePy** — video assembly, subtitle burning
- **PIL / Pillow** — thumbnail generation
- **pysrt** — SRT subtitle generation

### Content Sourcing
- **feedparser** — RSS feed parsing
- **BeautifulSoup4** — article content scraping
- **Economic Times RSS** — 3 feeds monitored continuously

### Publishing
- **YouTube Data API v3** — resumable upload for Shorts
- **Instagram Graph API** — Reels (configured, ready)
- **TikTok API** — configured
- **LinkedIn API** — configured

### Frontend
- React 18 + Vite · TailwindCSS · Dark theme dashboard

---

## Setup

### 1. Clone and install

```bash
git clone <repo-url>
cd TINY-FISH-WEB-AUTONOMOUS-AGENT
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your keys:

```env
OPENAI_API_KEY=sk-proj-...
TINYFISH_API_KEY=sk-tinyfish-...        # Required — pipeline will not run without this
YOUTUBE_API_KEY=AIza...
YOUTUBE_ACCESS_TOKEN=ya29...
```

> **Note:** The `TINYFISH_API_KEY` is a hard dependency. TINY-FISH-WEB-AUTONOMOUS-AGENT uses TinyFish to navigate live news websites, extract full article content, and detect named entities. Without it, the web agent cannot run.

### 3. Install frontend

```bash
cd new-frontend
npm install
```

---

## Running the Project

**Terminal 1 — Backend:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd new-frontend
npm run dev
```

Open: **http://localhost:5173**

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/automation/run` | Trigger full autonomous pipeline |
| `GET` | `/api/v1/automation/status` | Get current pipeline status |
| `GET` | `/api/v1/automation/trending` | Top trending articles with trend scores |
| `GET` | `/api/v1/automation/articles` | Latest articles from monitored feeds |
| `POST` | `/api/v1/automation/test` | Test run with 1 article |
| `GET` | `/api/v1/videos/list` | List all generated videos |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger interactive docs |

### Trigger automation via curl

```bash
curl -X POST http://localhost:8000/api/v1/automation/run \
  -H "Content-Type: application/json" \
  -d '{"top_n": 3, "auto_publish": true}'
```

### Check pipeline status

```bash
curl http://localhost:8000/api/v1/automation/status
```

---

## Using the Dashboard

1. Open **http://localhost:5173**
2. Click **Refresh** in the Automation Panel to fetch trending articles
3. Articles appear ranked by trend score with matched keyword highlights
4. Set the number of articles to process (1–5) and toggle Auto-Publish
5. Click **Run Automation**
6. Watch the live pipeline progress in real time
7. Generated videos appear automatically in the video library

---

## YouTube OAuth Token Refresh

The YouTube access token (`ya29...`) expires every hour. Refresh it with:

```bash
python get_youtube_token.py
```

Follow the browser prompt, paste the authorization code, and the new token is saved to `.env` automatically.

---

## Manual Publishing

To publish an existing video without running the full pipeline:

```bash
python publish_now.py
```

Edit `publish_now.py` to point to any video in `static/videos/`.

---

## Verification

```bash
python verify_setup.py       # Check imports, API keys, directory structure
python test_end_to_end.py    # Run full 10-test integration suite
```

Expected output:
```
TOTAL: 10/10 tests passed (100%)
🎉 ALL TESTS PASSED! APPLICATION IS READY!
```

---

## RSS Feeds Monitored

| Feed | URL |
|------|-----|
| Main | `https://economictimes.indiatimes.com/rssfeedsdefault.cms` |
| Tech | `https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms` |
| Business | `https://economictimes.indiatimes.com/news/rssfeeds/1715249553.cms` |

RSS feeds are cached for 5 minutes. Full article content is fetched lazily via TinyFish — only for the top-ranked articles, not all 50+ candidates.

---

## Business Model Potential

TINY-FISH-WEB-AUTONOMOUS-AGENT is infrastructure for the creator economy's next wave:

- **SaaS tier**: Channels pay per video generated — $3–5/video at scale
- **White-label**: News agencies and media houses license TINY-FISH-WEB-AUTONOMOUS-AGENT to automate their Shorts operations
- **Multi-platform**: One pipeline run → YouTube Shorts + Instagram Reels + TikTok simultaneously
- **Vertical expansion**: Finance, sports, politics — each as a separately tuned scoring + script system
- **Enterprise**: Internal communications teams generating executive briefing videos from internal news feeds

The total addressable market is every creator, brand, and media company that needs to publish faster than human production allows.

---

## What Makes This Genuinely Agentic

Most "AI agent" demos are thin wrappers: a chat UI over a database, a summarizer with a button. TINY-FISH-WEB-AUTONOMOUS-AGENT is different in three measurable ways:

**1. It operates on the live, uncontrolled web.** TinyFish navigates real news pages — handling cookie consent flows, lazy-loaded JavaScript content, dynamic DOM structures, and session state — the exact challenges that make real web automation hard.

**2. The workflow is multi-step and stateful.** The agent doesn't make one API call. It navigates to an index, extracts candidate links, scores them, follows the top links to full article pages, extracts entities, and hands structured data downstream — all in a single pipeline execution.

**3. It produces a real, published artifact.** The output isn't a JSON blob or a UI preview. It's a video, live on YouTube Shorts, discoverable by millions of people. That's the definition of an agent that "goes out into the world and performs labor."

---
