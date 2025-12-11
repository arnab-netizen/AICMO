"""
Canva API Adapter - Canva design platform integration.

Stub implementation for future integration.
Currently returns None to fall through to other providers.
"""

from typing import Optional
import logging
from ..generators.provider_chain import MediaGeneratorProvider, GeneratedImage

logger = logging.getLogger(__name__)


class CanvaAPIAdapter(MediaGeneratorProvider):
    """Canva API integration provider (stub)."""
    
    def __init__(self, api_key: Optional[str] = None, dry_run: bool = True):
        """
        Initialize Canva adapter.
        
        Args:
            api_key: Canva API key (optional)
            dry_run: If True, return stub data without API calls
        """
        self.api_key = api_key
        self.dry_run = dry_run
        # Canva is not yet implemented, always unhealthy
        self._healthy = False
    
    def get_name(self) -> str:
        """Get provider name."""
        return "canva_api"
    
    async def check_health(self) -> bool:
        """Check if provider is healthy."""
        # Canva is not yet implemented
        return self._healthy
    
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        **kwargs,
    ) -> Optional[GeneratedImage]:
        """
        Canva integration stub - not yet implemented.
        
        Returns None to fall through to next provider in chain.
        """
        logger.debug("Canva: Not yet implemented, skipping")
        return None
