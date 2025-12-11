"""
Phase 3: Analytics Engine

Aggregates metrics from publishing (Phase 2) and CRM (Phase 1) into analytics.
Provides campaign analysis, contact scoring, and performance reporting.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .models import (
    CampaignAnalytics,
    ContactEngagementScore,
    AnalyticsReport,
    MetricType,
    AnalyticsStatus,
)

# Module-level singleton for testing
_analytics_engine: Optional["AnalyticsEngine"] = None


class AnalyticsEngine:
    """Main analytics engine for aggregating campaign and contact metrics."""
    
    def __init__(self):
        """Initialize analytics engine."""
        self.reports: Dict[str, AnalyticsReport] = {}
        self.campaigns: Dict[str, CampaignAnalytics] = {}
        self.contact_scores: Dict[str, ContactEngagementScore] = {}
    
    def create_report(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> AnalyticsReport:
        """
        Create a new analytics report for a time period.
        
        Args:
            period_start: Start of analysis period
            period_end: End of analysis period
            
        Returns:
            New AnalyticsReport
        """
        report = AnalyticsReport(
            period_start=period_start,
            period_end=period_end,
        )
        self.reports[report.report_id] = report
        return report
    
    def add_campaign_to_report(
        self,
        report: AnalyticsReport,
        campaign_id: str,
        campaign_name: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        total_contacts: int = 0,
    ) -> CampaignAnalytics:
        """
        Add campaign analytics to a report.
        
        Args:
            report: Target report
            campaign_id: Unique campaign ID
            campaign_name: Human-readable campaign name
            start_date: Campaign start date
            end_date: Campaign end date
            total_contacts: Number of contacts targeted
            
        Returns:
            CampaignAnalytics object
        """
        campaign = CampaignAnalytics(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            start_date=start_date,
            end_date=end_date,
            total_contacts_targeted=total_contacts,
        )
        self.campaigns[campaign_id] = campaign
        report.add_campaign_analytics(campaign)
        return campaign
    
    def add_publishing_metrics(
        self,
        campaign_id: str,
        channel: str,
        impressions: float = 0.0,
        clicks: float = 0.0,
        engagements: float = 0.0,
        conversions: float = 0.0,
        shares: float = 0.0,
        comments: float = 0.0,
    ):
        """
        Add publishing metrics from Phase 2 to campaign analytics.
        
        Args:
            campaign_id: Campaign ID
            channel: Publishing channel (LinkedIn, Twitter, Email, etc.)
            impressions: Number of impressions
            clicks: Number of clicks
            engagements: Number of engagements
            conversions: Number of conversions
            shares: Number of shares
            comments: Number of comments
        """
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        if impressions > 0:
            campaign.add_channel_metric(channel, MetricType.IMPRESSIONS, impressions)
        if clicks > 0:
            campaign.add_channel_metric(channel, MetricType.CLICKS, clicks)
        if engagements > 0:
            campaign.add_channel_metric(channel, MetricType.ENGAGEMENTS, engagements)
        if conversions > 0:
            campaign.add_channel_metric(channel, MetricType.CONVERSIONS, conversions)
        if shares > 0:
            campaign.add_channel_metric(channel, MetricType.SHARES, shares)
        if comments > 0:
            campaign.add_channel_metric(channel, MetricType.COMMENTS, comments)
    
    def score_contact_engagement(
        self,
        contact_email: str,
        contact_id: Optional[str] = None,
        emails_sent: int = 0,
        emails_opened: int = 0,
        total_clicks: float = 0.0,
        total_conversions: float = 0.0,
        campaigns_engaged: int = 0,
        last_engagement_date: Optional[datetime] = None,
    ) -> ContactEngagementScore:
        """
        Calculate and store contact engagement score.
        
        Args:
            contact_email: Contact email address
            contact_id: Optional contact ID from CRM
            emails_sent: Number of emails sent
            emails_opened: Number of emails opened
            total_clicks: Total clicks in emails
            total_conversions: Total conversions attributed
            campaigns_engaged: Number of campaigns engaged with
            last_engagement_date: Last engagement timestamp
            
        Returns:
            ContactEngagementScore with calculated metrics
        """
        score = ContactEngagementScore(
            contact_email=contact_email,
            contact_id=contact_id,
            emails_sent=emails_sent,
            emails_opened=emails_opened,
            total_clicks=total_clicks,
            total_conversions=total_conversions,
            campaigns_engaged=campaigns_engaged,
            last_engagement_date=last_engagement_date or datetime.utcnow(),
        )
        self.contact_scores[contact_email] = score
        return score
    
    def update_contact_score(
        self,
        contact_email: str,
        emails_sent: Optional[int] = None,
        emails_opened: Optional[int] = None,
        add_clicks: float = 0.0,
        add_conversions: float = 0.0,
        add_campaigns: int = 0,
    ) -> Optional[ContactEngagementScore]:
        """
        Update existing contact engagement score.
        
        Args:
            contact_email: Contact email
            emails_sent: Set emails sent (overrides existing)
            emails_opened: Set emails opened (overrides existing)
            add_clicks: Add clicks to existing
            add_conversions: Add conversions to existing
            add_campaigns: Add campaigns engaged
            
        Returns:
            Updated ContactEngagementScore or None if not found
        """
        if contact_email not in self.contact_scores:
            return None
        
        score = self.contact_scores[contact_email]
        
        if emails_sent is not None:
            score.emails_sent = emails_sent
        if emails_opened is not None:
            score.emails_opened = emails_opened
        
        score.total_clicks += add_clicks
        score.total_conversions += add_conversions
        score.campaigns_engaged += add_campaigns
        score.last_engagement_date = datetime.utcnow()
        
        return score
    
    def finalize_report(self, report: AnalyticsReport) -> AnalyticsReport:
        """
        Finalize a report by calculating all metrics and adding contact scores.
        
        Args:
            report: Report to finalize
            
        Returns:
            Finalized report
        """
        # Add all contact scores
        for email, score in self.contact_scores.items():
            report.add_contact_score(score)
        
        # Mark campaigns as calculated
        for campaign in report.campaigns.values():
            campaign.status = AnalyticsStatus.CALCULATED
        
        return report
    
    def get_report(self, report_id: str) -> Optional[AnalyticsReport]:
        """Get report by ID."""
        return self.reports.get(report_id)
    
    def compare_campaigns(
        self,
        campaign_ids: List[str],
    ) -> Dict[str, any]:
        """
        Compare performance across multiple campaigns.
        
        Args:
            campaign_ids: List of campaign IDs to compare
            
        Returns:
            Dictionary with comparison metrics
        """
        campaigns = [
            self.campaigns[cid] for cid in campaign_ids
            if cid in self.campaigns
        ]
        
        if not campaigns:
            return {}
        
        # Calculate averages
        avg_ctr = sum(
            campaign.aggregate_metrics().ctr()
            for campaign in campaigns
        ) / len(campaigns)
        
        avg_engagement = sum(
            campaign.aggregate_metrics().engagement_rate()
            for campaign in campaigns
        ) / len(campaigns)
        
        best_campaign = max(
            campaigns,
            key=lambda c: c.aggregate_metrics().engagement_rate()
        )
        
        worst_campaign = min(
            campaigns,
            key=lambda c: c.aggregate_metrics().engagement_rate()
        )
        
        return {
            "total_campaigns": len(campaigns),
            "average_ctr": avg_ctr,
            "average_engagement_rate": avg_engagement,
            "best_campaign": {
                "id": best_campaign.campaign_id,
                "name": best_campaign.campaign_name,
                "engagement_rate": best_campaign.aggregate_metrics().engagement_rate(),
            },
            "worst_campaign": {
                "id": worst_campaign.campaign_id,
                "name": worst_campaign.campaign_name,
                "engagement_rate": worst_campaign.aggregate_metrics().engagement_rate(),
            },
        }
    
    def get_channel_comparison(
        self,
        campaign_id: str,
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare channel performance within a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dictionary with metrics per channel
        """
        if campaign_id not in self.campaigns:
            return {}
        
        campaign = self.campaigns[campaign_id]
        result = {}
        
        for channel, metrics in campaign.channel_metrics.items():
            result[channel] = {
                "impressions": metrics.total_impressions,
                "clicks": metrics.total_clicks,
                "engagements": metrics.total_engagements,
                "conversions": metrics.total_conversions,
                "ctr": metrics.ctr(),
                "engagement_rate": metrics.engagement_rate(),
                "conversion_rate": metrics.conversion_rate(),
            }
        
        return result


