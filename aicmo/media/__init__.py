"""Media module - Buying, Optimization, and Asset Management.

Stage M: Media Buying & Optimization Engine
Phase 4: Media Asset Management
"""

from aicmo.media.domain import (
    MediaChannel,
    MediaChannelType,
    MediaObjective,
    MediaCampaignPlan,
    MediaOptimizationAction,
    OptimizationActionType,
    MediaPerformanceSnapshot,
)

from aicmo.media.service import (
    generate_media_plan,
    generate_optimization_actions,
)

# Phase 4: Media Management imports
from aicmo.media.models import (
    MediaType,
    ImageFormat,
    VideoFormat,
    MediaStatus,
    MediaDimensions,
    MediaMetadata,
    MediaAsset,
    MediaVariant,
    MediaLibrary,
    MediaPerformance,
    MediaOptimizationSuggestion,
)

from aicmo.media.engine import (
    MediaEngine,
    get_media_engine,
    reset_media_engine,
    create_library,
    add_asset,
    track_performance,
    get_performance,
    suggest_optimization,
)

__all__ = [
    # Existing - Media Buying
    "MediaChannel",
    "MediaChannelType",
    "MediaObjective",
    "MediaCampaignPlan",
    "MediaOptimizationAction",
    "OptimizationActionType",
    "MediaPerformanceSnapshot",
    "generate_media_plan",
    "generate_optimization_actions",
    
    # Phase 4: Media Management - Enums
    "MediaType",
    "ImageFormat",
    "VideoFormat",
    "MediaStatus",
    
    # Phase 4: Media Management - Models
    "MediaDimensions",
    "MediaMetadata",
    "MediaAsset",
    "MediaVariant",
    "MediaLibrary",
    "MediaPerformance",
    "MediaOptimizationSuggestion",
    
    # Phase 4: Media Management - Engine
    "MediaEngine",
    "get_media_engine",
    "reset_media_engine",
    "create_library",
    "add_asset",
    "track_performance",
    "get_performance",
    "suggest_optimization",
]
