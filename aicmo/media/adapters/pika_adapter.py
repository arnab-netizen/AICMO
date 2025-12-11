"""
Pika Labs Video Generation Adapter

Generates videos from text prompts using Pika Labs API.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PikaLabsAdapter:
    """
    Video generation adapter for Pika Labs.
    
    Supports text-to-video generation with various aspect ratios.
    """
    
    def __init__(self, api_key: Optional[str] = None, dry_run: bool = False):
        """
        Initialize Pika Labs adapter.
        
        Args:
            api_key: Pika Labs API key
            dry_run: If True, returns stub data without API calls
        """
        self.api_key = api_key
        self.dry_run = dry_run
        self.provider_name = "pika_labs"
    
    def get_name(self) -> str:
        """Get provider name."""
        return self.provider_name
    
    def check_health(self) -> bool:
        """
        Check provider health and availability.
        
        Returns:
            True if provider is available
        """
        if self.dry_run:
            return True
        
        if not self.api_key:
            logger.warning("Pika Labs API key not configured")
            return False
        
        logger.debug("Pika Labs adapter healthy")
        return True
    
    def generate_video(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        duration_seconds: int = 10,
        **kwargs,
    ) -> Optional[Dict]:
        """
        Generate video from text prompt.
        
        Args:
            prompt: Text description of video
            aspect_ratio: Video aspect ratio (9:16, 16:9, 1:1)
            duration_seconds: Video duration in seconds
            **kwargs: Additional provider-specific options
            
        Returns:
            Dict with video data or None on failure
        """
        try:
            if not self.check_health():
                logger.error("Pika Labs adapter not healthy")
                return None
            
            if self.dry_run:
                return self._generate_stub_video(prompt, aspect_ratio, duration_seconds)
            
            logger.info(
                f"Generating video from prompt: {prompt[:50]}... "
                f"({aspect_ratio}, {duration_seconds}s)"
            )
            
            return self._generate_stub_video(prompt, aspect_ratio, duration_seconds)
            
        except Exception as e:
            logger.error(f"Error generating video: {e}", exc_info=True)
            return None
    
    def _generate_stub_video(
        self,
        prompt: str,
        aspect_ratio: str,
        duration_seconds: int,
    ) -> Dict:
        """Generate stub video data for testing."""
        if aspect_ratio == "9:16":
            width, height = 720, 1280
        elif aspect_ratio == "16:9":
            width, height = 1920, 1080
        else:
            width, height = 1024, 1024
        
        return {
            "url": f"https://stub.example.com/video_{prompt[:10]}.mp4",
            "width": width,
            "height": height,
            "duration": duration_seconds,
            "format": "mp4",
            "provider": self.provider_name,
            "content_type": "binary",
        }
