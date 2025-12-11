"""
No-op Media Adapter - Safe fallback for media generation.

Always returns stub images in healthy state.
Ensures system never crashes due to missing providers.
"""

from typing import Optional
import logging
from ..generators.provider_chain import MediaGeneratorProvider, GeneratedImage

logger = logging.getLogger(__name__)


class NoOpMediaAdapter(MediaGeneratorProvider):
    """No-op media generation provider (safe fallback)."""
    
    def __init__(self, **kwargs):
        """Initialize no-op adapter."""
        self._healthy = True
    
    def get_name(self) -> str:
        """Get provider name."""
        return "noop_media"
    
    async def check_health(self) -> bool:
        """Always healthy."""
        return self._healthy
    
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        **kwargs,
    ) -> Optional[GeneratedImage]:
        """
        Generate stub image (always succeeds).
        
        Safe fallback when all other providers fail.
        
        Args:
            prompt: Image prompt
            width: Width (default 1024)
            height: Height (default 1024)
            **kwargs: Ignored
            
        Returns:
            GeneratedImage with stub data
        """
        logger.info(f"NoOp: Generating stub {width}x{height} image")
        return GeneratedImage(
            content=b"NOOP_STUB_IMAGE_DATA",
            content_type="binary",
            format="png",
            width=width,
            height=height,
            metadata={
                "provider": "noop_media",
                "prompt": prompt,
                "warning": "This is a stub image (no real generation)",
            },
            provider_name="noop_media",
        )
