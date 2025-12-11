"""
Figma API Adapter - Figma design platform integration.

Supports:
- Image export to Figma
- Frame/page insertion
- Asset upload

Implements both generate_image (optional) and export_to_figma (required).
"""

from typing import Optional
import logging
from ..generators.provider_chain import (
    MediaGeneratorProvider,
    GeneratedImage,
    FigmaExportResult,
)

logger = logging.getLogger(__name__)


class FigmaAPIAdapter(MediaGeneratorProvider):
    """Figma API integration provider."""
    
    def __init__(self, api_token: Optional[str] = None, dry_run: bool = True):
        """
        Initialize Figma adapter.
        
        Args:
            api_token: Figma personal access token (optional)
            dry_run: If True, return stub data without API calls
        """
        self.api_token = api_token
        self.dry_run = dry_run
        self._healthy = bool(api_token)
    
    def get_name(self) -> str:
        """Get provider name."""
        return "figma_api"
    
    async def check_health(self) -> bool:
        """
        Check if Figma provider is healthy.
        
        Returns False if no token configured.
        """
        if not self.api_token:
            logger.warning("Figma: No API token configured")
            return False
        return self._healthy
    
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        **kwargs,
    ) -> Optional[GeneratedImage]:
        """
        Figma doesn't generate images - this is a stub.
        
        Returns None to indicate this provider doesn't support generation.
        """
        logger.debug("Figma: generate_image not supported, skipping")
        return None
    
    async def export_to_figma(
        self,
        image: GeneratedImage,
        file_key: str,
        page_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[FigmaExportResult]:
        """
        Export generated image to Figma file.
        
        In dry_run mode, returns predictable stub export result.
        In production, would:
        1. Upload image to Figma
        2. Create frame with image
        3. Insert into specified page
        
        Args:
            image: Generated image to export
            file_key: Figma file key
            page_id: Figma page ID (optional, uses first page if not provided)
            **kwargs: Additional options (frame_name, position, etc)
            
        Returns:
            FigmaExportResult with node_id and URL
        """
        if not self.api_token:
            logger.error("Figma: Cannot export without API token")
            return None
        
        if self.dry_run:
            # Return predictable stub export result
            logger.info(f"Figma (dry-run): Exporting image to file {file_key}")
            return FigmaExportResult(
                figma_node_id=f"node_{file_key[:8]}_{page_id or 'default'}_001",
                figma_url=f"https://figma.com/file/{file_key}?node-id={file_key[:8]}%3A{page_id or '1'}",
                figma_file_key=file_key,
                page_id=page_id,
                metadata={
                    "provider": "figma_api",
                    "image_format": image.format,
                    "image_width": image.width,
                    "image_height": image.height,
                    "frame_name": kwargs.get("frame_name", f"Generated {image.width}x{image.height}"),
                },
            )
        
        # Production: Would call Figma API
        logger.warning("Figma: Real API calls not implemented (dry_run=False)")
        return None
