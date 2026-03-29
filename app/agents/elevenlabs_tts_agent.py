"""
ElevenLabs TTS Agent
Primary narration engine. Converts script segments to high-quality MP3 audio.
Falls back to Kokoro TTS if ElevenLabs fails.

Supported languages: en (English), hi (Hindi), te (Telugu)
Model: eleven_multilingual_v2
"""
import logging
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# Free-tier premade voice IDs (work without paid plan)
VOICE_MAP = {
    "en": "onwK4e9ZLuTAKqWW03F9",   # Daniel — Steady Broadcaster, great for news
    "hi": "TX3LPaxmHKxFdv7VOQHJ",   # Liam — Energetic, multilingual model handles Hindi
    "te": "TX3LPaxmHKxFdv7VOQHJ",   # Liam — same for Telugu
}

LANGUAGE_LABELS = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
}


class ElevenLabsTTSAgent(BaseAgent):
    """
    Converts audio_script segments to MP3 files using ElevenLabs.
    Falls back to Kokoro TTS on any failure.
    """

    def __init__(self, api_key: str, audio_dir: Optional[Path] = None):
        super().__init__("ElevenLabsTTSAgent")
        self.api_key = api_key
        self.audio_dir = audio_dir or Path("resources/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate audio for all script segments.
        Tries ElevenLabs first; falls back to Kokoro on any failure (including 401/free-tier block).
        """
        self.log_start("Generating narration via ElevenLabs TTS")

        language = context.get("language", "en")
        audio_dir = Path(context.get("audio_dir", self.audio_dir))
        audio_dir.mkdir(parents=True, exist_ok=True)

        script = context.get("script", {})
        audio_script = script.get("audio_script", [])

        if not audio_script:
            self.log_error("No audio_script found in script — cannot generate audio")
            raise ValueError("script.audio_script is empty")

        self.log_progress(
            f"Language: {LANGUAGE_LABELS.get(language, language)} | "
            f"Segments: {len(audio_script)}"
        )

        # Quick connectivity check — if ElevenLabs is unavailable, go straight to Kokoro
        elevenlabs_available = await self._check_elevenlabs()
        if not elevenlabs_available:
            logger.warning("[TTS] ElevenLabs unavailable — using Kokoro for all segments")
            return await self._kokoro_all_segments(audio_script, audio_dir, context)

        audio_files: List[Path] = []

        for idx, segment in enumerate(audio_script):
            text = segment.get("text", "").strip()
            if not text:
                continue

            out_path = audio_dir / f"segment_{idx}.mp3"

            try:
                await self._generate_segment(text, language, out_path)
                audio_files.append(out_path)
                self.log_progress(f"  Segment {idx}: ElevenLabs OK")
            except Exception as e:
                logger.warning(f"[TTS] ElevenLabs failed for segment {idx} — falling back to Kokoro. Error: {e}")
                fallback_path = await self._kokoro_fallback(
                    script_path=context.get("script_path"),
                    audio_dir=audio_dir,
                    segment_index=idx,
                    text=text,
                )
                if fallback_path:
                    audio_files.append(fallback_path)
                    self.log_progress(f"  Segment {idx}: Kokoro fallback OK")

        self.log_complete(f"Generated {len(audio_files)} audio segments")
        return {"audio_files": audio_files}

    async def _check_elevenlabs(self) -> bool:
        """
        Verify ElevenLabs TTS actually works by making a minimal real TTS call.
        The /user endpoint returns 200 even when TTS is blocked, so we must test TTS directly.
        """
        try:
            voice_id = VOICE_MAP.get("en", "onwK4e9ZLuTAKqWW03F9")
            url = ELEVENLABS_API_URL.format(voice_id=voice_id)
            payload = {
                "text": "test",
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
            }
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    return True
                logger.warning(
                    f"[TTS] ElevenLabs TTS check failed: HTTP {resp.status_code} — "
                    f"{resp.json().get('detail', {}).get('message', resp.text[:100])}"
                )
                return False
        except Exception as e:
            logger.warning(f"[TTS] ElevenLabs check error: {e}")
            return False

    async def _kokoro_all_segments(
        self, audio_script: list, audio_dir: Path, context: dict
    ) -> Dict[str, Any]:
        """Generate all segments via Kokoro TTS."""
        try:
            from tts.generate_audio_refactored import main_generate_audio
            script_path = context.get("script_path")
            if script_path:
                audio_files = main_generate_audio(
                    script_path=Path(script_path),
                    audio_path=audio_dir,
                )
                self.log_complete(f"Kokoro generated {len(audio_files) if audio_files else '?'} segments")
                return {"audio_files": audio_files or list(audio_dir.glob("segment_*.wav"))}
        except Exception as e:
            logger.error(f"[TTS] Kokoro full generation failed: {e}")
        return {"audio_files": []}

    async def _generate_segment(self, text: str, language: str, out_path: Path) -> None:
        """Call ElevenLabs API for a single text segment."""
        voice_id = VOICE_MAP.get(language, VOICE_MAP["en"])
        url = ELEVENLABS_API_URL.format(voice_id=voice_id)

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.2,
                "use_speaker_boost": True,
            },
        }

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            out_path.write_bytes(resp.content)

    async def _kokoro_fallback(
        self,
        script_path: Optional[Path],
        audio_dir: Path,
        segment_index: int,
        text: str,
    ) -> Optional[Path]:
        """
        Attempt Kokoro TTS for a single segment.
        Returns the output path or None if Kokoro also fails.
        """
        try:
            from tts.generate_audio_refactored import main_generate_audio
            import json, tempfile

            # Build a minimal single-segment script for Kokoro
            mini_script = {
                "audio_script": [
                    {
                        "timestamp": "00:00",
                        "text": text,
                        "speaker": "narrator_male",
                        "speed": 1.0,
                        "pitch": 1.0,
                        "emotion": "informative",
                    }
                ]
            }

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as tmp:
                json.dump(mini_script, tmp)
                tmp_path = Path(tmp.name)

            fallback_dir = audio_dir / f"_fallback_{segment_index}"
            fallback_dir.mkdir(exist_ok=True)

            main_generate_audio(script_path=tmp_path, audio_path=fallback_dir)
            tmp_path.unlink(missing_ok=True)

            # Kokoro outputs segment_0.wav — rename to match expected naming
            wav_files = sorted(fallback_dir.glob("*.wav"))
            if wav_files:
                dest = audio_dir / f"segment_{segment_index}.wav"
                wav_files[0].rename(dest)
                fallback_dir.rmdir()
                return dest

        except Exception as e:
            logger.error(f"[TTS] Kokoro fallback also failed for segment {segment_index}: {e}")

        return None
