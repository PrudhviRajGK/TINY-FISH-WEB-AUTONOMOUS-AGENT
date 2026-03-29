"""
Video Assembly Agent
Assembles final video from all components
"""
from typing import Dict, Any
from pathlib import Path
from .base_agent import BaseAgent
from assembly.scripts.assembly_video_refactored import create_video, create_complete_srt


class VideoAssemblyAgent(BaseAgent):
    """Agent responsible for assembling the final video"""
    
    def __init__(self):
        super().__init__("VideoAssemblyAgent")
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assemble video from images, audio, and subtitles
        
        Expected context:
            - image_folder: Directory with images
            - audio_folder: Directory with audio
            - script_path: Path to script JSON
            - output_file: Output video path
            - font_path: Font file path
            - intro_image_path: Intro background image
            - subtitle_path: Output subtitle path
            - fps: Frames per second
        
        Returns:
            - video_path: Path to final video
            - subtitle_path: Path to subtitle file
        """
        self.log_start("Assembling final video")
        
        try:
            # Generate subtitles first
            self.log_progress("Generating subtitles...")
            create_complete_srt(
                script_folder=Path(context['script_path']),
                audio_file_folder=Path(context['audio_folder']),
                outfile_path=Path(context['subtitle_path']),
                chunk_size=context.get('chunk_size', 10)
            )
            
            # Assemble video
            self.log_progress("Assembling video with effects...")
            create_video(
                image_folder=Path(context['image_folder']),
                audio_folder=Path(context['audio_folder']),
                script_path=Path(context['script_path']),
                font_path=Path(context['font_path']),
                output_file=Path(context['output_file']),
                intro_image_path=Path(context['intro_image_path']),
                with_subtitles=context.get('with_subtitles', True),
                fps=context.get('fps', 24)
            )
            
            self.log_complete(f"Video assembled: {context['output_file']}")
            
            return {
                'video_path': context['output_file'],
                'subtitle_path': context['subtitle_path']
            }
            
        except Exception as e:
            self.log_error(f"Video assembly failed: {str(e)}")
            raise
