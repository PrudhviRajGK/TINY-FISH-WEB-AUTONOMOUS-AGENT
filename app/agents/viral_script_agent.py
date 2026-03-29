"""
Viral Script Generator Agent
Converts news articles into viral short-form video scripts.
Supports multilingual output: English (en), Hindi (hi), Telugu (te).
"""
import json
import openai
from typing import Dict, Any
from .base_agent import BaseAgent

# Language-specific prompt instructions
_LANG_INSTRUCTIONS = {
    "en": (
        "Write the entire script in natural, conversational English. "
        "Use energetic, punchy language optimised for YouTube Shorts."
    ),
    "hi": (
        "पूरी स्क्रिप्ट स्वाभाविक बोलचाल की हिंदी में लिखें। "
        "YouTube Shorts के लिए ऊर्जावान और प्रभावशाली भाषा का उपयोग करें। "
        "अंग्रेज़ी तकनीकी शब्दों को हिंदी में लिखें जैसे 'एआई', 'स्टार्टअप'।"
    ),
    "te": (
        "మొత్తం స్క్రిప్ట్‌ను సహజమైన తెలుగులో రాయండి. "
        "YouTube Shorts కోసం శక్తివంతమైన మరియు ఆకర్షణీయమైన భాషను ఉపయోగించండి. "
        "ఆంగ్ల సాంకేతిక పదాలను తెలుగులో రాయండి, ఉదా: 'ఏఐ', 'స్టార్టప్'."
    ),
}

_LANG_LABELS = {"en": "English", "hi": "Hindi", "te": "Telugu"}

_FOLLOW_CTA = {
    "en": "Follow for more business news!",
    "hi": "और बिज़नेस न्यूज़ के लिए फॉलो करें!",
    "te": "మరిన్ని వ్యాపార వార్తల కోసం ఫాలో చేయండి!",
}


