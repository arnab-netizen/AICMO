"""Media buying and optimization domain models.

Stage M: Media Buying & Optimization Engine
Skeleton implementation for managing media campaigns, channels, and optimization actions.
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum

from aicmo.domain.base import AicmoBaseModel


class MediaChannelType(str, Enum):
    """Media channel types."""
    
    SEARCH = "search"
    SOCIAL = "social"
    DISPLAY = "display"
    VIDEO = "video"
    NATIVE = "native"
    AUDIO = "audio"
    OUT_OF_HOME = "out_of_home"
    CONNECTED_TV = "connected_tv"
    PROGRAMMATIC = "programmatic"


class MediaObjective(str, Enum):
    """Media campaign objectives."""
    
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    CONVERSION = "conversion"
    RETENTION = "retention"


class OptimizationActionType(str, Enum):
    """Types of optimization actions."""
    
    BUDGET_SHIFT = "budget_shift"
    BID_ADJUSTMENT = "bid_adjustment"
    TARGETING_REFINEMENT = "targeting_refinement"
    CREATIVE_ROTATION = "creative_rotation"
    SCHEDULE_CHANGE = "schedule_change"
    AUDIENCE_EXPANSION = "audience_expansion"
    PAUSE_CAMPAIGN = "pause_campaign"
    REACTIVATE_CAMPAIGN = "reactivate_campaign"


class MediaChannel(AicmoBaseModel):
    """
    A specific media channel within a campaign.
    
    Represents allocation and targeting for one channel.
    """
    
    channel_type: MediaChannelType
    budget_allocated: float
    budget_spent: float = 0.0
    
    # Targeting
    audience_segments: List[str] = []
    geo_targets: List[str] = []
    
    # Performance (placeholder for future integration)
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    
    # Metadata
    platform: Optional[str] = None  # e.g., "Google Ads", "Meta"
    campaign_id: Optional[str] = None


class MediaCampaignPlan(AicmoBaseModel):
    """
    A complete media campaign plan.
    
    Includes channel mix, budget allocation, targeting strategy.
    Stage M: Skeleton - will be enhanced with real optimization logic later.
    """
    
    campaign_name: str
    brand_name: str
    objective: MediaObjective
    
    total_budget: float
    flight_start: datetime
    flight_end: datetime
    
    channels: List[MediaChannel] = []
    
    # Strategy
    target_audiences: List[str] = []
    key_messages: List[str] = []
    
    # Tracking
    created_at: datetime
    plan_notes: Optional[str] = None


class MediaOptimizationAction(AicmoBaseModel):
    """
    A recommended optimization action for a media campaign.
    
    Stage M: Skeleton - future versions will use ML-driven recommendations.
    """
    
    action_type: OptimizationActionType
    channel_type: MediaChannelType
    
    # Recommendation details
    recommendation: str
    rationale: str
    expected_impact: str
    
    # Actionable parameters
    budget_change: Optional[float] = None
    bid_change_percent: Optional[float] = None
    
    # Tracking
    priority: str = "medium"  # low, medium, high
    status: str = "pending"  # pending, applied, rejected
    created_at: datetime
    applied_at: Optional[datetime] = None


class MediaPerformanceSnapshot(AicmoBaseModel):
    """
    Performance snapshot for a media campaign.
    
    Stage M: Skeleton - will integrate with real analytics later.
    """
    
    campaign_name: str
    snapshot_date: datetime
    
    # Aggregate metrics
    total_spend: float
    total_impressions: int
    total_clicks: int
    total_conversions: int
    
    # Calculated metrics
    ctr: float = 0.0  # click-through rate
    cpc: float = 0.0  # cost per click
    cpa: float = 0.0  # cost per acquisition
    roas: float = 0.0  # return on ad spend
    
    # Channel breakdowns (placeholder)
    channel_performance: dict = {}
