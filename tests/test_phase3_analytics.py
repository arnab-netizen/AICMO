"""
Phase 3: Analytics & Aggregation Tests

Tests for analytics models, engine, and campaign/contact scoring.
Verifies consumption of Phase 2 publishing metrics and Phase 1 CRM data.
"""

import pytest
from datetime import datetime, timedelta
from aicmo.analytics import (
    MetricType,
    AnalyticsStatus,
    MetricSnapshot,
    ChannelMetrics,
    CampaignAnalytics,
    ContactEngagementScore,
    AnalyticsReport,
    AnalyticsEngine,
    get_analytics_engine,
    reset_analytics_engine,
    create_report,
    add_campaign,
    add_metrics,
    score_contact,
    finalize_report,
)


class TestMetricModels:
    """Test metric models."""
    
    def test_metric_snapshot_creation(self):
        """Test creating a metric snapshot."""
        snapshot = MetricSnapshot(metric_type=MetricType.IMPRESSIONS, value=100)
        assert snapshot.metric_type == MetricType.IMPRESSIONS
        assert snapshot.value == 100
        assert snapshot.timestamp is not None
    
    def test_metric_snapshot_negative_value_error(self):
        """Test that negative values raise error."""
        with pytest.raises(ValueError):
            MetricSnapshot(metric_type=MetricType.CLICKS, value=-5)
    
    def test_channel_metrics_ctr(self):
        """Test click-through rate calculation."""
        metrics = ChannelMetrics(channel="LinkedIn")
        metrics.total_impressions = 1000
        metrics.total_clicks = 50
        
        assert metrics.ctr() == 0.05  # 50/1000 = 0.05
    
    def test_channel_metrics_engagement_rate(self):
        """Test engagement rate calculation."""
        metrics = ChannelMetrics(channel="Twitter")
        metrics.total_impressions = 1000
        metrics.total_engagements = 100
        
        assert metrics.engagement_rate() == 0.1  # 100/1000 = 0.1
    
    def test_channel_metrics_conversion_rate(self):
        """Test conversion rate calculation."""
        metrics = ChannelMetrics(channel="Email")
        metrics.total_clicks = 50
        metrics.total_conversions = 5
        
        assert metrics.conversion_rate() == 0.1  # 5/50 = 0.1
    
    def test_channel_metrics_add_metric(self):
        """Test adding metrics to channel."""
        metrics = ChannelMetrics(channel="Instagram")
        
        metrics.add_metric(MetricType.IMPRESSIONS, 500)
        metrics.add_metric(MetricType.CLICKS, 25)
        metrics.add_metric(MetricType.ENGAGEMENTS, 50)
        
        assert metrics.total_impressions == 500
        assert metrics.total_clicks == 25
        assert metrics.total_engagements == 50


class TestCampaignAnalytics:
    """Test campaign analytics."""
    
    def test_campaign_creation(self):
        """Test creating campaign analytics."""
        now = datetime.utcnow()
        campaign = CampaignAnalytics(
            campaign_id="camp-001",
            campaign_name="Q1 Launch",
            start_date=now,
        )
        
        assert campaign.campaign_id == "camp-001"
        assert campaign.campaign_name == "Q1 Launch"
        assert campaign.start_date == now
        assert campaign.status == AnalyticsStatus.PENDING
    
    def test_campaign_aggregate_metrics(self):
        """Test aggregating metrics across channels."""
        now = datetime.utcnow()
        campaign = CampaignAnalytics(
            campaign_id="camp-002",
            campaign_name="Multi-Channel",
            start_date=now,
        )
        
        # Add LinkedIn metrics
        campaign.add_channel_metric("LinkedIn", MetricType.IMPRESSIONS, 1000)
        campaign.add_channel_metric("LinkedIn", MetricType.CLICKS, 50)
        
        # Add Twitter metrics
        campaign.add_channel_metric("Twitter", MetricType.IMPRESSIONS, 500)
        campaign.add_channel_metric("Twitter", MetricType.CLICKS, 30)
        
        aggregated = campaign.aggregate_metrics()
        assert aggregated.total_impressions == 1500
        assert aggregated.total_clicks == 80
    
    def test_campaign_best_performing_channel(self):
        """Test finding best performing channel."""
        now = datetime.utcnow()
        campaign = CampaignAnalytics(
            campaign_id="camp-003",
            campaign_name="Channel Comparison",
            start_date=now,
        )
        
        # LinkedIn: 10% engagement
        campaign.add_channel_metric("LinkedIn", MetricType.IMPRESSIONS, 1000)
        campaign.add_channel_metric("LinkedIn", MetricType.ENGAGEMENTS, 100)
        
        # Twitter: 5% engagement
        campaign.add_channel_metric("Twitter", MetricType.IMPRESSIONS, 1000)
        campaign.add_channel_metric("Twitter", MetricType.ENGAGEMENTS, 50)
        
        best = campaign.best_performing_channel()
        assert best == "LinkedIn"
    
    def test_campaign_total_roi(self):
        """Test ROI calculation."""
        now = datetime.utcnow()
        campaign = CampaignAnalytics(
            campaign_id="camp-004",
            campaign_name="ROI Test",
            start_date=now,
            total_contacts_targeted=100,
        )
        
        campaign.add_channel_metric("Email", MetricType.CONVERSIONS, 10)
        
        # ROI = (10 conversions / (100 contacts * $0.50 cost)) * 100 = (10 / 50) * 100 = 20%
        roi = campaign.total_roi(cost_per_contact=0.50)
        assert roi == 20.0