class ViralScriptAgent(BaseAgent):
    """Generates viral scripts optimized for YouTube Shorts, Instagram Reels"""
    
    def __init__(self, api_key: str):
        super().__init__("ViralScriptAgent")
        self.client = openai.OpenAI(api_key=api_key)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate viral script from article.

        Expected context:
            - title, content, summary, category
            - language: 'en' | 'hi' | 'te'  (default 'en')

        Returns:
            - script: Viral video script with segments
        """
        self.log_start("Generating viral script from article")

        try:
            title = context.get('title', '')
            content = context.get('content', '')
            summary = context.get('summary', '')
            category = context.get('category', 'business')
            language = context.get('language', 'en')

            self.log_progress(f"Language: {_LANG_LABELS.get(language, language)}")

            script = self._generate_viral_script(
                title=title,
                content=content,
                summary=summary,
                category=category,
                language=language,
            )

            self.log_complete(f"Generated viral script with {len(script['segments'])} segments")
            return {'script': script}

        except Exception as e:
            self.log_error(f"Viral script generation failed: {str(e)}")
            raise
    
    def _generate_viral_script(
        self,
        title: str,
        content: str,
        summary: str,
        category: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate viral script using GPT-4 in the requested language."""

        lang_instruction = _LANG_INSTRUCTIONS.get(language, _LANG_INSTRUCTIONS["en"])
        follow_cta = _FOLLOW_CTA.get(language, _FOLLOW_CTA["en"])

        prompt = f"""Convert this news article into a viral 30-45 second video script.

Article Title: {title}
Summary: {summary}
Content: {content[:1000]}
Category: {category}

LANGUAGE INSTRUCTION: {lang_instruction}

Create a script with this EXACT structure:
1. HOOK (3 seconds) - Shocking/attention-grabbing opener
2. THE NEWS (10 seconds) - What happened
3. WHY IT MATTERS (10 seconds) - Impact and significance
4. KEY FACT (8 seconds) - Most important data point
5. ENDING (5 seconds) - Call to action: "{follow_cta}"

Requirements:
- All narration text MUST be in the specified language
- Include specific numbers and data
- Keep it urgent and impactful
- Total duration: 30-45 seconds

Output as JSON:
{{
  "topic": "title",
  "language": "{language}",
  "audio_script": [
    {{"timestamp": "00:00", "text": "hook text", "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"}},
    {{"timestamp": "00:03", "text": "news text", "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"}},
    {{"timestamp": "00:13", "text": "why it matters text", "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"}},
    {{"timestamp": "00:23", "text": "key fact text", "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"}},
    {{"timestamp": "00:31", "text": "{follow_cta}", "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"}}
  ],
  "visual_script": [
    {{"timestamp_start": "00:00", "timestamp_end": "00:03", "prompt": "Bold text with news headline", "negative_prompt": "Avoid abstract"}},
    {{"timestamp_start": "00:03", "timestamp_end": "00:13", "prompt": "Article image or related visual", "negative_prompt": "Avoid abstract"}},
    {{"timestamp_start": "00:13", "timestamp_end": "00:23", "prompt": "Impact visualization", "negative_prompt": "Avoid abstract"}},
    {{"timestamp_start": "00:23", "timestamp_end": "00:31", "prompt": "Data visualization", "negative_prompt": "Avoid abstract"}},
    {{"timestamp_start": "00:31", "timestamp_end": "00:36", "prompt": "Call to action screen", "negative_prompt": "Avoid abstract"}}
  ],
  "segments": [
    {{"timestamp_start": "00:00", "timestamp_end": "00:03", "text": "hook text", "visual_description": "Bold headline", "segment_type": "hook"}},
    {{"timestamp_start": "00:03", "timestamp_end": "00:13", "text": "news text", "visual_description": "News visual", "segment_type": "news"}},
    {{"timestamp_start": "00:13", "timestamp_end": "00:23", "text": "why it matters text", "visual_description": "Impact visual", "segment_type": "why_matters"}},
    {{"timestamp_start": "00:23", "timestamp_end": "00:31", "text": "key fact text", "visual_description": "Data visual", "segment_type": "key_fact"}},
    {{"timestamp_start": "00:31", "timestamp_end": "00:36", "text": "{follow_cta}", "visual_description": "CTA screen", "segment_type": "ending"}}
  ]
}}"""

        system_prompt = (
            "You are a viral content creator specialising in business news shorts. "
            "Generate scripts in the exact language specified. "
            "For Hindi and Telugu, use natural spoken language — not formal/literary style. "
            "Output valid JSON only."
        )

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=1500,
        )

        script_text = response.choices[0].message.content

        try:
            script = json.loads(script_text)
        except Exception:
            import re
            m = re.search(r'```json\n(.*?)\n```', script_text, re.DOTALL)
            if m:
                script = json.loads(m.group(1))
            else:
                script = self._create_fallback_script(title, summary, language)

        # Ensure all required fields
        if 'audio_script' not in script:
            script['audio_script'] = self._create_audio_script_from_segments(script.get('segments', []))
        if 'visual_script' not in script:
            script['visual_script'] = self._create_visual_script_from_segments(script.get('segments', []))
        if 'segments' not in script:
            script['segments'] = self._create_segments_from_text(script)

        script['language'] = language
        return script
    
    def _create_fallback_script(self, title: str, summary: str, language: str = "en") -> Dict[str, Any]:
        """Create fallback script if AI generation fails"""
        follow_cta = _FOLLOW_CTA.get(language, _FOLLOW_CTA["en"])
        hook_text = f"Breaking: {title[:100]}" if language == "en" else title[:100]
        news_text = summary[:200] if summary else ("Here's what you need to know." if language == "en" else summary[:200])

        audio_script = [
            {"timestamp": "00:00", "text": hook_text, "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"},
            {"timestamp": "00:03", "text": news_text, "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"},
            {"timestamp": "00:15", "text": "This could change everything in the business world." if language == "en" else news_text, "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"},
            {"timestamp": "00:25", "text": follow_cta, "speaker": "narrator_male", "speed": 1.0, "pitch": 1.0, "emotion": "informative"},
        ]

        visual_script = [
            {"timestamp_start": "00:00", "timestamp_end": "00:03", "prompt": "Bold text with news headline", "negative_prompt": "Avoid abstract"},
            {"timestamp_start": "00:03", "timestamp_end": "00:15", "prompt": "Article image or related visual", "negative_prompt": "Avoid abstract"},
            {"timestamp_start": "00:15", "timestamp_end": "00:25", "prompt": "Impact visualization", "negative_prompt": "Avoid abstract"},
            {"timestamp_start": "00:25", "timestamp_end": "00:30", "prompt": "Call to action screen", "negative_prompt": "Avoid abstract"},
        ]

        segments = [
            {"timestamp_start": "00:00", "timestamp_end": "00:03", "text": hook_text, "visual_description": "Bold text with news headline", "segment_type": "hook"},
            {"timestamp_start": "00:03", "timestamp_end": "00:15", "text": news_text, "visual_description": "Article image or related visual", "segment_type": "news"},
            {"timestamp_start": "00:15", "timestamp_end": "00:25", "text": "This could change everything in the business world." if language == "en" else news_text, "visual_description": "Impact visualization", "segment_type": "why_matters"},
            {"timestamp_start": "00:25", "timestamp_end": "00:30", "text": follow_cta, "visual_description": "Call to action screen", "segment_type": "ending"},
        ]

        return {"topic": title, "language": language, "audio_script": audio_script, "visual_script": visual_script, "segments": segments}
    
    def _create_audio_script_from_segments(self, segments: list) -> list:
        """Create audio_script from segments"""
        audio_script = []
        for seg in segments:
            audio_script.append({
                "timestamp": seg.get('timestamp_start', '00:00'),
                "text": seg.get('text', ''),
                "speaker": "narrator_male",
                "speed": 1.0,
                "pitch": 1.0,
                "emotion": "informative"
            })
        return audio_script
    
    def _create_visual_script_from_segments(self, segments: list) -> list:
        """Create visual_script from segments"""
        visual_script = []
        for seg in segments:
            visual_script.append({
                "timestamp_start": seg.get('timestamp_start', '00:00'),
                "timestamp_end": seg.get('timestamp_end', '00:05'),
                "prompt": seg.get('visual_description', 'Visual for segment'),
                "negative_prompt": "Avoid abstract or complex designs"
            })
        return visual_script
    
    def _create_segments_from_text(self, script: Dict[str, Any]) -> list:
        """Create segments from script text fields"""
        segments = []
        current_time = 0
        
        segment_map = [
            ('hook', 3, 'hook'),
            ('news', 12, 'news'),
            ('why_matters', 10, 'why_matters'),
            ('key_fact', 8, 'key_fact'),
            ('ending', 5, 'ending'),
        ]
        
        for field, duration, seg_type in segment_map:
            if field in script:
                end_time = current_time + duration
                segments.append({
                    "timestamp_start": f"00:{current_time:02d}",
                    "timestamp_end": f"00:{end_time:02d}",
                    "text": script[field],
                    "visual_description": f"Visual for {seg_type}",
                    "segment_type": seg_type
                })
                current_time = end_time
        
        return segments
