"""Analytics and attribution module.

Stage A: Analytics & Attribution Engine
"""

from aicmo.analytics.domain import (
    AttributionModel,
    MetricType,
    ChannelType,
    TouchPoint,
    ConversionEvent,
    ChannelPerformance,
    AttributionReport,
    MMMAnalysis,
    PerformanceDashboard,
    CampaignAnalysis,
    FunnelAnalysis,
)

from aicmo.analytics.service import (
    calculate_attribution,
    generate_mmm_analysis,
    generate_performance_dashboard,
    analyze_campaign,
)

__all__ = [
    # Enums
    "AttributionModel",
    "MetricType",
    "ChannelType",
    
    # Domain models
    "TouchPoint",
    "ConversionEvent",
    "ChannelPerformance",
    "AttributionReport",
    "MMMAnalysis",
    "PerformanceDashboard",
    "CampaignAnalysis",
    "FunnelAnalysis",
    
    # Service functions
    "calculate_attribution",
    "generate_mmm_analysis",
    "generate_performance_dashboard",
    "analyze_campaign",
]