class TestContactEngagementScore:
    """Test contact engagement scoring."""
    
    def test_contact_score_creation(self):
        """Test creating contact score."""
        score = ContactEngagementScore(
            contact_email="john@example.com",
            contact_id="contact-001",
            emails_sent=10,
            emails_opened=3,
        )
        
        assert score.contact_email == "john@example.com"
        assert score.emails_sent == 10
        assert score.emails_opened == 3
    
    def test_contact_engagement_rate(self):
        """Test email engagement rate."""
        score = ContactEngagementScore(
            contact_email="jane@example.com",
            emails_sent=20,
            emails_opened=10,
        )
        
        assert score.engagement_rate() == 0.5  # 10/20 = 50%
    
    def test_contact_click_rate(self):
        """Test click rate calculation."""
        score = ContactEngagementScore(
            contact_email="bob@example.com",
            emails_opened=10,
            total_clicks=5,
        )
        
        assert score.click_rate() == 0.5  # 5/10 = 50%
    
    def test_contact_conversion_rate(self):
        """Test conversion rate calculation."""
        score = ContactEngagementScore(
            contact_email="alice@example.com",
            total_clicks=10,
            total_conversions=3,
        )
        
        assert score.conversion_rate() == 0.3  # 3/10 = 30%
    
    def test_contact_lifetime_value_score(self):
        """Test LTV score calculation."""
        score = ContactEngagementScore(
            contact_email="vip@example.com",
            emails_sent=100,
            emails_opened=50,
            total_clicks=25,
            total_conversions=5,
        )
        
        # Engagement: 50/100 = 0.5 (40% weight)
        # Conversion: 5/25 = 0.2 (40% weight)
        # Conversions normalized: 5/5 = 1.0 (20% weight)
        # Score = (0.5 * 0.4) + (0.2 * 0.4) + (1.0 * 0.2) = 0.2 + 0.08 + 0.2 = 0.48 * 100 = 48
        ltv = score.lifetime_value_score()
        assert 47 < ltv < 49  # Allow for floating point variance
    
    def test_contact_engagement_tier(self):
        """Test engagement tier classification."""
        # High tier (LTV >= 75)
        # Engagement: 99/100 = 0.99 (40% weight)
        # Conversion: 25/50 = 0.5 (40% weight)
        # Conversions normalized: min(1.0, 25/5) = 1.0 (20% weight)
        # Score = (0.99 * 0.4) + (0.5 * 0.4) + (1.0 * 0.2) = 0.796 * 100 = 79.6 (high)
        high = ContactEngagementScore(
            contact_email="high@example.com",
            emails_sent=100,
            emails_opened=99,
            total_clicks=50,
            total_conversions=25,
        )
        assert high.engagement_tier() == "high"
        
        # Medium tier (50-75)
        # Engagement: 80/100 = 0.8 (40% weight)
        # Conversion: 20/50 = 0.4 (40% weight)
        # Conversions normalized: min(1.0, 10/5) = 1.0 (20% weight)
        # Score = (0.8 * 0.4) + (0.4 * 0.4) + (1.0 * 0.2) = 0.32 + 0.16 + 0.2 = 0.68 * 100 = 68 (medium)
        medium = ContactEngagementScore(
            contact_email="med@example.com",
            emails_sent=100,
            emails_opened=80,
            total_clicks=50,
            total_conversions=10,
        )
        assert medium.engagement_tier() == "medium"
        
        # Low tier (25-50)
        # Engagement: 40/100 = 0.4 (40% weight)
        # Conversion: 3/10 = 0.3 (40% weight)
        # Conversions normalized: min(1.0, 3/5) = 0.6 (20% weight)
        # Score = (0.4 * 0.4) + (0.3 * 0.4) + (0.6 * 0.2) = 0.16 + 0.12 + 0.12 = 0.4 * 100 = 40 (low)
        low = ContactEngagementScore(
            contact_email="low@example.com",
            emails_sent=100,
            emails_opened=40,
            total_clicks=10,
            total_conversions=3,
        )
        assert low.engagement_tier() == "low"
        
        # Inactive (< 25)
        # Engagement: 10/50 = 0.2 (40% weight)
        # Conversion: 0
        # Score = (0.2 * 0.4) + 0 + 0 = 0.08 * 100 = 8 (inactive)
        inactive = ContactEngagementScore(
            contact_email="inactive@example.com",
            emails_sent=50,
            emails_opened=10,
        )
        assert inactive.engagement_tier() == "inactive"


