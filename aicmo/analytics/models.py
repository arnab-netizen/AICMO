"""
Phase 3: Analytics Models

Dataclasses for analytics, metrics aggregation, and performance analysis.
Consumes publishing metrics from Phase 2 and CRM data from Phase 1.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4


class MetricType(Enum):
    """Types of metrics that can be tracked."""
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    ENGAGEMENTS = "engagements"
    CONVERSIONS = "conversions"
    SHARES = "shares"
    COMMENTS = "comments"
    REPLIES = "replies"
    OPENS = "opens"
    BOUNCES = "bounces"


class AnalyticsStatus(Enum):
    """Status of analytics calculations."""
    PENDING = "pending"
    PROCESSING = "processing"
    CALCULATED = "calculated"
    FAILED = "failed"


@dataclass
class MetricSnapshot:
    """Single point-in-time metric measurement."""
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Metric value cannot be negative: {self.value}")


@dataclass
class ChannelMetrics:
    """Aggregated metrics for a single channel."""
    channel: str
    total_impressions: float = 0.0
    total_clicks: float = 0.0
    total_engagements: float = 0.0
    total_conversions: float = 0.0
    total_shares: float = 0.0
    total_comments: float = 0.0
    
    def ctr(self) -> float:
        """Click-through rate (clicks / impressions)."""
        if self.total_impressions == 0:
            return 0.0
        return self.total_clicks / self.total_impressions
    
    def engagement_rate(self) -> float:
        """Engagement rate (engagements / impressions)."""
        if self.total_impressions == 0:
            return 0.0
        return self.total_engagements / self.total_impressions
    
    def conversion_rate(self) -> float:
        """Conversion rate (conversions / clicks)."""
        if self.total_clicks == 0:
            return 0.0
        return self.total_conversions / self.total_clicks
    
    def add_metric(self, metric_type: MetricType, value: float):
        """Add a metric value."""
        if metric_type == MetricType.IMPRESSIONS:
            self.total_impressions += value
        elif metric_type == MetricType.CLICKS:
            self.total_clicks += value
        elif metric_type == MetricType.ENGAGEMENTS:
            self.total_engagements += value
        elif metric_type == MetricType.CONVERSIONS:
            self.total_conversions += value
        elif metric_type == MetricType.SHARES:
            self.total_shares += value
        elif metric_type == MetricType.COMMENTS:
            self.total_comments += value


@dataclass
class CampaignAnalytics:
    """Analytics for a single campaign."""
    campaign_id: str
    campaign_name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    channel_metrics: Dict[str, ChannelMetrics] = field(default_factory=dict)
    total_content_pieces: int = 0
    total_contacts_targeted: int = 0
    status: AnalyticsStatus = AnalyticsStatus.PENDING
    
    def aggregate_metrics(self) -> ChannelMetrics:
        """Get aggregated metrics across all channels."""
        aggregated = ChannelMetrics(channel="all_channels")
        for channel_metric in self.channel_metrics.values():
            aggregated.total_impressions += channel_metric.total_impressions
            aggregated.total_clicks += channel_metric.total_clicks
            aggregated.total_engagements += channel_metric.total_engagements
            aggregated.total_conversions += channel_metric.total_conversions
            aggregated.total_shares += channel_metric.total_shares
            aggregated.total_comments += channel_metric.total_comments
        return aggregated
    
    def total_roi(self, cost_per_contact: float = 0.0) -> float:
        """
        Calculate total ROI.
        
        Args:
            cost_per_contact: Cost per contact targeted (optional)
            
        Returns:
            ROI as percentage (conversions / cost)
        """
        if self.total_contacts_targeted == 0:
            return 0.0
        total_cost = self.total_contacts_targeted * cost_per_contact
        if total_cost == 0:
            return 0.0
        aggregated = self.aggregate_metrics()
        return (aggregated.total_conversions / total_cost) * 100
    
    def best_performing_channel(self) -> Optional[str]:
        """Get the highest-performing channel by engagement rate."""
        if not self.channel_metrics:
            return None
        best_channel = None
        best_engagement = -1.0
        for channel, metrics in self.channel_metrics.items():
            engagement = metrics.engagement_rate()
            if engagement > best_engagement:
                best_engagement = engagement
                best_channel = channel
        return best_channel
    
    def add_channel_metric(self, channel: str, metric_type: MetricType, value: float):
        """Add a metric for a channel."""
        if channel not in self.channel_metrics:
            self.channel_metrics[channel] = ChannelMetrics(channel=channel)
        self.channel_metrics[channel].add_metric(metric_type, value)


@dataclass
class ContactEngagementScore:
    """Engagement score for a single contact."""
    contact_email: str
    contact_id: Optional[str] = None
    total_engagements: float = 0.0
    total_clicks: float = 0.0
    total_conversions: float = 0.0
    emails_sent: int = 0
    emails_opened: int = 0
    campaigns_engaged: int = 0
    last_engagement_date: Optional[datetime] = None
    
    def engagement_rate(self) -> float:
        """Email open rate."""
        if self.emails_sent == 0:
            return 0.0
        return self.emails_opened / self.emails_sent
    
    def click_rate(self) -> float:
        """Click rate (clicks / opens)."""
        if self.emails_opened == 0:
            return 0.0
        return self.total_clicks / self.emails_opened
    
    def conversion_rate(self) -> float:
        """Conversion rate (conversions / clicks)."""
        if self.total_clicks == 0:
            return 0.0
        return self.total_conversions / self.total_clicks
    
    def lifetime_value_score(self) -> float:
        """
        Calculate contact lifetime value score (0-100).
        Weighted formula:
        - Engagement rate (opens/sends): 40%
        - Conversion rate (conversions/clicks): 40%
        - Number of conversions: 20%
        """
        engagement = self.engagement_rate()  # 0-1
        conversion = self.conversion_rate()  # 0-1
        conversions_normalized = min(1.0, self.total_conversions / 5.0)  # Cap at 5
        
        score = (engagement * 0.4) + (conversion * 0.4) + (conversions_normalized * 0.2)
        return score * 100  # Return 0-100
    
    def engagement_tier(self) -> str:
        """Categorize contact by engagement level."""
        ltv = self.lifetime_value_score()
        if ltv >= 75:
            return "high"
        elif ltv >= 50:
            return "medium"
        elif ltv >= 25:
            return "low"
        else:
            return "inactive"


@dataclass
class AnalyticsReport:
    """Complete analytics report."""
    report_id: str = field(default_factory=lambda: str(uuid4()))
    generated_at: datetime = field(default_factory=datetime.utcnow)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    # Campaign analytics
    campaigns: Dict[str, CampaignAnalytics] = field(default_factory=dict)
    
    # Contact engagement
    contact_scores: Dict[str, ContactEngagementScore] = field(default_factory=dict)
    
    # Summary metrics
    total_campaigns_analyzed: int = 0
    total_contacts_analyzed: int = 0
    total_revenue_generated: float = 0.0
    
    def add_campaign_analytics(self, campaign: CampaignAnalytics):
        """Add campaign analytics to the report."""
        self.campaigns[campaign.campaign_id] = campaign
        self.total_campaigns_analyzed = len(self.campaigns)
    
    def add_contact_score(self, score: ContactEngagementScore):
        """Add contact engagement score to the report."""
        self.contact_scores[score.contact_email] = score
        self.total_contacts_analyzed = len(self.contact_scores)
    
    def overall_roi(self, cost_per_contact: float = 0.0) -> float:
        """Calculate overall ROI across all campaigns."""
        if not self.campaigns:
            return 0.0
        total_roi = sum(
            campaign.total_roi(cost_per_contact)
            for campaign in self.campaigns.values()
        )
        return total_roi / len(self.campaigns) if self.campaigns else 0.0
    
    def top_contacts_by_engagement(self, limit: int = 10) -> List[ContactEngagementScore]:
        """Get top contacts by lifetime value score."""
        sorted_contacts = sorted(
            self.contact_scores.values(),
            key=lambda c: c.lifetime_value_score(),
            reverse=True
        )
        return sorted_contacts[:limit]
    
    def contacts_by_tier(self, tier: str) -> List[ContactEngagementScore]:
        """Get all contacts in a specific engagement tier."""
        return [
            score for score in self.contact_scores.values()
            if score.engagement_tier() == tier
        ]
    
    def summary_stats(self) -> Dict[str, float]:
        """Get summary statistics."""
        if not self.campaigns:
            return {
                "total_campaigns": 0,
                "total_contacts": 0,
                "average_engagement_rate": 0.0,
                "average_conversion_rate": 0.0,
                "total_revenue": 0.0,
            }
        
        # Campaign stats
        total_impressions = sum(
            campaign.aggregate_metrics().total_impressions
            for campaign in self.campaigns.values()
        )
        total_clicks = sum(
            campaign.aggregate_metrics().total_clicks
            for campaign in self.campaigns.values()
        )
        total_conversions = sum(
            campaign.aggregate_metrics().total_conversions
            for campaign in self.campaigns.values()
        )
        
        avg_ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0.0
        avg_conversion = (total_conversions / total_clicks) if total_clicks > 0 else 0.0
        
        return {
            "total_campaigns": self.total_campaigns_analyzed,
            "total_contacts": self.total_contacts_analyzed,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "overall_ctr": avg_ctr,
            "overall_conversion_rate": avg_conversion,
            "total_revenue": self.total_revenue_generated,
        }
