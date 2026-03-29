"""
Image Generator Agent
Handles hybrid image sourcing: article images + AI generation
"""
from typing import Dict, Any, List
from pathlib import Path
import httpx
from .base_agent import BaseAgent
from imagegen.gen_img_openai_refactored import generate_openai_image, download_image


class ImageGeneratorAgent(BaseAgent):
    """Agent responsible for sourcing and generating images"""
    
    def __init__(self, api_key: str):
        super().__init__("ImageGeneratorAgent")
        self.api_key = api_key
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate fallback images ONLY for segments that have no video clip.

        Expected context:
            - script:        Video script with visual_script
            - clip_results:  list of {segment_index, clip_path, ...}
            - extracted_images: Images from article
            - images_dir:    Output directory

        Returns:
            - image_paths: list of Path (one per segment, None where clip exists)
        """
        self.log_start("Generating fallback images for segments without clips")

        try:
            script = context['script']
            extracted_images = context.get('extracted_images', [])
            images_dir = Path(context['images_dir'])
            images_dir.mkdir(parents=True, exist_ok=True)

            visual_script = script.get('visual_script', [])
            image_paths = []

            for idx, scene in enumerate(visual_script):
                # Priority 1: article image (round-robin across available images)
                article_img = None
                if extracted_images:
                    img_idx = idx % len(extracted_images)
                    candidate = extracted_images[img_idx]
                    if candidate.get("url"):
                        article_img = candidate["url"]

                if article_img:
                    self.log_progress(f"Segment {idx}: using article image")
                    try:
                        image_path = await self._download_article_image(
                            article_img, images_dir, idx
                        )
                        image_paths.append(image_path)
                        continue
                    except Exception as e:
                        self.log_progress(f"Segment {idx}: article image failed ({e}), using DALL-E")

                # Priority 2: DALL-E 9:16
                self.log_progress(f"Segment {idx}: generating DALL-E image")
                prompt = scene.get('prompt', '')
                image_path = await self._generate_ai_image(prompt, images_dir, idx)
                image_paths.append(image_path)

            real_images = sum(1 for p in image_paths if p is not None)
            self.log_complete(f"Generated {real_images} images for {len(visual_script)} segments")
            return {'image_paths': image_paths}

        except Exception as e:
            self.log_error(f"Image generation failed: {str(e)}")
            raise

    
    async def _download_article_image(
        self,
        url: str,
        output_dir: Path,
        index: int
    ) -> Path:
        """Download and crop article image to 9:16 vertical format."""
        output_path = output_dir / f"scene_{index:03d}.jpg"

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; FragmentBot/1.0)"
            })
            response.raise_for_status()

        # Save raw download
        raw_path = output_dir / f"scene_{index:03d}_raw.jpg"
        raw_path.write_bytes(response.content)

        # Crop/resize to 9:16 (1080x1920) using PIL
        try:
            from PIL import Image as PILImage
            img = PILImage.open(raw_path).convert("RGB")
            w, h = img.size
            target_ratio = 9 / 16

            if w / h > target_ratio:
                # Too wide — crop sides
                new_w = int(h * target_ratio)
                x1 = (w - new_w) // 2
                img = img.crop((x1, 0, x1 + new_w, h))
            else:
                # Too tall — crop top/bottom
                new_h = int(w / target_ratio)
                y1 = (h - new_h) // 2
                img = img.crop((0, y1, w, y1 + new_h))

            img = img.resize((1080, 1920), PILImage.LANCZOS)
            img.save(output_path, "JPEG", quality=90)
            raw_path.unlink(missing_ok=True)
        except Exception:
            # If PIL fails, just use the raw download as-is
            raw_path.rename(output_path)

        return output_path
    
    async def _generate_ai_image(
        self,
        prompt: str,
        output_dir: Path,
        index: int
    ) -> Path:
        """Generate image using DALL-E in 9:16 vertical format."""
        output_path = output_dir / f"scene_{index:03d}.jpg"

        # Use 1024x1792 for native 9:16 — no cropping needed
        image_urls = generate_openai_image(
            prompt=f"{prompt}, vertical composition, 9:16 aspect ratio, cinematic",
            api_key=self.api_key,
            model="dall-e-3",
            size="1024x1792"
        )

        download_image(image_urls[0], output_path)
        return output_path
