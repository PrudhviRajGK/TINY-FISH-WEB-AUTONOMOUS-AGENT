"""
Video Generation Service
Orchestrates the entire video generation pipeline with TinyFish integration
All paths are dynamically resolved from configuration
"""
import logging
import json
import time
import re
import shutil
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import BackgroundTasks

from app.schemas.video import VideoGenerationRequest, VideoGenerationResponse
from app.core.config import settings
from imagegen.generate_script import VideoScriptGenerator
from imagegen.gen_img_openai_refactored import main_generate_images, generate_openai_image, download_image
from tts.generate_audio_refactored import main_generate_audio
from assembly.scripts.assembly_video_refactored import create_video, create_complete_srt

logger = logging.getLogger(__name__)


class TinyFishClient:
    """Client for TinyFish API integration"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.tinyfish.io/v1"):
        self.api_key = api_key
        self.base_url = base_url
    
    async def fetch_article(self, url: str) -> Dict[str, Any]:
        """Fetch article content from TinyFish API"""
        logger.info(f"Fetching article from TinyFish: {url}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/extract",
                    json={"url": url},
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning(f"TinyFish API call failed: {str(e)}, using fallback")
                return self._create_fallback_data(url)
    
    async def search_articles(self, query: str) -> List[Dict[str, Any]]:
        """Search for articles via TinyFish API"""
        logger.info(f"Searching TinyFish for: {query}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={"q": query, "limit": 5},
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get('results', [])
            except Exception as e:
                logger.warning(f"TinyFish search failed: {str(e)}")
                return []
    
    def _create_fallback_data(self, url: str) -> Dict[str, Any]:
        """Create fallback data when API is unavailable"""
        return {
            'article_id': 'fallback',
            'title': 'Article Content',
            'url': url,
            'summary': 'Content extracted from article',
            'topics': [],
            'key_points': [],
            'entities': {},
            'content_sections': [],
            'images': [],
            'metadata': {}
        }


class VideoGenerationService:
    """Service for generating videos with TinyFish integration"""
    
    def __init__(self):
        self.script_generator = VideoScriptGenerator(api_key=settings.OPENAI_API_KEY)
        self.tinyfish_client = TinyFishClient(
            api_key=settings.TINYFISH_API_KEY,
            base_url=settings.TINYFISH_BASE_URL
        )
    
    def _clean_directory(self, folder_path: Path):
        """Clean all files in a directory"""
        if not folder_path.exists():
            return
        
        for item in folder_path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                logger.warning(f"Failed to delete {item}: {e}")
    
    def _generate_video_filename(self, topic: str) -> str:
        """Generate a clean filename from topic"""
        clean_topic = re.sub(r"[^A-Za-z0-9]", "_", topic)[:30]
        timestamp = int(time.time())
        return f"{clean_topic}_{timestamp}.mp4"
    
    async def generate_video_async(
        self,
        request: VideoGenerationRequest,
        background_tasks: BackgroundTasks
    ) -> VideoGenerationResponse:
        """
        Generate video asynchronously
        Returns immediately with success status, actual generation happens in background
        """
        try:
            # Generate video filename
            video_filename = self._generate_video_filename(request.topic)
            
            # Add background task
            background_tasks.add_task(
                self._generate_video_task,
                request,
                video_filename
            )
            
            return VideoGenerationResponse(
                success=True,
                message="Video generation started. This may take several minutes.",
                video_path=f"/static/videos/{video_filename}",
                video_filename=video_filename
            )
            
        except Exception as e:
            logger.error(f"Failed to start video generation: {str(e)}", exc_info=True)
            return VideoGenerationResponse(
                success=False,
                message="Failed to start video generation",
                error=str(e)
            )
    
    def _generate_video_task(self, request: VideoGenerationRequest, video_filename: str):
        """
        Background task for video generation with TinyFish integration
        This is the main pipeline that orchestrates all steps
        All paths are dynamically resolved from configuration
        """
        try:
            logger.info(f"Starting video generation for: {request.topic}")
            
            # Step 1: Clean working directories
            logger.info("Cleaning working directories...")
            self._clean_directory(settings.IMAGES_DIR)
            self._clean_directory(settings.AUDIO_DIR)
            
            # Step 2: Fetch article data from TinyFish (if enabled)
            article_data = None
            extracted_images = []
            
            if request.use_tinyfish and request.article_url:
                logger.info("Fetching article data from TinyFish...")
                import asyncio
                article_data = asyncio.run(self.tinyfish_client.fetch_article(request.article_url))
                extracted_images = article_data.get('images', [])
                
                # Override topic and key_points with article data
                if article_data.get('title'):
                    request.topic = article_data['title']
                if article_data.get('key_points'):
                    request.key_points = article_data['key_points']
                
                logger.info(f"TinyFish extracted: {len(extracted_images)} images, {len(request.key_points)} key points")
            
            elif request.use_tinyfish and not request.article_url:
                logger.info("Searching TinyFish for articles...")
                import asyncio
                search_results = asyncio.run(self.tinyfish_client.search_articles(request.topic))
                if search_results:
                    article_data = search_results[0]
                    extracted_images = article_data.get('images', [])
                    if article_data.get('key_points'):
                        request.key_points = article_data['key_points']
            
            # Step 3: Generate script
            logger.info("Generating script...")
            if article_data:
                # Generate script from article data
                script = self._generate_script_from_article(
                    article_data=article_data,
                    duration=request.duration
                )
            else:
                # Use original script generation
                script = self.script_generator.generate_script(
                    topic=request.topic,
                    duration=request.duration,
                    key_points=request.key_points if request.key_points else None
                )
            
            # Save script
            script_path = settings.SCRIPT_DIR / "script.json"
            script_path.parent.mkdir(parents=True, exist_ok=True)
            self.script_generator.save_script(script, str(script_path))
            logger.info(f"Script saved to: {script_path}")
            
            # Step 4: Generate/source images (hybrid approach)
            logger.info("Generating/sourcing images...")
            self._generate_hybrid_images(
                script=script,
                extracted_images=extracted_images,
                images_dir=settings.IMAGES_DIR
            )
            logger.info("Images generated successfully")
            
            # Step 5: Generate audio
            logger.info("Generating audio...")
            main_generate_audio(
                script_path=script_path,
                audio_path=settings.AUDIO_DIR
            )
            logger.info("Audio generated successfully")
            
            # Step 6: Generate subtitles
            logger.info("Generating subtitles...")
            clean_topic = re.sub(r"[^A-Za-z0-9]", "_", request.topic)[:30]
            srt_path = settings.SUBTITLE_OUTPUT_DIR / f"{clean_topic}.srt"
            create_complete_srt(
                script_folder=script_path,
                audio_file_folder=settings.AUDIO_DIR,
                outfile_path=srt_path,
                chunk_size=settings.DEFAULT_CHUNK_SIZE
            )
            logger.info(f"Subtitles saved to: {srt_path}")
            
            # Step 7: Assemble video
            logger.info("Assembling video...")
            temp_video_path = settings.VIDEO_OUTPUT_DIR / video_filename
            
            create_video(
                image_folder=settings.IMAGES_DIR,
                audio_folder=settings.AUDIO_DIR,
                script_path=script_path,
                font_path=settings.FONT_PATH,
                output_file=temp_video_path,
                intro_image_path=settings.INTRO_IMAGE_PATH,
                with_subtitles=True,
                fps=settings.DEFAULT_VIDEO_FPS
            )
            
            # Step 8: Copy to static directory
            final_video_path = settings.STATIC_DIR / "videos" / video_filename
            final_video_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(temp_video_path, final_video_path)
            
            logger.info(f"Video generation complete: {video_filename}")
            
        except Exception as e:
            logger.error(f"Video generation task failed: {str(e)}", exc_info=True)
            raise

    
    def _generate_script_from_article(
        self,
        article_data: Dict[str, Any],
        duration: int
    ) -> Dict[str, Any]:
        """Generate script from TinyFish article data"""
        
        title = article_data.get('title', 'Untitled')
        summary = article_data.get('summary', '')
        key_points = article_data.get('key_points', [])
        content_sections = article_data.get('content_sections', [])
        
        # Build content text from sections
        content_text = summary
        for section in content_sections[:3]:  # Use first 3 sections
            content_text += f"\n{section.get('content', '')}"
        
        prompt = f"""Create a {duration}-second video script from this article:

