"""
Application Configuration
Loads all settings from environment variables
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Fragment Video Generator"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000",
        env="CORS_ORIGINS"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # API Keys
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    # TinyFish is a required dependency — the pipeline cannot run without it
    TINYFISH_API_KEY: str = Field(..., env="TINYFISH_API_KEY")
    TINYFISH_BASE_URL: str = Field(default="https://agent.tinyfish.ai/v1", env="TINYFISH_BASE_URL")

    # Stock video APIs (optional — enables real motion clips)
    PEXELS_API_KEY: Optional[str] = Field(None, env="PEXELS_API_KEY")
    PIXABAY_API_KEY: Optional[str] = Field(None, env="PIXABAY_API_KEY")

    # ElevenLabs TTS — primary narration engine
    ELEVENLABS_API_KEY: Optional[str] = Field(None, env="ELEVENLABS_API_KEY")
    
    # Social Media API Keys (Optional)
    YOUTUBE_API_KEY: Optional[str] = Field(None, env="YOUTUBE_API_KEY")
    YOUTUBE_ACCESS_TOKEN: Optional[str] = Field(None, env="YOUTUBE_ACCESS_TOKEN")
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = Field(None, env="INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_USER_ID: Optional[str] = Field(None, env="INSTAGRAM_USER_ID")
    TIKTOK_ACCESS_TOKEN: Optional[str] = Field(None, env="TIKTOK_ACCESS_TOKEN")
    LINKEDIN_ACCESS_TOKEN: Optional[str] = Field(None, env="LINKEDIN_ACCESS_TOKEN")
    LINKEDIN_PERSON_URN: Optional[str] = Field(None, env="LINKEDIN_PERSON_URN")
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_FOLDER: Optional[Path] = Field(default=None)
    STATIC_DIR: Optional[Path] = Field(default=None)
    TEMPLATES_DIR: Optional[Path] = Field(default=None)
    RESOURCE_DIR: Optional[Path] = Field(default=None)
    
    # Resource subdirectories
    SCRIPT_DIR: Optional[Path] = Field(default=None)
    IMAGES_DIR: Optional[Path] = Field(default=None)
    AUDIO_DIR: Optional[Path] = Field(default=None)
    VIDEO_OUTPUT_DIR: Optional[Path] = Field(default=None)
    SUBTITLE_OUTPUT_DIR: Optional[Path] = Field(default=None)
    FONT_PATH: Optional[Path] = Field(default=None)
    HINDI_FONT_PATH: Optional[Path] = Field(default=None)
    TELUGU_FONT_PATH: Optional[Path] = Field(default=None)
    INTRO_IMAGE_PATH: Optional[Path] = Field(default=None)
    CLIPS_DIR: Optional[Path] = Field(default=None)
    
    # File upload limits
    MAX_UPLOAD_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 50MB
    
    # Video generation settings
    DEFAULT_VIDEO_DURATION: int = Field(default=60, env="DEFAULT_VIDEO_DURATION")
    DEFAULT_VIDEO_FPS: int = Field(default=24, env="DEFAULT_VIDEO_FPS")
    DEFAULT_CHUNK_SIZE: int = Field(default=10, env="DEFAULT_CHUNK_SIZE")
    
    # DALL-E settings
    DALLE_MODEL: str = Field(default="dall-e-3", env="DALLE_MODEL")
    DALLE_SIZE: str = Field(default="1024x1024", env="DALLE_SIZE")
    DALLE_QUALITY: str = Field(default="standard", env="DALLE_QUALITY")
    
    # TTS settings
    TTS_LANG_CODE: str = Field(default="b", env="TTS_LANG_CODE")
    
    # Logging
    LOG_FILE: str = Field(default="app.log", env="LOG_FILE")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Background task settings
    TASK_TIMEOUT: int = Field(default=600, env="TASK_TIMEOUT")  # 10 minutes
    IMAGE_GEN_DELAY: float = Field(default=2.0, env="IMAGE_GEN_DELAY")  # Delay between DALL-E calls
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize paths after base initialization
        if self.UPLOAD_FOLDER is None:
            self.UPLOAD_FOLDER = self.BASE_DIR / "uploads"
        
        if self.STATIC_DIR is None:
            self.STATIC_DIR = self.BASE_DIR / "static"
        
        if self.TEMPLATES_DIR is None:
            self.TEMPLATES_DIR = self.BASE_DIR / "templates"
        
        if self.RESOURCE_DIR is None:
            self.RESOURCE_DIR = self.BASE_DIR / "resources"
        
        # Resource subdirectories
        if self.SCRIPT_DIR is None:
            self.SCRIPT_DIR = self.RESOURCE_DIR / "scripts"
        
        if self.IMAGES_DIR is None:
            self.IMAGES_DIR = self.RESOURCE_DIR / "images"
        
        if self.AUDIO_DIR is None:
            self.AUDIO_DIR = self.RESOURCE_DIR / "audio"
        
        if self.VIDEO_OUTPUT_DIR is None:
            self.VIDEO_OUTPUT_DIR = self.RESOURCE_DIR / "video"
        
        if self.SUBTITLE_OUTPUT_DIR is None:
            self.SUBTITLE_OUTPUT_DIR = self.RESOURCE_DIR / "subtitles"
        
        if self.FONT_PATH is None:
            self.FONT_PATH = self.RESOURCE_DIR / "font" / "font.ttf"

        if self.HINDI_FONT_PATH is None:
            self.HINDI_FONT_PATH = self.RESOURCE_DIR / "font" / "hindi.ttf"

        if self.TELUGU_FONT_PATH is None:
            self.TELUGU_FONT_PATH = self.RESOURCE_DIR / "font" / "telugu.ttf"

        if self.INTRO_IMAGE_PATH is None:
            self.INTRO_IMAGE_PATH = self.RESOURCE_DIR / "intro" / "intro.jpg"

        if self.CLIPS_DIR is None:
            self.CLIPS_DIR = self.RESOURCE_DIR / "clips"
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.UPLOAD_FOLDER,
            self.STATIC_DIR / "videos",
            self.RESOURCE_DIR,
            self.SCRIPT_DIR,
            self.IMAGES_DIR,
            self.AUDIO_DIR,
            self.VIDEO_OUTPUT_DIR,
            self.SUBTITLE_OUTPUT_DIR,
            self.RESOURCE_DIR / "font",
            self.RESOURCE_DIR / "intro",
            self.CLIPS_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Create global settings instance
settings = Settings()
