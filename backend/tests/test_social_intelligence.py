"""Tests for Social Intelligence Engine.

Stage S: Social intelligence tests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import tempfile
import os

from aicmo.domain.intake import ClientIntake
from aicmo.social.domain import (
    SocialPlatform,
    SentimentType,
    TrendStrength,
    SocialMention,
    SocialTrend,
    Influencer,
    SocialListeningReport,
    TrendAnalysis,
    InfluencerCampaign,
)
from aicmo.social.service import (
    generate_listening_report,
    analyze_trends,
    discover_influencers,
    create_influencer_campaign,
)
from aicmo.learning.event_types import EventType


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_intake():
    """Sample client intake for testing."""
    return ClientIntake(
        brand_name="SocialTestCo",
        industry="Technology",
        product_service="SaaS Platform",
        primary_goal="Increase brand awareness",
        target_audiences=["Tech professionals", "Startups"]
    )


@pytest.fixture
def sample_influencer():
    """Sample influencer for testing."""
    return Influencer(
        influencer_id="inf-1",
        name="Tech Influencer",
        handle="@tech_influencer",
        platform=SocialPlatform.INSTAGRAM,
        followers=100000,
        avg_engagement_rate=4.5,
        content_categories=["tech", "lifestyle"],
        relevance_score=90.0,
        niche="Technology",
        last_analyzed=datetime.now()
    )


# ═══════════════════════════════════════════════════════════════════════
# Domain Model Tests
# ═══════════════════════════════════════════════════════════════════════


class TestSocialMentionDomain:
    """Test SocialMention domain model."""
    
    def test_mention_creation(self):
        """Test creating a social mention."""
        mention = SocialMention(
            mention_id="m-123",
            platform=SocialPlatform.TWITTER,
            brand_name="TestBrand",
            author="User123",
            author_handle="@user123",
            content="Great product from @TestBrand!",
            likes=50,
            shares=10,
            sentiment=SentimentType.POSITIVE,
            sentiment_score=0.8,
            posted_at=datetime.now(),
            captured_at=datetime.now()
        )
        
        assert mention.platform == SocialPlatform.TWITTER
        assert mention.sentiment == SentimentType.POSITIVE
        assert mention.likes == 50


class TestInfluencerDomain:
    """Test Influencer domain model."""
    
    def test_influencer_creation(self, sample_influencer):
        """Test creating an influencer profile."""
        assert sample_influencer.followers == 100000
        assert sample_influencer.relevance_score == 90.0
        assert sample_influencer.platform == SocialPlatform.INSTAGRAM


# ═══════════════════════════════════════════════════════════════════════
# Service Function Tests
# ═══════════════════════════════════════════════════════════════════════


class TestSocialListeningReport:
    """Test social listening report generation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_generate_report_returns_report(self, temp_db, sample_intake):
        """Test that generate_listening_report returns a report."""
        report = generate_listening_report(sample_intake, days_back=30)
        
        assert isinstance(report, SocialListeningReport)
        assert report.brand_name == sample_intake.brand_name
        assert report.total_mentions > 0
    
    def test_report_has_sentiment_breakdown(self, temp_db, sample_intake):
        """Test that report includes sentiment analysis."""
        report = generate_listening_report(sample_intake)
        
        total = report.positive_mentions + report.negative_mentions + report.neutral_mentions
        assert total == report.total_mentions
        assert -1.0 <= report.avg_sentiment_score <= 1.0
    
    def test_report_logs_event(self, temp_db, sample_intake):
        """Test that report generation logs learning event."""
        with patch('aicmo.social.service.log_event') as mock_log:
            generate_listening_report(sample_intake)
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.SOCIAL_INTEL_SENTIMENT_ANALYZED.value