class TestAnalyticsReport:
    """Test analytics report."""
    
    def test_report_creation(self):
        """Test creating analytics report."""
        start = datetime.utcnow()
        end = start + timedelta(days=30)
        
        report = AnalyticsReport(period_start=start, period_end=end)
        
        assert report.period_start == start
        assert report.period_end == end
        assert report.report_id is not None
    
    def test_report_add_campaign(self):
        """Test adding campaign to report."""
        report = AnalyticsReport()
        now = datetime.utcnow()
        
        campaign = CampaignAnalytics(
            campaign_id="camp-001",
            campaign_name="Test Campaign",
            start_date=now,
            total_contacts_targeted=100,
        )
        
        report.add_campaign_analytics(campaign)
        
        assert len(report.campaigns) == 1
        assert report.total_campaigns_analyzed == 1
        assert "camp-001" in report.campaigns
    
    def test_report_add_contact_score(self):
        """Test adding contact score to report."""
        report = AnalyticsReport()
        
        score = ContactEngagementScore(
            contact_email="user@example.com",
            emails_sent=10,
            emails_opened=5,
        )
        
        report.add_contact_score(score)
        
        assert len(report.contact_scores) == 1
        assert report.total_contacts_analyzed == 1
    
    def test_report_top_contacts_by_engagement(self):
        """Test getting top contacts by engagement."""
        report = AnalyticsReport()
        
        # Create 3 contacts with different engagement levels
        score1 = ContactEngagementScore(
            contact_email="high@example.com",
            emails_sent=100,
            emails_opened=90,
            total_clicks=40,
            total_conversions=5,
        )
        report.add_contact_score(score1)
        
        score2 = ContactEngagementScore(
            contact_email="medium@example.com",
            emails_sent=100,
            emails_opened=50,
            total_clicks=20,
            total_conversions=2,
        )
        report.add_contact_score(score2)
        
        score3 = ContactEngagementScore(
            contact_email="low@example.com",
            emails_sent=100,
            emails_opened=10,
            total_clicks=2,
            total_conversions=0,
        )
        report.add_contact_score(score3)
        
        top = report.top_contacts_by_engagement(limit=2)
        
        assert len(top) == 2
        assert top[0].contact_email == "high@example.com"
        assert top[1].contact_email == "medium@example.com"
    
    def test_report_contacts_by_tier(self):
        """Test filtering contacts by tier."""
        report = AnalyticsReport()
        
        # High tier contact: LTV >= 75
        high = ContactEngagementScore(
            contact_email="high@example.com",
            emails_sent=100,
            emails_opened=99,
            total_clicks=50,
            total_conversions=25,
        )
        report.add_contact_score(high)
        
        # Low tier contact: LTV 25-50
        low = ContactEngagementScore(
            contact_email="low@example.com",
            emails_sent=100,
            emails_opened=40,
            total_clicks=10,
            total_conversions=3,
        )
        report.add_contact_score(low)
        
        high_tier = report.contacts_by_tier("high")
        low_tier = report.contacts_by_tier("low")
        
        assert len(high_tier) == 1
        assert high_tier[0].contact_email == "high@example.com"
        
        assert len(low_tier) == 1
        assert low_tier[0].contact_email == "low@example.com"
    
    def test_report_summary_stats(self):
        """Test summary statistics calculation."""
        report = AnalyticsReport()
        now = datetime.utcnow()
        
        campaign = CampaignAnalytics(
            campaign_id="camp-001",
            campaign_name="Test",
            start_date=now,
            total_contacts_targeted=100,
        )
        campaign.add_channel_metric("Email", MetricType.IMPRESSIONS, 1000)
        campaign.add_channel_metric("Email", MetricType.CLICKS, 50)
        campaign.add_channel_metric("Email", MetricType.CONVERSIONS, 5)
        
        report.add_campaign_analytics(campaign)
        
        stats = report.summary_stats()
        
        assert stats["total_campaigns"] == 1
        assert stats["total_impressions"] == 1000
        assert stats["total_clicks"] == 50
        assert stats["total_conversions"] == 5
        assert stats["overall_ctr"] == 0.05


