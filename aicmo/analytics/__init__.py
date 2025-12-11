"""Analytics and attribution module.

Stage A: Analytics & Attribution Engine
Phase 3: Analytics & Aggregation System
"""

from aicmo.analytics.domain import (
    AttributionModel,
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

# Phase 3: Analytics models and engine
from aicmo.analytics.models import (
    MetricType,
    AnalyticsStatus,
    MetricSnapshot,
    ChannelMetrics,
    CampaignAnalytics,
    ContactEngagementScore,
    AnalyticsReport,
)

from aicmo.analytics.engine import (
    AnalyticsEngine,
    get_analytics_engine,
    reset_analytics_engine,
    create_report,
    add_campaign,
    add_metrics,
    score_contact,
    finalize_report,
)

__all__ = [
    # Attribution Enums
    "AttributionModel",
    "ChannelType",
    
    # Attribution Domain models
    "TouchPoint",
    "ConversionEvent",
    "ChannelPerformance",
    "AttributionReport",
    "MMMAnalysis",
    "PerformanceDashboard",
    "CampaignAnalysis",
    "FunnelAnalysis",
    
    # Attribution Service functions
    "calculate_attribution",
    "generate_mmm_analysis",
    "generate_performance_dashboard",
    "analyze_campaign",
    
    # Phase 3: Analytics Enums
    "MetricType",
    "AnalyticsStatus",
    
    # Phase 3: Analytics Models
    "MetricSnapshot",
    "ChannelMetrics",
    "CampaignAnalytics",
    "ContactEngagementScore",
    "AnalyticsReport",
    
    # Phase 3: Analytics Engine
    "AnalyticsEngine",
    "get_analytics_engine",
    "reset_analytics_engine",
    "create_report",
    "add_campaign",
    "add_metrics",
    "score_contact",
    "finalize_report",
]
