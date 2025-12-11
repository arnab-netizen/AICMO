"""
No-op Video Generation Adapter

Safe fallback adapter that always returns predictable stub video data.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class NoOpVideoAdapter:
    """
    Safe fallback adapter for video generation.
    
    Always returns predictable stub video data.
    Used as final fallback in provider chain.
    """
    
    def __init__(self, **kwargs):
        """Initialize no-op adapter (accepts any kwargs for compatibility)."""
        self.provider_name = "noop_video"
    
    def get_name(self) -> str:
        """Get provider name."""
        return self.provider_name
    
    def check_health(self) -> bool:
        """
        Always returns healthy (safe fallback).
        
        Returns:
            True always
        """
        return True
    
    def generate_video(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        duration_seconds: int = 10,
        **kwargs,
    ) -> Optional[Dict]:
        """
        Generate stub video data.
        
        Args:
            prompt: Text description of video (ignored)
            aspect_ratio: Video aspect ratio
            duration_seconds: Video duration in seconds
            **kwargs: Additional options (ignored)
            
        Returns:
            Dict with predictable stub video data
        """
        try:
            # Parse aspect ratio
            if aspect_ratio == "9:16":
                width, height = 720, 1280
            elif aspect_ratio == "16:9":
                width, height = 1920, 1080
            elif aspect_ratio == "1:1":
                width, height = 1024, 1024
            else:
                width, height = 1024, 1024
            
            # Always return predictable stub
            return {
                "url": f"https://stub.example.com/noop_video_{duration_seconds}s.mp4",
                "width": width,
                "height": height,
                "duration": min(duration_seconds, 120),
                "format": "mp4",
                "provider": self.provider_name,
                "content_type": "binary",
                "is_stub": True,
            }
            
        except Exception as e:
            logger.error(f"Error in no-op adapter: {e}")
            return None