class TestAnalyticsEngine:
    """Test analytics engine."""
    
    def setup_method(self):
        """Reset engine before each test."""
        reset_analytics_engine()
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = get_analytics_engine()
        assert engine is not None
        assert isinstance(engine, AnalyticsEngine)
    
    def test_engine_singleton(self):
        """Test engine is singleton."""
        engine1 = get_analytics_engine()
        engine2 = get_analytics_engine()
        assert engine1 is engine2
    
    def test_create_and_retrieve_report(self):
        """Test creating and retrieving report."""
        engine = get_analytics_engine()
        
        report = engine.create_report()
        retrieved = engine.get_report(report.report_id)
        
        assert retrieved is report
    
    def test_add_campaign_to_report(self):
        """Test adding campaign to report."""
        engine = get_analytics_engine()
        report = engine.create_report()
        now = datetime.utcnow()
        
        campaign = engine.add_campaign_to_report(
            report,
            campaign_id="camp-001",
            campaign_name="Test Campaign",
            start_date=now,
            total_contacts=100,
        )
        
        assert campaign.campaign_id == "camp-001"
        assert len(report.campaigns) == 1
    
    def test_add_publishing_metrics(self):
        """Test adding publishing metrics from Phase 2."""
        engine = get_analytics_engine()
        report = engine.create_report()
        now = datetime.utcnow()
        
        engine.add_campaign_to_report(
            report,
            campaign_id="camp-001",
            campaign_name="Test",
            start_date=now,
        )
        
        # Add Phase 2 publishing metrics
        engine.add_publishing_metrics(
            campaign_id="camp-001",
            channel="LinkedIn",
            impressions=1000,
            clicks=50,
            engagements=100,
            conversions=5,
        )
        
        campaign = engine.campaigns["camp-001"]
        assert campaign.channel_metrics["LinkedIn"].total_impressions == 1000
        assert campaign.channel_metrics["LinkedIn"].total_clicks == 50
    
    def test_score_contact_engagement(self):
        """Test scoring contact engagement from Phase 1 CRM."""
        engine = get_analytics_engine()
        
        score = engine.score_contact_engagement(
            contact_email="user@example.com",
            contact_id="crm-001",
            emails_sent=20,
            emails_opened=10,
            total_clicks=5,
            total_conversions=1,
            campaigns_engaged=3,
        )
        
        assert score.contact_email == "user@example.com"
        assert score.contact_id == "crm-001"
        assert score.emails_sent == 20
        assert "user@example.com" in engine.contact_scores
    
    def test_update_contact_score(self):
        """Test updating existing contact score."""
        engine = get_analytics_engine()
        
        # Create initial score
        engine.score_contact_engagement(
            contact_email="user@example.com",
            emails_sent=10,
            emails_opened=5,
        )
        
        # Update score
        updated = engine.update_contact_score(
            contact_email="user@example.com",
            emails_sent=20,
            add_clicks=3,
            add_conversions=1,
        )
        
        assert updated.emails_sent == 20
        assert updated.total_clicks == 3
        assert updated.total_conversions == 1
    
    def test_compare_campaigns(self):
        """Test comparing multiple campaigns."""
        engine = get_analytics_engine()
        now = datetime.utcnow()
        
        # Campaign 1: High engagement
        report1 = engine.create_report()
        camp1 = engine.add_campaign_to_report(
            report1, "camp-001", "High", now, total_contacts=100
        )
        engine.add_publishing_metrics("camp-001", "Email", impressions=1000, engagements=200)
        
        # Campaign 2: Low engagement
        report2 = engine.create_report()
        camp2 = engine.add_campaign_to_report(
            report2, "camp-002", "Low", now, total_contacts=100
        )
        engine.add_publishing_metrics("camp-002", "Email", impressions=1000, engagements=50)
        
        comparison = engine.compare_campaigns(["camp-001", "camp-002"])
        
        assert comparison["total_campaigns"] == 2
        assert comparison["best_campaign"]["id"] == "camp-001"
        assert comparison["worst_campaign"]["id"] == "camp-002"
    
    def test_get_channel_comparison(self):
        """Test comparing channels within campaign."""
        engine = get_analytics_engine()
        report = engine.create_report()
        now = datetime.utcnow()
        
        engine.add_campaign_to_report(
            report, "camp-001", "Multi-Channel", now
        )
        
        engine.add_publishing_metrics("camp-001", "LinkedIn", impressions=1000, clicks=50)
        engine.add_publishing_metrics("camp-001", "Twitter", impressions=500, clicks=30)
        
        channels = engine.get_channel_comparison("camp-001")
        
        assert "LinkedIn" in channels
        assert "Twitter" in channels
        assert channels["LinkedIn"]["ctr"] == 0.05
        assert channels["Twitter"]["ctr"] == 0.06
    
    def test_finalize_report(self):
        """Test finalizing report with all data."""
        engine = get_analytics_engine()
        report = engine.create_report()
        now = datetime.utcnow()
        
        # Add campaign
        engine.add_campaign_to_report(
            report, "camp-001", "Test", now, total_contacts=100
        )
        engine.add_publishing_metrics("camp-001", "Email", conversions=5)
        
        # Add contact score
        engine.score_contact_engagement(
            contact_email="user@example.com",
            emails_sent=10,
            emails_opened=5,
        )
        
        # Finalize
        finalized = engine.finalize_report(report)
        
        assert len(finalized.campaigns) == 1
        assert len(finalized.contact_scores) == 1
        assert finalized.campaigns["camp-001"].status == AnalyticsStatus.CALCULATED