class TestTrendAnalysis:
    """Test trend analysis."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_analyze_trends_returns_analysis(self, temp_db, sample_intake):
        """Test that analyze_trends returns analysis."""
        analysis = analyze_trends(sample_intake, days_back=7)
        
        assert isinstance(analysis, TrendAnalysis)
        assert analysis.brand_name == sample_intake.brand_name
        assert analysis.industry == sample_intake.industry
    
    def test_analysis_has_trends_and_opportunities(self, temp_db, sample_intake):
        """Test that analysis includes trends and opportunities."""
        analysis = analyze_trends(sample_intake)
        
        assert len(analysis.relevant_hashtags) > 0
        assert len(analysis.content_opportunities) > 0
        assert len(analysis.trending_keywords) > 0
    
    def test_trend_analysis_logs_event(self, temp_db, sample_intake):
        """Test that trend analysis logs learning event."""
        with patch('aicmo.social.service.log_event') as mock_log:
            analyze_trends(sample_intake)
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.SOCIAL_INTEL_TREND_DETECTED.value


class TestInfluencerDiscovery:
    """Test influencer discovery."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_discover_influencers_returns_list(self, temp_db, sample_intake):
        """Test that discover_influencers returns influencer list."""
        influencers = discover_influencers(sample_intake, niche="Technology")
        
        assert isinstance(influencers, list)
        assert len(influencers) > 0
        assert all(isinstance(inf, Influencer) for inf in influencers)
    
    def test_influencers_have_metrics(self, temp_db, sample_intake):
        """Test that influencers have proper metrics."""
        influencers = discover_influencers(sample_intake)
        
        for inf in influencers:
            assert inf.followers > 0
            assert 0 <= inf.relevance_score <= 100
            assert inf.niche
    
    def test_influencer_discovery_logs_event(self, temp_db, sample_intake):
        """Test that influencer discovery logs learning event."""
        with patch('aicmo.social.service.log_event') as mock_log:
            discover_influencers(sample_intake)
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.SOCIAL_INTEL_INFLUENCER_FOUND.value


class TestInfluencerCampaign:
    """Test influencer campaign creation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_create_campaign_returns_campaign(self, temp_db, sample_intake, sample_influencer):
        """Test that create_influencer_campaign returns campaign."""
        campaign = create_influencer_campaign(
            sample_intake,
            campaign_name="Product Launch",
            influencers=[sample_influencer],
            budget=10000.0
        )
        
        assert isinstance(campaign, InfluencerCampaign)
        assert campaign.brand_name == sample_intake.brand_name
        assert len(campaign.recommended_influencers) == 1
    
    def test_campaign_allocates_budget(self, temp_db, sample_intake, sample_influencer):
        """Test that campaign allocates budget to influencers."""
        budget = 15000.0
        campaign = create_influencer_campaign(
            sample_intake,
            campaign_name="Test Campaign",
            influencers=[sample_influencer],
            budget=budget
        )
        
        assert len(campaign.budget_per_influencer) > 0
        total_allocated = sum(campaign.budget_per_influencer.values())
        assert abs(total_allocated - budget) < 1.0  # Allow small rounding error
    
    def test_campaign_creation_logs_event(self, temp_db, sample_intake, sample_influencer):
        """Test that campaign creation logs learning event."""
        with patch('aicmo.social.service.log_event') as mock_log:
            create_influencer_campaign(
                sample_intake,
                campaign_name="Test",
                influencers=[sample_influencer],
                budget=5000.0
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.SOCIAL_INTEL_CONVERSATION_TRACKED.value


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════


class TestSocialIntelligenceIntegration:
    """Test social intelligence integration."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_social_intelligence_workflow(self, temp_db):
        """Test complete social intelligence workflow."""
        # Create intake
        intake = ClientIntake(
            brand_name="WorkflowTest",
            industry="Fashion",
            product_service="Clothing line",
            primary_goal="Build social presence",
            target_audiences=["Young adults", "Fashion enthusiasts"]
        )
        
        # Generate listening report
        report = generate_listening_report(intake, days_back=30)
        assert report.total_mentions > 0
        assert report.brand_name == intake.brand_name
        
        # Analyze trends
        trends = analyze_trends(intake, days_back=7)
        assert len(trends.content_opportunities) > 0
        
        # Discover influencers
        influencers = discover_influencers(intake, niche="Fashion")
        assert len(influencers) > 0
        
        # Create campaign
        campaign = create_influencer_campaign(
            intake,
            campaign_name="Fall Collection Launch",
            influencers=influencers[:2],
            budget=20000.0
        )
        assert campaign.status == "draft"
        assert len(campaign.recommended_influencers) == 2
        
        # Note: Learning events are tested separately in other test methods