Title: {title}
Summary: {summary}
Key Points: {', '.join(key_points)}
Content: {content_text[:500]}

Generate a JSON script with:
1. audio_script: Array of narration segments with timestamps
2. visual_script: Array of visual descriptions with timestamps

Each segment should be 5-10 seconds. Make it engaging and educational."""
        
        system_prompt = """You are a video script generator. Output JSON with this structure:
{
  "topic": "Title",
  "audio_script": [
    {"timestamp": "00:00", "text": "Narration", "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"}
  ],
  "visual_script": [
    {"timestamp_start": "00:00", "timestamp_end": "00:05", "prompt": "Visual description", "negative_prompt": "Avoid abstract"}
  ]
}"""
        
        response = self.script_generator.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        script_text = response.choices[0].message.content
        
        # Extract JSON
        try:
            script = json.loads(script_text)
        except:
            import re
            json_match = re.search(r'```json\n(.*?)\n```', script_text, re.DOTALL)
            if json_match:
                script = json.loads(json_match.group(1))
            else:
                raise ValueError("Failed to parse script JSON")
        
        script['topic'] = title
        return script
    
    def _generate_hybrid_images(
        self,
        script: Dict[str, Any],
        extracted_images: List[Dict[str, Any]],
        images_dir: Path
    ):
        """Generate images using hybrid approach: article images + AI generation"""
        
        visual_script = script.get('visual_script', [])
        images_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, scene in enumerate(visual_script):
            timestamp = scene.get('timestamp_start', f'{idx:03d}')
            scene_id = timestamp.replace(':', '-')
            output_path = images_dir / f"scene_{scene_id}.jpg"
            
            # Try to use article image first
            if idx < len(extracted_images) and extracted_images[idx].get('url'):
                try:
                    logger.info(f"Using article image for scene {idx}")
                    image_url = extracted_images[idx]['url']
                    download_image(image_url, output_path)
                    continue
                except Exception as e:
                    logger.warning(f"Failed to download article image: {e}, generating AI image")
            
            # Generate with DALL-E
            try:
                logger.info(f"Generating AI image for scene {idx}")
                prompt = scene.get('prompt', '')
                image_urls = generate_openai_image(
                    prompt=prompt,
                    api_key=settings.OPENAI_API_KEY,
                    model="dall-e-3",
                    size="1024x1024"
                )
                
                if image_urls:
                    download_image(image_urls[0], output_path)
                    time.sleep(2.0)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to generate image for scene {idx}: {e}")
