"""Creative production interface.

Stage C: Advanced Creative Production Engine
Abstract interface for video generation, motion graphics, and asset production tools.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from aicmo.creatives.domain import (
    VideoSpec,
    MotionGraphicsSpec,
    Moodboard,
    Storyboard,
    CreativeAsset,
)


class CreativeProducer(ABC):
    """
    Abstract interface for creative production tools.
    
    Stage C: Skeleton interface - implement concrete adapters for:
    - Runway ML (video generation)
    - Synthesia (AI video)
    - Canva API (graphics)
    - Adobe Creative Cloud APIs
    - Midjourney/DALL-E (image generation)
    - etc.
    
    Future: Add real creative tool integration here.
    """
    
    @abstractmethod
    def generate_video(
        self,
        spec: VideoSpec,
        storyboard: Optional[Storyboard] = None
    ) -> CreativeAsset:
        """
        Generate a video asset from specifications.
        
        Args:
            spec: Video specifications
            storyboard: Optional storyboard for guidance
            
        Returns:
            CreativeAsset with video details
            
        Raises:
            NotImplementedError: Stage C skeleton
        """
        raise NotImplementedError("Stage C: Video generation integration pending")
    
    @abstractmethod
    def generate_motion_graphics(
        self,
        spec: MotionGraphicsSpec
    ) -> CreativeAsset:
        """
        Generate motion graphics from specifications.
        
        Args:
            spec: Motion graphics specifications
            
        Returns:
            CreativeAsset with motion graphics details
            
        Raises:
            NotImplementedError: Stage C skeleton
        """
        raise NotImplementedError("Stage C: Motion graphics integration pending")
    
    @abstractmethod
    def generate_moodboard_images(
        self,
        keywords: List[str],
        aesthetic: str,
        num_images: int = 8
    ) -> List[str]:
        """
        Generate or search for moodboard inspiration images.
        
        Args:
            keywords: Search/generation keywords
            aesthetic: Overall aesthetic direction
            num_images: Number of images to generate/find
            
        Returns:
            List of image URLs
            
        Raises:
            NotImplementedError: Stage C skeleton
        """
        raise NotImplementedError("Stage C: Image generation integration pending")
    
    @abstractmethod
    def render_asset(
        self,
        asset_id: str,
        format: str = "mp4"
    ) -> str:
        """
        Render a creative asset to final format.
        
        Args:
            asset_id: Asset identifier
            format: Output format (mp4, png, jpg, gif)
            
        Returns:
            URL to rendered asset
            
        Raises:
            NotImplementedError: Stage C skeleton
        """
        raise NotImplementedError("Stage C: Asset rendering integration pending")
    
    @abstractmethod
    def export_storyboard(
        self,
        storyboard: Storyboard,
        format: str = "pdf"
    ) -> str:
        """
        Export storyboard to shareable format.
        
        Args:
            storyboard: Storyboard to export
            format: Export format (pdf, pptx, etc.)
            
        Returns:
            URL to exported storyboard
            
        Raises:
            NotImplementedError: Stage C skeleton
        """
        raise NotImplementedError("Stage C: Storyboard export integration pending")
    
    @abstractmethod
    def get_asset_status(self, asset_id: str) -> Dict[str, Any]:
        """
        Get production status for an asset.
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            Status information (progress, errors, etc.)
            
        Raises:
            NotImplementedError: Stage C skeleton
        """
        raise NotImplementedError("Stage C: Asset status tracking pending")
