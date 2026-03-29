"""
Coordinator Agent
Orchestrates the entire video generation pipeline
"""
import logging
from typing import Dict, Any
from pathlib import Path
from .base_agent import BaseAgent
from .tinyfish_agent import TinyFishDataAgent
from .script_agent import ScriptGeneratorAgent
from .image_agent import ImageGeneratorAgent
from .audio_agent import AudioGeneratorAgent
from .assembly_agent import VideoAssemblyAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """Main coordinator that orchestrates all agents"""
    
    def __init__(
        self,
        openai_api_key: str,
        tinyfish_api_key: str = None,
        tinyfish_base_url: str = "https://api.tinyfish.io/v1"
    ):
        super().__init__("CoordinatorAgent")
        
        # Initialize all agents
        self.tinyfish_agent = TinyFishDataAgent(
            api_key=tinyfish_api_key,
            base_url=tinyfish_base_url
        )
        self.script_agent = ScriptGeneratorAgent(api_key=openai_api_key)
        self.image_agent = ImageGeneratorAgent(api_key=openai_api_key)
        self.audio_agent = AudioGeneratorAgent()
        self.assembly_agent = VideoAssemblyAgent()
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete video generation pipeline
        
        Expected context:
            - topic: Video topic
            - duration: Video duration
            - key_points: Optional key points
            - article_url: Optional article URL
            - use_tinyfish: Boolean flag
            - output_paths: Dict with all required paths
        
        Returns:
            - video_path: Path to final video
            - metadata: Video metadata
        """
        self.log_start("Starting video generation pipeline")
        
        try:
            # Stage 1: TinyFish Data Extraction (if enabled)
            if context.get('use_tinyfish'):
                self.log_progress("Stage 1: Fetching article data from TinyFish")
                tinyfish_result = await self.tinyfish_agent.execute(context)
                context.update(tinyfish_result)
            else:
                self.log_progress("Stage 1: Skipping TinyFish (traditional mode)")
                context.update({
                    'title': context['topic'],
                    'key_points': context.get('key_points', []),
                    'extracted_images': []
                })
            
            # Stage 2: Script Generation
            self.log_progress("Stage 2: Generating video script")
            script_result = await self.script_agent.execute(context)
            context.update(script_result)
            
            # Stage 3: Image Generation/Sourcing
            self.log_progress("Stage 3: Generating/sourcing images")
            image_result = await self.image_agent.execute(context)
            context.update(image_result)
            
            # Stage 4: Audio Generation
            self.log_progress("Stage 4: Generating audio narration")
            audio_result = await self.audio_agent.execute(context)
            context.update(audio_result)
            
            # Stage 5: Video Assembly
            self.log_progress("Stage 5: Assembling final video")
            assembly_result = await self.assembly_agent.execute(context)
            context.update(assembly_result)
            
            self.log_complete("Video generation pipeline completed successfully")
            
            return {
                'success': True,
                'video_path': context['video_path'],
                'subtitle_path': context.get('subtitle_path'),
                'metadata': {
                    'title': context.get('title'),
                    'duration': context.get('duration'),
                    'topics': context.get('topics', []),
                    'key_points': context.get('key_points', [])
                }
            }
            
        except Exception as e:
            self.log_error(f"Pipeline execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