def get_analytics_engine() -> AnalyticsEngine:
    """Get or create global analytics engine singleton."""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine


def reset_analytics_engine() -> None:
    """Reset analytics engine (for testing)."""
    global _analytics_engine
    _analytics_engine = None


# Convenience functions
def create_report(
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> AnalyticsReport:
    """Create a new analytics report."""
    return get_analytics_engine().create_report(period_start, period_end)


def add_campaign(
    report: AnalyticsReport,
    campaign_id: str,
    campaign_name: str,
    start_date: datetime,
    end_date: Optional[datetime] = None,
    total_contacts: int = 0,
) -> CampaignAnalytics:
    """Add campaign to report."""
    return get_analytics_engine().add_campaign_to_report(
        report, campaign_id, campaign_name, start_date, end_date, total_contacts
    )


def add_metrics(
    campaign_id: str,
    channel: str,
    impressions: float = 0.0,
    clicks: float = 0.0,
    engagements: float = 0.0,
    conversions: float = 0.0,
    shares: float = 0.0,
    comments: float = 0.0,
):
    """Add publishing metrics to campaign."""
    return get_analytics_engine().add_publishing_metrics(
        campaign_id, channel, impressions, clicks, engagements, conversions, shares, comments
    )


def score_contact(
    contact_email: str,
    contact_id: Optional[str] = None,
    emails_sent: int = 0,
    emails_opened: int = 0,
    total_clicks: float = 0.0,
    total_conversions: float = 0.0,
    campaigns_engaged: int = 0,
    last_engagement_date: Optional[datetime] = None,
) -> ContactEngagementScore:
    """Score contact engagement."""
    return get_analytics_engine().score_contact_engagement(
        contact_email, contact_id, emails_sent, emails_opened,
        total_clicks, total_conversions, campaigns_engaged, last_engagement_date
    )


def finalize_report(report: AnalyticsReport) -> AnalyticsReport:
    """Finalize a report."""
    return get_analytics_engine().finalize_report(report)