class TestConvenienceFunctions:
    """Test module-level convenience functions."""
    
    def setup_method(self):
        """Reset engine before each test."""
        reset_analytics_engine()
    
    def test_create_report_function(self):
        """Test create_report() function."""
        report = create_report()
        assert report is not None
        assert report.report_id is not None
    
    def test_add_campaign_function(self):
        """Test add_campaign() function."""
        report = create_report()
        now = datetime.utcnow()
        
        campaign = add_campaign(
            report,
            campaign_id="camp-001",
            campaign_name="Test",
            start_date=now,
            total_contacts=100,
        )
        
        assert campaign.campaign_id == "camp-001"
    
    def test_add_metrics_function(self):
        """Test add_metrics() function."""
        report = create_report()
        now = datetime.utcnow()
        
        add_campaign(report, "camp-001", "Test", now)
        add_metrics(
            campaign_id="camp-001",
            channel="Email",
            impressions=1000,
            clicks=50,
        )
        
        engine = get_analytics_engine()
        campaign = engine.campaigns["camp-001"]
        assert campaign.channel_metrics["Email"].total_impressions == 1000
    
    def test_score_contact_function(self):
        """Test score_contact() function."""
        score = score_contact(
            contact_email="user@example.com",
            emails_sent=10,
            emails_opened=5,
        )
        
        assert score.contact_email == "user@example.com"
        assert score.emails_sent == 10
    
    def test_finalize_report_function(self):
        """Test finalize_report() function."""
        report = create_report()
        now = datetime.utcnow()
        
        add_campaign(report, "camp-001", "Test", now)
        score_contact("user@example.com", emails_sent=10)
        
        finalized = finalize_report(report)
        
        assert len(finalized.campaigns) == 1
        assert len(finalized.contact_scores) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
