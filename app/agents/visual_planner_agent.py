"""
Visual Planner Agent
Converts script segments into cinematic visual search queries.
"""
import re
import openai
import logging
from typing import Dict, Any, List

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Segment-type → default visual style hint
_STYLE_HINTS = {
    "hook":        "dramatic cinematic wide shot",
    "news":        "news broadcast professional",
    "why_matters": "business impact visualization",
    "key_fact":    "data technology close-up",
    "ending":      "call to action motivational",
}


class VisualPlannerAgent(BaseAgent):
    """
    Converts each script segment into a concrete visual search query
    suitable for stock video APIs and DALL-E.
    """

    def __init__(self, api_key: str):
        super().__init__("VisualPlannerAgent")
        self.client = openai.OpenAI(api_key=api_key)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a visual plan for every segment in the script.

        Expected context:
            - script: dict with 'segments' list

        Returns:
            - visual_plan: list of {segment_index, query, keywords, style_hint, segment_type}
        """
        self.log_start("Building visual plan from script segments")

        script = context.get("script", {})
        segments = script.get("segments", [])

        if not segments:
            # Fall back to visual_script if segments missing
            segments = [
                {
                    "timestamp_start": s.get("timestamp_start", "00:00"),
                    "timestamp_end": s.get("timestamp_end", "00:05"),
                    "text": s.get("prompt", ""),
                    "segment_type": "general",
                }
                for s in script.get("visual_script", [])
            ]

        visual_plan = []
        for idx, segment in enumerate(segments):
            plan_item = self.generate_visual_query(segment, idx)
            visual_plan.append(plan_item)
            self.log_progress(
                f"Segment {idx} ({plan_item['segment_type']}): {plan_item['query']}"
            )

        self.log_complete(f"Visual plan ready — {len(visual_plan)} queries")
        return {"visual_plan": visual_plan}

    def generate_visual_query(
        self, segment: Dict[str, Any], index: int = 0
    ) -> Dict[str, Any]:
        """
        Convert a single script segment into a visual search query.

        Returns:
            {
                "segment_index": int,
                "query": str,          # stock video / image search string
                "keywords": list[str], # individual search terms
                "style_hint": str,     # cinematic style descriptor
                "segment_type": str,
                "timestamp_start": str,
                "timestamp_end": str,
            }
        """
        text = segment.get("text", "") or segment.get("visual_description", "")
        seg_type = segment.get("segment_type", "general")
        style_hint = _STYLE_HINTS.get(seg_type, "cinematic professional")

        query = self._text_to_visual_query(text, seg_type)
        keywords = self._extract_keywords(query)

        return {
            "segment_index": index,
            "query": query,
            "keywords": keywords,
            "style_hint": style_hint,
            "segment_type": seg_type,
            "timestamp_start": segment.get("timestamp_start", "00:00"),
            "timestamp_end": segment.get("timestamp_end", "00:05"),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _text_to_visual_query(self, text: str, seg_type: str) -> str:
        """
        Map narration text to a concrete visual description.
        Uses a rule-based approach first; falls back to GPT for complex text.
        """
        text_lower = text.lower()

        # Rule-based fast path — covers the most common news topics
        rules = [
            (["ai", "artificial intelligence", "chatgpt", "openai", "llm", "model"],
             "AI technology data center servers glowing blue light"),
            (["startup", "founder", "venture", "funding", "series"],
             "startup office developers working computers modern"),
            (["stock", "market", "sensex", "nifty", "shares", "trading"],
             "stock market trading floor screens financial data"),
            (["layoff", "fired", "job cut", "redundan"],
             "office workers packing boxes corporate downsizing"),
            (["acquisition", "merger", "deal", "billion"],
             "business handshake corporate deal signing"),
            (["india", "bangalore", "mumbai", "delhi"],
             "India city skyline modern technology hub"),
            (["electric", "ev", "tesla", "vehicle"],
             "electric vehicle charging futuristic"),
            (["crypto", "bitcoin", "blockchain"],
             "cryptocurrency blockchain digital finance"),
            (["bank", "finance", "loan", "rbi"],
             "bank building financial district cityscape"),
            (["follow", "subscribe", "like", "comment"],
             "social media notification bell subscribe button"),
        ]

        for keywords, visual in rules:
            if any(kw in text_lower for kw in keywords):
                return visual

        # GPT fallback for unusual topics
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Convert news narration into a 5-8 word visual search query "
                            "for stock footage. Return ONLY the query, no explanation. "
                            "Make it concrete and cinematic."
                        ),
                    },
                    {"role": "user", "content": f"Narration: {text[:200]}"},
                ],
                max_tokens=30,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip().strip('"')
        except Exception:
            # Last resort: strip stop-words from the narration
            return self._naive_query(text)

    def _extract_keywords(self, query: str) -> List[str]:
        """Split query into individual keyword tokens."""
        stop = {"a", "an", "the", "and", "or", "of", "in", "on", "at", "with", "for"}
        words = re.findall(r"[a-zA-Z]+", query.lower())
        return [w for w in words if w not in stop]

    @staticmethod
    def _naive_query(text: str) -> str:
        """Fallback: take first 6 meaningful words from narration."""
        stop = {"a", "an", "the", "and", "or", "is", "are", "was", "were",
                "it", "this", "that", "to", "of", "in", "on", "at"}
        words = [w for w in re.findall(r"[a-zA-Z]+", text) if w.lower() not in stop]
        return " ".join(words[:6])
