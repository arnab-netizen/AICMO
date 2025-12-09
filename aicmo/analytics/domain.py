"""Analytics and attribution domain models.

Stage A: Analytics & Attribution Engine
Skeleton implementation for performance tracking, attribution modeling, and MMM-lite analysis.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from aicmo.domain.base import AicmoBaseModel


class AttributionModel(str, Enum):
    """Attribution model types."""
    
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"
    DATA_DRIVEN = "data_driven"


class MetricType(str, Enum):
    """Performance metric types."""
    
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    REVENUE = "revenue"
    COST = "cost"
    ROAS = "roas"
    CPA = "cpa"
    CTR = "ctr"
    CVR = "cvr"


class ChannelType(str, Enum):
    """Marketing channel types."""
    
    PAID_SEARCH = "paid_search"
    PAID_SOCIAL = "paid_social"
    DISPLAY = "display"
    VIDEO = "video"
    EMAIL = "email"
    ORGANIC_SEARCH = "organic_search"
    ORGANIC_SOCIAL = "organic_social"
    DIRECT = "direct"
    REFERRAL = "referral"


class TouchPoint(AicmoBaseModel):
    """
    A single marketing touchpoint in a customer journey.
    
    Stage A: Skeleton for attribution tracking.
    """
    
    touchpoint_id: str
    customer_id: str
    
    # Channel
    channel: ChannelType
    campaign_name: Optional[str] = None
    campaign_id: Optional[str] = None
    
    # Interaction
    timestamp: datetime
    interaction_type: str = "view"  # view, click, engagement
    
    # Attribution
    attributed_value: float = 0.0
    attribution_weight: float = 0.0  # 0-1
    
    # Metadata
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    device: Optional[str] = None


class ConversionEvent(AicmoBaseModel):
    """
    A conversion event for attribution analysis.
    
    Stage A: Skeleton for conversion tracking.
    """
    
    conversion_id: str
    customer_id: str
    
    # Conversion details
    conversion_type: str  # purchase, signup, lead, etc.
    conversion_value: float
    timestamp: datetime
    
    # Attribution
    touchpoints: List[TouchPoint] = []
    primary_channel: Optional[ChannelType] = None
    
    # Metadata
    order_id: Optional[str] = None
    product_ids: List[str] = []


class ChannelPerformance(AicmoBaseModel):
    """
    Performance metrics for a marketing channel.
    
    Stage A: Skeleton for channel analysis.
    """
    
    channel: ChannelType
    brand_name: str
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Metrics
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    cost: float = 0.0
    revenue: float = 0.0
    
    # Calculated KPIs
    ctr: float = 0.0  # Click-through rate
    cvr: float = 0.0  # Conversion rate
    cpa: float = 0.0  # Cost per acquisition
    roas: float = 0.0  # Return on ad spend
    
    # Attribution
    attributed_conversions: float = 0.0
    attribution_model: Optional[AttributionModel] = None


class AttributionReport(AicmoBaseModel):
    """
    Attribution analysis report.
    
    Stage A: Skeleton for multi-touch attribution.
    """
    
    report_id: str
    brand_name: str
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Model
    attribution_model: AttributionModel
    
    # Results
    channel_performance: List[ChannelPerformance] = []
    total_conversions: int = 0
    total_revenue: float = 0.0
    total_cost: float = 0.0
    overall_roas: float = 0.0
    
    # Insights
    top_performing_channels: List[ChannelType] = []
    underperforming_channels: List[ChannelType] = []
    
    # Generated
    generated_at: datetime


class MMMAnalysis(AicmoBaseModel):
    """
    Marketing Mix Modeling (MMM) lite analysis.
    
    Stage A: Skeleton for channel contribution analysis.
    """
    
    analysis_id: str
    brand_name: str
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Channel contributions
    channel_contributions: Dict[str, float] = {}  # Channel -> % contribution
    channel_elasticity: Dict[str, float] = {}  # Channel -> elasticity score
    
    # Budget optimization
    recommended_budget_allocation: Dict[str, float] = {}  # Channel -> budget %
    predicted_roi_by_channel: Dict[str, float] = {}  # Channel -> predicted ROI
    
    # Insights
    saturation_points: Dict[str, float] = {}  # Channel -> saturation spend
    synergy_effects: List[str] = []  # Channel combinations with synergy
    
    # Model quality
    model_r_squared: float = 0.0
    confidence_level: float = 0.0
    
    # Generated
    generated_at: datetime


class PerformanceDashboard(AicmoBaseModel):
    """
    Real-time performance dashboard data.
    
    Stage A: Skeleton for live monitoring.
    """
    
    dashboard_id: str
    brand_name: str
    
    # Current period
    current_period_start: datetime
    current_period_end: datetime
    
    # Metrics
    current_metrics: Dict[str, Any] = {}  # Metric name -> value
    
    # Comparisons
    previous_period_metrics: Dict[str, Any] = {}
    percent_changes: Dict[str, float] = {}  # Metric -> % change
    
    # Goals
    goals: Dict[str, float] = {}  # Metric -> goal value
    goal_progress: Dict[str, float] = {}  # Metric -> % of goal achieved
    
    # Trends
    trending_up: List[str] = []  # Metric names
    trending_down: List[str] = []
    
    # Alerts
    critical_issues: List[str] = []
    opportunities: List[str] = []
    
    # Updated
    last_updated: datetime


class CampaignAnalysis(AicmoBaseModel):
    """
    Detailed campaign performance analysis.
    
    Stage A: Skeleton for campaign evaluation.
    """
    
    analysis_id: str
    brand_name: str
    campaign_id: str
    campaign_name: str
    
    # Duration
    start_date: datetime
    end_date: datetime
    
    # Performance
    total_spend: float = 0.0
    total_revenue: float = 0.0
    total_conversions: int = 0
    
    # Efficiency
    cpa: float = 0.0
    roas: float = 0.0
    roi: float = 0.0
    
    # Channel breakdown
    channel_performance: List[ChannelPerformance] = []
    
    # Audience insights
    top_performing_audiences: List[str] = []
    audience_overlap: Dict[str, float] = {}
    
    # Creative performance
    top_performing_creatives: List[str] = []
    creative_fatigue_indicators: List[str] = []
    
    # Recommendations
    optimization_recommendations: List[str] = []
    
    # Generated
    generated_at: datetime


class FunnelAnalysis(AicmoBaseModel):
    """
    Marketing funnel analysis.
    
    Stage A: Skeleton for conversion funnel tracking.
    """
    
    analysis_id: str
    brand_name: str
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Funnel stages
    funnel_stages: List[str] = []  # e.g., ["Awareness", "Consideration", "Conversion"]
    stage_volumes: Dict[str, int] = {}  # Stage -> count
    stage_conversion_rates: Dict[str, float] = {}  # Stage -> conversion %
    
    # Drop-off analysis
    biggest_drop_offs: List[str] = []  # Stage names with highest drop-off
    drop_off_reasons: Dict[str, List[str]] = {}  # Stage -> reasons
    
    # Channel performance by stage
    channel_performance_by_stage: Dict[str, Dict[str, float]] = {}
    
    # Recommendations
    optimization_opportunities: List[str] = []
    
    # Generated
    generated_at: datetime
