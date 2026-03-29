"""
Motion Assembly Agent
Extends VideoAssemblyAgent with dynamic motion visuals.

CASE 1 — Video clip available:
    Load clip → trim to 3-4s → crop/resize to 1080×1920 → use as-is

CASE 2 — Image fallback:
    Apply Ken Burns effect (slow zoom + drift) → animated 4s clip

Both cases feed into the existing create_video pipeline via a
pre-built clips directory, so AssemblyAgent is unchanged.
"""
import logging
import os
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent
from .assembly_agent import VideoAssemblyAgent
from assembly.scripts.assembly_video_refactored import create_video, create_complete_srt

logger = logging.getLogger(__name__)

# Target vertical format
TARGET_W = 1080
TARGET_H = 1920
CLIP_DURATION = 4.0   # seconds per visual segment


class MotionAssemblyAgent(BaseAgent):
    """
    Assembles the final video using motion visuals.
    Replaces static ImageClip calls with either real video clips
    or Ken Burns animated image clips.
    """

    def __init__(self):
        super().__init__("MotionAssemblyAgent")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assemble video with motion visuals.

        Expected context (in addition to standard AssemblyAgent keys):
            - clip_results:  list of {segment_index, clip_path, duration, source}
            - image_paths:   list of Path (fallback images, one per segment)
            - script_path, audio_folder, output_file, font_path,
              intro_image_path, subtitle_path, fps, with_subtitles

        Returns:
            - video_path, subtitle_path
        """
        self.log_start("Assembling video — images primary, clips as motion overlay")

        try:
            from moviepy import (
                VideoFileClip, ImageClip, AudioFileClip,
                CompositeVideoClip, concatenate_videoclips,
                vfx,
            )

            clip_results: List[Dict] = context.get("clip_results", [])
            image_paths: List[Path] = context.get("image_paths", [])
            audio_folder = Path(context["audio_folder"])
            script_path = Path(context["script_path"])
            output_file = Path(context["output_file"])
            font_path = Path(context["font_path"])
            intro_image_path = Path(context["intro_image_path"])
            subtitle_path = Path(context["subtitle_path"])
            fps = context.get("fps", 24)
            with_subtitles = context.get("with_subtitles", True)

            # Build lookup: segment_index → clip_path (used as overlay only)
            clip_map: Dict[int, Optional[Path]] = {
                r["segment_index"]: r.get("clip_path")
                for r in clip_results
                if r.get("clip_path")
            }

            motion_dir = output_file.parent / f"motion_{output_file.stem}"
            motion_dir.mkdir(parents=True, exist_ok=True)

            n_segments = len(image_paths)

            for idx in range(n_segments):
                out_path = motion_dir / f"scene_{idx:03d}.mp4"

                # Primary visual: always the image (Ken Burns)
                img_path = image_paths[idx] if idx < len(image_paths) else None
                if img_path and Path(img_path).exists():
                    self.log_progress(f"Segment {idx}: Ken Burns image")
                    base_clip = self._apply_ken_burns(img_path, CLIP_DURATION)
                else:
                    from moviepy import ColorClip
                    self.log_progress(f"Segment {idx}: black frame fallback")
                    base_clip = ColorClip(
                        size=(TARGET_W, TARGET_H), color=(0, 0, 0), duration=CLIP_DURATION
                    )

                # Motion overlay: blend clip on top at low opacity if available
                clip_path = clip_map.get(idx)
                if clip_path and Path(clip_path).exists():
                    self.log_progress(f"Segment {idx}: adding motion overlay")
                    motion_clip = self._build_motion_overlay(clip_path, CLIP_DURATION)
                    if motion_clip:
                        final_clip = CompositeVideoClip(
                            [base_clip, motion_clip],
                            size=(TARGET_W, TARGET_H),
                        )
                    else:
                        final_clip = base_clip
                else:
                    final_clip = base_clip

                final_clip.write_videofile(
                    str(out_path), fps=fps, logger=None, audio=False
                )
                final_clip.close()

            # Generate subtitles
            self.log_progress("Generating subtitles...")
            create_complete_srt(
                script_folder=script_path,
                audio_file_folder=audio_folder,
                outfile_path=subtitle_path,
                chunk_size=context.get("chunk_size", 10),
            )

            self.log_progress("Assembling final video...")
            self._assemble_with_motion(
                motion_dir=motion_dir,
                audio_folder=audio_folder,
                script_path=script_path,
                font_path=font_path,
                output_file=output_file,
                intro_image_path=intro_image_path,
                subtitle_path=subtitle_path,
                with_subtitles=with_subtitles,
                fps=fps,
            )

            self.log_complete(f"Video assembled: {output_file}")
            return {
                "video_path": output_file,
                "subtitle_path": subtitle_path,
            }

        except Exception as e:
            self.log_error(f"Motion assembly failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Motion clip builders
    # ------------------------------------------------------------------

    def _build_motion_overlay(self, clip_path: Path, duration: float):
        """
        Load a stock clip, crop to 9:16, trim to duration,
        and set opacity to ~25% so it blends over the image as a motion texture.
        Returns None if the clip can't be loaded.
        """
        try:
            from moviepy import VideoFileClip
            vc = VideoFileClip(str(clip_path)).without_audio()
            vc = self._crop_to_vertical(vc)
            trim = min(vc.duration, duration)
            vc = vc.subclipped(0, trim)
            if vc.duration < duration:
                loops = int(duration / vc.duration) + 1
                from moviepy import concatenate_videoclips as _cat
                vc = _cat([vc] * loops).subclipped(0, duration)
            # 25% opacity overlay — adds motion feel without obscuring the image
            vc = vc.with_opacity(0.25)
            return vc
        except Exception as e:
            logger.warning(f"[MotionAssembly] Could not build overlay from {clip_path}: {e}")
            return None

    def _prepare_video_clip(self, clip_path: Path, target_duration: float):
        """Load a stock video clip, trim and crop to 1080x1920."""
        from moviepy import VideoFileClip
        clip = VideoFileClip(str(clip_path))
        duration = min(clip.duration, target_duration)
        clip = clip.subclipped(0, duration)
        return self._crop_to_vertical(clip)

    def _apply_ken_burns(self, image_path: Path, duration: float):
        """
        Apply Ken Burns effect to a static image:
        - Slow zoom in (1.0 → 1.08 over `duration` seconds)
        - Gentle drift (top-left → centre)
        Returns a VideoClip sized TARGET_W × TARGET_H.
        """
        from moviepy import ImageClip

        # Oversample so zoom doesn't reveal edges
        oversample = 1.15
        clip = (
            ImageClip(str(image_path))
            .resized((int(TARGET_W * oversample), int(TARGET_H * oversample)))
            .with_duration(duration)
        )

        zoom_factor = 0.08   # total zoom over duration
        drift_x = int(TARGET_W * oversample - TARGET_W) // 2
        drift_y = int(TARGET_H * oversample - TARGET_H) // 2

        def make_frame(t):
            progress = t / duration  # 0 → 1
            scale = 1.0 + zoom_factor * progress

            # Current frame from the oversampled clip
            frame = clip.get_frame(t)  # H×W×3 numpy array
            h, w = frame.shape[:2]

            # Compute crop window
            new_w = int(TARGET_W / scale)
            new_h = int(TARGET_H / scale)

            # Drift offset
            ox = int(drift_x * progress)
            oy = int(drift_y * progress)

            # Clamp
            ox = max(0, min(ox, w - new_w))
            oy = max(0, min(oy, h - new_h))

            cropped = frame[oy: oy + new_h, ox: ox + new_w]

            # Resize back to target
            from PIL import Image as PILImage
            pil = PILImage.fromarray(cropped).resize(
                (TARGET_W, TARGET_H), PILImage.LANCZOS
            )
            return np.array(pil)

        from moviepy import VideoClip
        return VideoClip(make_frame, duration=duration).with_fps(24)

    # ------------------------------------------------------------------
    # Final assembly (motion-aware)
    # ------------------------------------------------------------------

    def _assemble_with_motion(
        self,
        motion_dir: Path,
        audio_folder: Path,
        script_path: Path,
        font_path: Path,
        output_file: Path,
        intro_image_path: Path,
        subtitle_path: Path,
        with_subtitles: bool,
        fps: int,
    ):
        """
        Assemble the final video by pairing motion clips with audio segments.
        Mirrors the logic in create_video but uses VideoFileClip for .mp4 files.
        """
        from moviepy import (
            VideoFileClip, ImageClip, AudioFileClip,
            CompositeVideoClip, concatenate_videoclips,
            TextClip, vfx,
        )
        from assembly.scripts.assembly_video_refactored import (
            get_files, extract_topic_from_json, json_extract,
            create_intro_clip, add_effects,
        )

        audio_files = get_files(audio_folder, (".mp3", ".wav"))
        motion_clips_paths = sorted(motion_dir.glob("scene_*.mp4"))

        # Pad or trim so counts match
        while len(motion_clips_paths) < len(audio_files):
            motion_clips_paths.append(motion_clips_paths[-1] if motion_clips_paths else None)

        subtitles = json_extract(script_path)
        topic = extract_topic_from_json(script_path)

        raw_clips = []
        audio_durations = []

        # Intro
        intro = create_intro_clip(intro_image_path, duration=5, topic=topic, font_path=font_path)
        raw_clips.append(intro)

        for motion_path, audio_path in zip(motion_clips_paths, audio_files):
            audio_clip = AudioFileClip(str(audio_path))
            audio_durations.append(audio_clip.duration)

            if motion_path and motion_path.exists():
                vc = VideoFileClip(str(motion_path))
                # Loop if motion clip is shorter than audio
                if vc.duration < audio_clip.duration:
                    loops = int(audio_clip.duration / vc.duration) + 1
                    from moviepy import concatenate_videoclips as _cat
                    vc = _cat([vc] * loops).subclipped(0, audio_clip.duration)
                else:
                    vc = vc.subclipped(0, audio_clip.duration)
                segment_clip = vc.with_audio(audio_clip)
            else:
                # Absolute fallback: black frame
                from moviepy import ColorClip
                segment_clip = (
                    ColorClip(size=(TARGET_W, TARGET_H), color=(0, 0, 0))
                    .with_duration(audio_clip.duration)
                    .with_audio(audio_clip)
                )

            segment_clip = add_effects(segment_clip)
            raw_clips.append(segment_clip)
        # Outro
        outro = create_intro_clip(
            intro_image_path, duration=5, topic="MADE BY TEAM FRAGMENT", font_path=font_path
        )
        raw_clips.append(outro)

        video = concatenate_videoclips(raw_clips, method="compose")

        if with_subtitles:
            start_t = 5.0
            sub_clips = [video]
            chunk_size = 10
            for text, dur in zip(subtitles, audio_durations):
                words = text.split()
                if len(words) > chunk_size:
                    for i in range(0, len(words), chunk_size):
                        chunk = " ".join(words[i: i + chunk_size])
                        chunk_dur = dur * (len(chunk.split()) / len(words))
                        sub_clips.append(
                            TextClip(
                                text=chunk, font=str(font_path),
                                color="white", bg_color="black",
                                size=(TARGET_W, 150), font_size=28,
                                method="caption", text_align="center",
                            )
                            .with_duration(chunk_dur)
                            .with_start(start_t)
                            .with_position("bottom")
                        )
                        start_t += chunk_dur
                else:
                    sub_clips.append(
                        TextClip(
                            text=text, font=str(font_path),
                            color="white", bg_color="black",
                            size=(TARGET_W, 150), font_size=28,
                            method="caption", text_align="center",
                        )
                        .with_duration(dur)
                        .with_start(start_t)
                        .with_position("bottom")
                    )
                    start_t += dur

            final = CompositeVideoClip(sub_clips)
        else:
            final = video

        output_file.parent.mkdir(parents=True, exist_ok=True)
        final.write_videofile(str(output_file), fps=fps, threads=os.cpu_count())
        logger.info(f"[MotionAssemblyAgent] Video written: {output_file}")

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _crop_to_vertical(clip):
        """Centre-crop a clip to 9:16 aspect ratio."""
        from moviepy import vfx

        w, h = clip.size
        target_ratio = TARGET_W / TARGET_H  # 9/16

        if w / h > target_ratio:
            # Wider than needed — crop sides
            new_w = int(h * target_ratio)
            x1 = (w - new_w) // 2
            clip = clip.cropped(x1=x1, x2=x1 + new_w)
        else:
            # Taller than needed — crop top/bottom
            new_h = int(w / target_ratio)
            y1 = (h - new_h) // 2
            clip = clip.cropped(y1=y1, y2=y1 + new_h)

        return clip.resized((TARGET_W, TARGET_H))
