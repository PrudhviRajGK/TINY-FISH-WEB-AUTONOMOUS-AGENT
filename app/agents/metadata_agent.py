"""
AI Metadata Generator Agent
Generates titles, descriptions, and hashtags for social media
"""
import json
import openai
from typing import Dict, Any, List
from .base_agent import BaseAgent


class MetadataAgent(BaseAgent):
    """Generates optimized metadata for video publishing"""
    
    def __init__(self, api_key: str):
        super().__init__("MetadataAgent")
        self.client = openai.OpenAI(api_key=api_key)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate metadata for video.

        Expected context:
            - title, script, category
            - language: 'en' | 'hi' | 'te'  (default 'en')
        """
        self.log_start("Generating video metadata")

        try:
            title = context.get('title', '')
            script = context.get('script', {})
            category = context.get('category', 'business')
            language = context.get('language', 'en')

            metadata = self._generate_metadata(title, script, category, language)
            self.log_complete("Metadata generated for all platforms")
            return {'metadata': metadata}

        except Exception as e:
            self.log_error(f"Metadata generation failed: {str(e)}")
            raise
    
    def _generate_metadata(
        self,
        title: str,
        script: Dict[str, Any],
        category: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate metadata using GPT-4 in the requested language."""

        script_text = self._extract_script_text(script)

        lang_note = {
            "en": "Generate all metadata in English.",
            "hi": "सभी मेटाडेटा हिंदी में लिखें। YouTube title, description और hashtags हिंदी में हों।",
            "te": "అన్ని మెటాడేటాను తెలుగులో రాయండి. YouTube title, description మరియు hashtags తెలుగులో ఉండాలి.",
        }.get(language, "Generate all metadata in English.")

        prompt = f"""Generate viral social media metadata for this business news video.

Original Title: {title}
Script: {script_text}
Category: {category}
Language instruction: {lang_note}

Generate:
1. YouTube Title (max 100 chars) — include emoji, make it clickable
2. YouTube Description (200-300 chars) — brief summary + call to action
3. Hashtags (10-15) — mix trending and specific, include #Shorts #BusinessNews
4. Instagram Caption — 2-3 lines with emojis
5. LinkedIn Post — professional tone, 3-4 lines

Output as JSON:
{{
  "youtube": {{
    "title": "...",
    "description": "...",
    "tags": ["tag1", "tag2"]
  }},
  "instagram": {{
    "caption": "...",
    "hashtags": ["#tag1", "#tag2"]
  }},
  "linkedin": {{
    "post": "...",
    "hashtags": ["#tag1", "#tag2"]
  }}
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a social media expert. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        metadata_text = response.choices[0].message.content

        try:
            metadata = json.loads(metadata_text)
        except Exception:
            import re
            m = re.search(r'```json\n(.*?)\n```', metadata_text, re.DOTALL)
            if m:
                metadata = json.loads(m.group(1))
            else:
                metadata = self._create_fallback_metadata(title, language)

        return metadata
    
    def _extract_script_text(self, script: Dict[str, Any]) -> str:
        """Extract text from script"""
        if 'segments' in script:
            return ' '.join([seg.get('text', '') for seg in script['segments']])
        
        parts = []
        for key in ['hook', 'news', 'why_matters', 'key_fact', 'ending']:
            if key in script:
                parts.append(script[key])
        
        return ' '.join(parts)
    
    def _create_fallback_metadata(self, title: str, language: str = "en") -> Dict[str, Any]:
        """Create fallback metadata if AI generation fails"""
        if language == "hi":
            yt_title = f"📈 {title[:80]}"
            yt_desc = f"ताज़ा बिज़नेस न्यूज़। {title}\n\n#Shorts #BusinessNews"
            ig_caption = f"📊 {title}\n\nफॉलो करें! 🚀"
            li_post = f"{title}\n\nSource: Economic Times"
        elif language == "te":
            yt_title = f"📈 {title[:80]}"
            yt_desc = f"తాజా వ్యాపార వార్తలు. {title}\n\n#Shorts #BusinessNews"
            ig_caption = f"📊 {title}\n\nఫాలో చేయండి! 🚀"
            li_post = f"{title}\n\nSource: Economic Times"
        else:
            yt_title = f"{title} 📈"
            yt_desc = f"Latest business news. {title}\n\n#Shorts #BusinessNews #EconomicTimes"
            ig_caption = f"📊 {title}\n\nFollow for daily business updates! 🚀"
            li_post = f"{title}\n\nStay updated with the latest business developments.\n\nSource: Economic Times"

        return {
            "youtube": {"title": yt_title, "description": yt_desc, "tags": ["business", "news", "shorts"]},
            "instagram": {"caption": ig_caption, "hashtags": ["#business", "#news", "#shorts"]},
            "linkedin": {"post": li_post, "hashtags": ["#Business", "#News", "#India"]},
        }
