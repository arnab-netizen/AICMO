"""Advanced creative production domain models.

Stage C: Advanced Creative Production Engine
Skeleton implementation for video, motion graphics, and moodboard generation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from aicmo.domain.base import AicmoBaseModel


class CreativeType(str, Enum):
    """Types of creative assets."""
    
    VIDEO = "video"
    MOTION_GRAPHICS = "motion_graphics"
    STATIC_IMAGE = "static_image"
    CAROUSEL = "carousel"
    MOODBOARD = "moodboard"
    STORYBOARD = "storyboard"


class VideoStyle(str, Enum):
    """Video production styles."""
    
    LIVE_ACTION = "live_action"
    ANIMATION_2D = "animation_2d"
    ANIMATION_3D = "animation_3d"
    MOTION_GRAPHICS = "motion_graphics"
    MIXED_MEDIA = "mixed_media"
    KINETIC_TYPOGRAPHY = "kinetic_typography"


class AspectRatio(str, Enum):
    """Common aspect ratios for creative assets."""
    
    SQUARE = "1:1"  # Instagram, Facebook feed
    VERTICAL = "9:16"  # Stories, Reels, TikTok
    HORIZONTAL = "16:9"  # YouTube, landscape video
    WIDE = "21:9"  # Cinematic
    PORTRAIT = "4:5"  # Instagram portrait


class VideoSpec(AicmoBaseModel):
    """
    Video creative specifications.
    
    Stage C: Skeleton - will integrate with video generation APIs later.
    """
    
    duration_seconds: int
    aspect_ratio: AspectRatio
    style: VideoStyle
    
    # Technical specs
    fps: int = 30
    resolution: str = "1080p"  # 1080p, 4K, etc.
    
    # Content structure
    scenes: List[str] = []  # Scene descriptions
    voiceover_script: Optional[str] = None
    music_style: Optional[str] = None
    
    # Platform targeting
    target_platform: Optional[str] = None  # "YouTube", "Instagram", "TikTok"


class MotionGraphicsSpec(AicmoBaseModel):
    """
    Motion graphics specifications.
    
    Stage C: Skeleton for animated graphics and transitions.
    """
    
    duration_seconds: int
    aspect_ratio: AspectRatio
    
    # Content
    key_messages: List[str] = []
    data_points: List[Dict[str, Any]] = []  # For data visualization
    
    # Style
    color_palette: List[str] = []  # Hex colors
    animation_style: str = "smooth"  # smooth, energetic, minimal
    typography_style: str = "modern"  # modern, classic, bold
    
    # Technical
    fps: int = 30
    loop: bool = False


class MoodboardItem(AicmoBaseModel):
    """Single item in a moodboard."""
    
    image_url: Optional[str] = None
    image_description: str
    category: str  # "color", "typography", "imagery", "layout", "texture"
    notes: Optional[str] = None


class Moodboard(AicmoBaseModel):
    """
    Creative moodboard for brand/campaign inspiration.
    
    Stage C: Skeleton - will integrate with image search/generation APIs.
    """
    
    title: str
    brand_name: str
    purpose: str  # "Brand identity", "Campaign concept", etc.
    
    items: List[MoodboardItem] = []
    
    # Style direction
    overall_aesthetic: str
    color_palette: List[str] = []
    keywords: List[str] = []
    
    created_at: datetime


class Storyboard(AicmoBaseModel):
    """
    Video storyboard with scene-by-scene breakdown.
    
    Stage C: Skeleton for video planning.
    """
    
    title: str
    brand_name: str
    video_purpose: str
    
    total_duration_seconds: int
    aspect_ratio: AspectRatio
    
    scenes: List[Dict[str, Any]] = []  # Each scene with timing, description, visuals, audio
    
    creative_notes: Optional[str] = None
    production_notes: Optional[str] = None
    
    created_at: datetime


class CreativeAsset(AicmoBaseModel):
    """
    A produced creative asset.
    
    Stage C: Skeleton - tracks generated or produced assets.
    """
    
    asset_id: str
    creative_type: CreativeType
    brand_name: str
    
    # Asset details
    title: str
    description: Optional[str] = None
    
    # File info (placeholders for future integration)
    file_url: Optional[str] = None
    file_format: Optional[str] = None  # mp4, png, jpg, gif
    file_size_mb: Optional[float] = None
    
    # Specifications
    video_spec: Optional[VideoSpec] = None
    motion_spec: Optional[MotionGraphicsSpec] = None
    
    # Metadata
    tags: List[str] = []
    status: str = "draft"  # draft, in_production, completed, archived
    
    created_at: datetime
    updated_at: Optional[datetime] = None


class CreativeProject(AicmoBaseModel):
    """
    A creative production project with multiple assets.
    
    Stage C: Skeleton for managing creative workflows.
    """
    
    project_id: str
    brand_name: str
    project_name: str
    campaign_name: Optional[str] = None
    
    # Project scope
    deliverables: List[str] = []  # List of required asset types
    moodboard: Optional[Moodboard] = None
    
    # Assets
    assets: List[CreativeAsset] = []
    
    # Timeline
    created_at: datetime
    due_date: Optional[datetime] = None
    
    # Status
    status: str = "planning"  # planning, in_production, review, completed
    notes: Optional[str] = None
