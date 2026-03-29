"""
Audio Generator Agent
Generates narration audio using Kokoro TTS
"""
from typing import Dict, Any
from pathlib import Path
from .base_agent import BaseAgent
from tts.generate_audio_refactored import main_generate_audio


class AudioGeneratorAgent(BaseAgent):
    """Agent responsible for generating audio narration"""
    
    def __init__(self):
        super().__init__("AudioGeneratorAgent")
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate audio from script
        
        Expected context:
            - script_path: Path to script JSON
            - audio_dir: Output directory
        
        Returns:
            - audio_files: List of generated audio file paths
        """
        self.log_start("Generating audio narration")
        
        try:
            script_path = Path(context['script_path'])
            audio_dir = Path(context['audio_dir'])
            
            # Generate audio
            audio_files = main_generate_audio(
                script_path=script_path,
                audio_path=audio_dir
            )
            
            self.log_complete(f"Generated {len(audio_files)} audio segments")
            
            return {'audio_files': audio_files}
            
        except Exception as e:
            self.log_error(f"Audio generation failed: {str(e)}")
            raise
