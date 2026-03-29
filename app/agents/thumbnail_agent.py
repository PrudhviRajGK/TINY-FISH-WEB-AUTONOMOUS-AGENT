"""
AI Thumbnail Generator Agent
Generates eye-catching thumbnails for videos
"""
from typing import Dict, Any
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import textwrap
from .base_agent import BaseAgent


class ThumbnailAgent(BaseAgent):
    """Generates thumbnails for viral videos"""
    
    def __init__(self):
        super().__init__("ThumbnailAgent")
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate thumbnail from video frame
        
        Expected context:
            - video_path: Path to video file
            - title: Video title
            - key_visual_path: Path to key frame image
            - output_path: Where to save thumbnail
        
        Returns:
            - thumbnail_path: Path to generated thumbnail
        """
        self.log_start("Generating video thumbnail")
        
        try:
            title = context.get('title', '')
            key_visual_path = Path(context.get('key_visual_path', ''))
            output_path = Path(context.get('output_path', 'thumbnail.jpg'))
            
            # Generate thumbnail
            thumbnail_path = self._create_thumbnail(
                base_image_path=key_visual_path,
                title=title,
                output_path=output_path
            )
            
            self.log_complete(f"Thumbnail generated: {thumbnail_path}")
            
            return {'thumbnail_path': thumbnail_path}
            
        except Exception as e:
            self.log_error(f"Thumbnail generation failed: {str(e)}")
            raise
    
    def _create_thumbnail(
        self,
        base_image_path: Path,
        title: str,
        output_path: Path
    ) -> Path:
        """Create thumbnail with text overlay"""
        
        # YouTube thumbnail size: 1280x720
        thumbnail_size = (1280, 720)
        
        # Load base image or create blank
        if base_image_path and base_image_path.exists():
            img = Image.open(base_image_path)
            img = img.resize(thumbnail_size, Image.Resampling.LANCZOS)
        else:
            # Create gradient background
            img = self._create_gradient_background(thumbnail_size)
        
        # Enhance image
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.7)  # Darken for text visibility
        
        # Add text overlay
        img = self._add_text_overlay(img, title)
        
        # Add branding elements
        img = self._add_branding(img)
        
        # Save thumbnail
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        
        return output_path
    
    def _create_gradient_background(self, size: tuple) -> Image.Image:
        """Create gradient background"""
        width, height = size
        img = Image.new('RGB', size)
        draw = ImageDraw.Draw(img)
        
        # Create blue to purple gradient
        for y in range(height):
            r = int(30 + (y / height) * 100)
            g = int(50 + (y / height) * 50)
            b = int(150 - (y / height) * 50)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return img
    
    def _add_text_overlay(self, img: Image.Image, title: str) -> Image.Image:
        """Add bold text overlay to thumbnail"""
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Try to load custom font, fallback to default
        try:
            # Large bold font for title
            font_size = 80
            font = ImageFont.truetype("arial.ttf", font_size)
            font_bold = ImageFont.truetype("arialbd.ttf", font_size)
        except:
            font = ImageFont.load_default()
            font_bold = font
        
        # Wrap text
        max_width = width - 100
        wrapped_lines = self._wrap_text(title, font_bold, max_width)
        
        # Limit to 3 lines
        wrapped_lines = wrapped_lines[:3]
        
        # Calculate total text height
        line_height = font_size + 20
        total_height = len(wrapped_lines) * line_height
        
        # Start position (centered vertically)
        y = (height - total_height) // 2
        
        # Draw each line
        for line in wrapped_lines:
            # Get text size
            bbox = draw.textbbox((0, 0), line, font=font_bold)
            text_width = bbox[2] - bbox[0]
            
            # Center horizontally
            x = (width - text_width) // 2
            
            # Draw text shadow
            shadow_offset = 4
            draw.text((x + shadow_offset, y + shadow_offset), line, 
                     fill=(0, 0, 0), font=font_bold)
            
            # Draw main text
            draw.text((x, y), line, fill=(255, 255, 255), font=font_bold)
            
            y += line_height
        
        return img
    
    def _wrap_text(self, text: str, font, max_width: int) -> list:
        """Wrap text to fit within max width"""
        words = text.split()
        lines = []
        current_line = []
        
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _add_branding(self, img: Image.Image) -> Image.Image:
        """Add branding elements to thumbnail"""
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Add "BREAKING" badge in top-left
        badge_text = "BREAKING"
        try:
            badge_font = ImageFont.truetype("arialbd.ttf", 40)
        except:
            badge_font = ImageFont.load_default()
        
        # Badge background
        badge_padding = 20
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_width = bbox[2] - bbox[0] + badge_padding * 2
        badge_height = bbox[3] - bbox[1] + badge_padding * 2
        
        # Draw red badge
        draw.rectangle(
            [(30, 30), (30 + badge_width, 30 + badge_height)],
            fill=(220, 20, 60)  # Crimson red
        )
        
        # Draw badge text
        draw.text(
            (30 + badge_padding, 30 + badge_padding),
            badge_text,
            fill=(255, 255, 255),
            font=badge_font
        )
        
        return img
