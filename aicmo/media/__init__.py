"""Media buying and optimization module.

Stage M: Media Buying & Optimization Engine
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

__all__ = [
    # Domain models
    "MediaChannel",
    "MediaChannelType",
    "MediaObjective",
    "MediaCampaignPlan",
    "MediaOptimizationAction",
    "OptimizationActionType",
    "MediaPerformanceSnapshot",
    
    # Service functions
    "generate_media_plan",
    "generate_optimization_actions",
]
