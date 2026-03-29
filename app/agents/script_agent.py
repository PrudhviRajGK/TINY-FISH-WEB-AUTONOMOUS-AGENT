"""
Script Generator Agent
Converts article data or topic into video script
"""
import json
from typing import Dict, Any, List
from pathlib import Path
import openai
from .base_agent import BaseAgent


class ScriptGeneratorAgent(BaseAgent):
    """Agent responsible for generating video scripts"""
    
    def __init__(self, api_key: str):
        super().__init__("ScriptGeneratorAgent")
        self.client = openai.OpenAI(api_key=api_key)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate video script from article data or topic
        
        Expected context:
            - title: Article/video title
            - summary: Optional summary
            - key_points: List of key points
            - content_sections: Optional article sections
            - duration: Target video duration
            - script_path: Output path for script
        
        Returns:
            - script: Complete video script
            - script_path: Path to saved script
        """
        self.log_start("Generating video script")
        
        try:
            title = context.get('title', 'Untitled')
            summary = context.get('summary', '')
            key_points = context.get('key_points', [])
            duration = context.get('duration', 60)
            content_sections = context.get('content_sections', [])
            
            # Build content text
            content_text = summary
            for section in content_sections[:3]:
                content_text += f"\n{section.get('content', '')}"
            
            # Generate script
            script = self._generate_script(
                title=title,
                summary=summary,
                key_points=key_points,
                content_text=content_text[:1000],
                duration=duration
            )
            
            # Save script
            script_path = Path(context.get('script_path', 'script.json'))
            script_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(script_path, 'w') as f:
                json.dump(script, f, indent=2)
            
            self.log_complete(f"Generated script with {len(script['audio_script'])} segments")
            
            return {
                'script': script,
                'script_path': str(script_path)
            }
            
        except Exception as e:
            self.log_error(f"Script generation failed: {str(e)}")
            raise

    
    def _generate_script(
        self,
        title: str,
        summary: str,
        key_points: List[str],
        content_text: str,
        duration: int
    ) -> Dict[str, Any]:
        """Generate script using GPT-4"""
        
        prompt = f"""Create a {duration}-second video script:

Title: {title}
Summary: {summary}
Key Points: {', '.join(key_points) if key_points else 'Cover main topics'}
Content: {content_text}

Generate an engaging video script with:
1. audio_script: Narration segments (5-10 seconds each)
2. visual_script: Visual descriptions for each segment

Make it informative and engaging for social media."""
        
        system_prompt = """You are a video script generator for short-form content. Output JSON:
{
  "topic": "Title",
  "description": "Brief description",
  "audio_script": [
    {
      "timestamp": "00:00",
      "text": "Narration text",
      "speaker": "narrator_male",
      "speed": 1.0,
      "pitch": 1.0,
      "emotion": "informative"
    }
  ],
  "visual_script": [
    {
      "timestamp_start": "00:00",
      "timestamp_end": "00:05",
      "prompt": "Visual description (5 words max)",
      "negative_prompt": "Avoid abstract or complex designs"
    }
  ]
}"""
        
        response = self.client.chat.completions.create(
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
