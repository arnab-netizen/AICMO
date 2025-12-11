"""
Phase 4.5: Media Generator Provider Chain

Multi-provider media generation with automatic failover and health tracking.
Extends Phase 0 ProviderChain for media generation capabilities.

Supports:
- SDXL
- OpenAI Images  
- Flux Models
- Replicate SDXL
- Figma API (export + insert)
- Canva (stub)
- No-op stub

All providers support dry_run mode (no real API calls).
All methods use dynamic dispatch (no if/elif routing).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeneratedImage:
    """Result from image generation provider."""
    
    # Either 'binary' (bytes) or 'url' (str)
    content: Any  # bytes or str
    content_type: str  # 'binary' or 'url'
    format: str  # jpeg, png, webp, etc
    width: int
    height: int
    metadata: Dict[str, Any]  # provider-specific metadata
    provider_name: str


@dataclass
class FigmaExportResult:
    """Result from Figma export operation."""
    
    figma_node_id: str
    figma_url: str
    figma_file_key: str
    page_id: Optional[str]
    metadata: Dict[str, Any]


class MediaGeneratorProvider(ABC):
    """
    Base interface for media generation providers.
    
    All providers must implement:
    - generate_image()
    - check_health()
    - get_name()
    
    Figma-specific providers also implement:
    - export_to_figma()
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """Get provider name."""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Check if provider is healthy."""
        pass
    
    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        **kwargs,
    ) -> Optional[GeneratedImage]:
        """
        Generate image from prompt.
        
        Args:
            prompt: Text description
            width: Image width
            height: Image height
            **kwargs: Provider-specific options
            
        Returns:
            GeneratedImage or None on failure
        """
        pass
    
    async def export_to_figma(
        self,
        image: GeneratedImage,
        file_key: str,
        page_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[FigmaExportResult]:
        """
        Export generated image to Figma (optional).
        
        Only implemented by Figma providers.
        
        Args:
            image: Generated image to export
            file_key: Figma file key
            page_id: Figma page ID (optional)
            **kwargs: Provider-specific options
            
        Returns:
            FigmaExportResult or None
        """
        return None


class MediaGeneratorChain:
    """
    Chain of media generation providers with automatic failover.
    
    Uses dynamic dispatch - wraps providers and calls methods
    using getattr() instead of hard-coded routing.
    """
    
    def __init__(self, providers: list, dry_run: bool = False):
        """
        Initialize chain with ordered list of providers.
        
        Args:
            providers: List of MediaGeneratorProvider instances
            dry_run: If True, providers return stub data
        """
        self.providers = providers
        self.dry_run = dry_run
        self._provider_health: Dict[str, bool] = {}
    
    async def execute_generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        **kwargs,
    ) -> Optional[GeneratedImage]:
        """
        Execute generate_image across provider chain with fallback.
        
        Args:
            prompt: Image prompt
            width: Width
            height: Height
            **kwargs: Provider-specific options
            
        Returns:
            GeneratedImage from first successful provider, or None
        """
        for provider in self.providers:
            try:
                # Dynamic dispatch - no hard-coded routing
                method = getattr(provider, "generate_image", None)
                if not callable(method):
                    logger.warning(
                        f"Provider {provider.get_name()} missing generate_image()"
                    )
                    continue
                
                # Call with dynamic signature
                result = await method(
                    prompt=prompt,
                    width=width,
                    height=height,
                    **kwargs,
                )
                
                if result:
                    logger.info(
                        f"Successfully generated image using {provider.get_name()}"
                    )
                    self._provider_health[provider.get_name()] = True
                    return result
            except Exception as e:
                logger.warning(
                    f"Provider {provider.get_name()} failed: {e}"
                )
                self._provider_health[provider.get_name()] = False
                continue
        
        logger.error("All providers in chain failed for generate_image")
        return None
    
    async def execute_export_figma(
        self,
        image: GeneratedImage,
        file_key: str,
        page_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[FigmaExportResult]:
        """
        Execute export_to_figma across provider chain with fallback.
        
        Args:
            image: Image to export
            file_key: Figma file key
            page_id: Figma page ID
            **kwargs: Provider-specific options
            
        Returns:
            FigmaExportResult from first successful provider, or None
        """
        for provider in self.providers:
            try:
                # Dynamic dispatch
                method = getattr(provider, "export_to_figma", None)
                if not callable(method):
                    logger.debug(
                        f"Provider {provider.get_name()} missing export_to_figma()"
                    )
                    continue
                
                # Call with dynamic signature
                result = await method(
                    image=image,
                    file_key=file_key,
                    page_id=page_id,
                    **kwargs,
                )
                
                if result:
                    logger.info(
                        f"Successfully exported to Figma using {provider.get_name()}"
                    )
                    self._provider_health[provider.get_name()] = True
                    return result
            except Exception as e:
                logger.warning(
                    f"Provider {provider.get_name()} export failed: {e}"
                )
                self._provider_health[provider.get_name()] = False
                continue
        
        logger.error("All providers in chain failed for export_to_figma")
        return None
    
    def get_provider_health(self) -> Dict[str, bool]:
        """Get health status of all providers in chain."""
        return dict(self._provider_health)
