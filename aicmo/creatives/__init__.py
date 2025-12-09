"""Creatives module for AICMO."""

from aicmo.creatives.mockups import build_mockup_zip_from_report
from aicmo.creatives.service import (
    generate_creatives,
    CreativeLibrary,
    # Stage C: Advanced Creative Production
    generate_video_storyboard,
    generate_moodboard,
    generate_motion_graphics_spec,
    create_creative_project,
)

# Stage C: Advanced Creative Production
from aicmo.creatives.domain import (
    CreativeType,
    VideoStyle,
    AspectRatio,
    VideoSpec,
    MotionGraphicsSpec,
    MoodboardItem,
    Moodboard,
    Storyboard,
    CreativeAsset,
    CreativeProject,
)

__all__ = [
    # Existing
    "build_mockup_zip_from_report",
    "generate_creatives",
    "CreativeLibrary",
    
    # Stage C: Service functions
    "generate_video_storyboard",
    "generate_moodboard",
    "generate_motion_graphics_spec",
    "create_creative_project",
    
    # Stage C: Domain models
    "CreativeType",
    "VideoStyle",
    "AspectRatio",
    "VideoSpec",
    "MotionGraphicsSpec",
    "MoodboardItem",
    "Moodboard",
    "Storyboard",
    "CreativeAsset",
    "CreativeProject",
]


