"""
Tests for Phase 5: Lead Routing Engine.

Comprehensive test coverage for:
- RoutingRules configuration
- ContentSequence definitions
- LeadRouter single and batch routing
- RoutingMetrics tracking
"""

import pytest
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, LeadSource, LeadStatus
from aicmo.cam.db_models import LeadDB, CampaignDB
from aicmo.cam.engine.lead_router import (
    RoutingRules,
    ContentSequence,
    ContentSequenceType,
    LeadRouter,
    RoutingStatus,
    RoutingDecision,
    RoutingMetrics,
)


# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def routing_rules() -> RoutingRules:
    """Standard routing rules."""
    return RoutingRules()


@pytest.fixture
def lead_router(routing_rules) -> LeadRouter:
    """Lead router instance."""
    return LeadRouter(routing_rules)


@pytest.fixture
def lead_hot() -> Lead:
    """HOT tier lead (aggressive close)."""
    return Lead(
        id=1,
        campaign_id=1,
        name="John Smith",
        email="john@company.com",
        company="TechCorp Inc",
        source=LeadSource.CSV,
        status=LeadStatus.QUALIFIED,
        lead_score=0.90,
        enrichment_data={
            "recent_job_change": True,
            "company_hiring": True,
            "is_decision_maker": True
        }
    )


@pytest.fixture
def lead_warm() -> Lead:
    """WARM tier lead (regular nurture)."""
    return Lead(
        id=2,
        campaign_id=1,
        name="Jane Doe",
        email="jane@company.com",
        company="StartupX",
        source=LeadSource.CSV,
        status=LeadStatus.QUALIFIED,
        lead_score=0.75,
        enrichment_data={"company_hiring": True}
    )


@pytest.fixture
def lead_cool() -> Lead:
    """COOL tier lead (long-term nurture)."""
    return Lead(
        id=3,
        campaign_id=1,
        name="Bob Johnson",
        email="bob@company.com",
        company="MediumCorp",
        source=LeadSource.CSV,
        status=LeadStatus.QUALIFIED,
        lead_score=0.60,
        enrichment_data={}
    )


@pytest.fixture
def lead_cold() -> Lead:
    """COLD tier lead (education)."""
    return Lead(
        id=4,
        campaign_id=1,
        name="Sarah Wilson",
        email="sarah@company.com",
        company="LargeOrg",
        source=LeadSource.CSV,
        status=LeadStatus.QUALIFIED,
        lead_score=0.40,
        enrichment_data={}
    )


@pytest.fixture
def db(db) -> Session:
    """Database session."""
    return db


# ==========================================
# TESTS: RoutingRules
# ==========================================


class TestRoutingRules:
    """Tests for RoutingRules class."""

    def test_rules_initialization_defaults(self):
        """Test rules with default values."""
        rules = RoutingRules()
        assert rules.enable_auto_routing is True
        assert rules.hot_tier_min_score == 0.85
        assert rules.warm_tier_min_score == 0.70
        assert rules.cool_tier_min_score == 0.50
        assert rules.intent_boost_enabled is True

    def test_rules_custom_initialization(self):
        """Test rules with custom values."""
        rules = RoutingRules(
            enable_auto_routing=False,
            hot_tier_min_score=0.80,
            intent_boost_enabled=False
        )
        assert rules.enable_auto_routing is False
        assert rules.hot_tier_min_score == 0.80
        assert rules.intent_boost_enabled is False

    def test_rules_to_dict(self, routing_rules):
        """Test rules conversion to dict."""
        result = routing_rules.to_dict()
        assert result["hot_tier_min_score"] == 0.85
        assert result["intent_boost_enabled"] is True


# ==========================================
# TESTS: ContentSequence
# ==========================================


class TestContentSequence:
    """Tests for ContentSequence class."""

    def test_hot_sequence(self):
        """Test HOT sequence definition."""
        seq = ContentSequence.hot_sequence()
        assert seq.sequence_type == ContentSequenceType.AGGRESSIVE_CLOSE
        assert seq.duration_days == 7
        assert seq.email_count == 3

    def test_warm_sequence(self):
        """Test WARM sequence definition."""
        seq = ContentSequence.warm_sequence()
        assert seq.sequence_type == ContentSequenceType.REGULAR_NURTURE
        assert seq.duration_days == 14
        assert seq.email_count == 4

    def test_cool_sequence(self):
        """Test COOL sequence definition."""
        seq = ContentSequence.cool_sequence()
        assert seq.sequence_type == ContentSequenceType.LONG_TERM_NURTURE
        assert seq.duration_days == 30
        assert seq.email_count == 6

    def test_cold_sequence(self):
        """Test COLD sequence definition."""
        seq = ContentSequence.cold_sequence()
        assert seq.sequence_type == ContentSequenceType.COLD_OUTREACH
        assert seq.duration_days == 60
        assert seq.email_count == 8

    def test_custom_sequence(self):
        """Test custom sequence creation."""
        seq = ContentSequence(
            name="Custom",
            sequence_type=ContentSequenceType.REGULAR_NURTURE,
            duration_days=21,
            email_count=5,
            goal="Test goal"
        )
        assert seq.name == "Custom"
        assert seq.duration_days == 21


# ==========================================
# TESTS: LeadRouter - Single Lead Routing
# ==========================================


class TestLeadRouter:
    """Tests for LeadRouter class."""

    def test_route_hot_lead(self, lead_router, lead_hot):
        """Test routing of HOT lead."""
        decision = lead_router.route_single_lead(lead_hot)
        assert decision.status == RoutingStatus.ROUTED
        assert decision.sequence_type == ContentSequenceType.AGGRESSIVE_CLOSE
        assert decision.lead_id == lead_hot.id

    def test_route_warm_lead(self, lead_router, lead_warm):
        """Test routing of WARM lead."""
        decision = lead_router.route_single_lead(lead_warm)
        assert decision.status == RoutingStatus.ROUTED
        assert decision.sequence_type == ContentSequenceType.REGULAR_NURTURE

    def test_route_cool_lead(self, lead_router, lead_cool):
        """Test routing of COOL lead."""
        decision = lead_router.route_single_lead(lead_cool)
        assert decision.status == RoutingStatus.ROUTED
        assert decision.sequence_type == ContentSequenceType.LONG_TERM_NURTURE

    def test_route_cold_lead(self, lead_router, lead_cold):
        """Test routing of COLD lead."""
        decision = lead_router.route_single_lead(lead_cold)
        assert decision.status == RoutingStatus.ROUTED
        assert decision.sequence_type == ContentSequenceType.COLD_OUTREACH

    def test_route_rejected_lead(self, lead_router):
        """Test rejection of already-rejected lead."""
        lead = Lead(
            id=5,
            campaign_id=1,
            name="Rejected",
            email="rejected@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.LOST,
            lead_score=0.90
        )
        decision = lead_router.route_single_lead(lead)
        assert decision.status == RoutingStatus.REJECTED_LEAD
        assert decision.sequence_type is None

    def test_route_not_qualified_lead(self, lead_router):
        """Test rejection of non-qualified lead."""
        lead = Lead(
            id=6,
            campaign_id=1,
            name="Pending",
            email="pending@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ENRICHED,
            lead_score=0.90
        )
        decision = lead_router.route_single_lead(lead)
        assert decision.status == RoutingStatus.QUALIFICATION_PENDING

    def test_route_already_routed_lead(self, lead_router):
        """Test rejection of already-routed lead."""
        lead = Lead(
            id=7,
            campaign_id=1,
            name="Routed",
            email="routed@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ROUTED,
            lead_score=0.90
        )
        decision = lead_router.route_single_lead(lead)
        assert decision.status == RoutingStatus.ALREADY_ROUTED

    def test_intent_boost_elevates_tier(self, routing_rules):
        """Test that high intent boosts tier."""
        routing_rules.intent_boost_enabled = True
        router = LeadRouter(routing_rules)
        
        # Lead with medium score but high intent
        lead = Lead(
            id=8,
            campaign_id=1,
            name="Intent Boost",
            email="intent@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED,
            lead_score=0.72,  # Just above WARM threshold
            enrichment_data={
                "recent_job_change": True,
                "company_funded_recently": True,
                "company_hiring": True,
                "recent_activity": True  # 4+ signals = high intent
            }
        )
        
        decision = router.route_single_lead(lead)
        # Intent boost should elevate from WARM to HOT
        assert decision.sequence_type == ContentSequenceType.AGGRESSIVE_CLOSE
        assert decision.boosted_by_intent is True

    def test_intent_boost_disabled(self, routing_rules):
        """Test that intent boost can be disabled."""
        routing_rules.intent_boost_enabled = False
        router = LeadRouter(routing_rules)
        
        lead = Lead(
            id=9,
            campaign_id=1,
            name="No Boost",
            email="noboost@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED,
            lead_score=0.72,  # WARM score
            enrichment_data={
                "recent_job_change": True,
                "company_funded_recently": True,
            }
        )
        
        decision = router.route_single_lead(lead)
        assert decision.sequence_type == ContentSequenceType.REGULAR_NURTURE
        assert decision.boosted_by_intent is False

    def test_routing_decision_has_reasoning(self, lead_router, lead_hot):
        """Test that routing decision includes reasoning."""
        decision = lead_router.route_single_lead(lead_hot)
        assert decision.reasoning is not None
        assert len(decision.reasoning) > 0

    def test_routing_decision_has_scheduled_time(self, lead_router, lead_hot):
        """Test that routing decision includes schedule."""
        decision = lead_router.route_single_lead(lead_hot)
        assert decision.scheduled_for is not None


# ==========================================
# TESTS: RoutingMetrics
# ==========================================


class TestRoutingMetrics:
    """Tests for RoutingMetrics class."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = RoutingMetrics()
        assert metrics.processed_count == 0
        assert metrics.routed_count == 0
        assert metrics.hot_count == 0

    def test_metrics_to_dict(self):
        """Test metrics conversion to dict."""
        metrics = RoutingMetrics(
            processed_count=100,
            routed_count=80,
            hot_count=25,
            warm_count=35,
            cool_count=15,
            cold_count=5,
            duration_seconds=5.5
        )
        result = metrics.to_dict()
        assert result["processed_count"] == 100
        assert result["routed_count"] == 80
        assert result["hot_count"] == 25
        assert "hot_ratio" in result
        assert result["hot_ratio"] > 0

    def test_metrics_ratio_calculations(self):
        """Test ratio calculations."""
        metrics = RoutingMetrics(
            routed_count=100,
            hot_count=50,
            warm_count=30,
            cool_count=15,
            cold_count=5
        )
        result = metrics.to_dict()
        assert result["hot_ratio"] == 0.5
        assert result["warm_ratio"] == 0.3
        assert result["cool_ratio"] == 0.15
        assert result["cold_ratio"] == 0.05


# ==========================================
# TESTS: Batch Routing
# ==========================================


class TestBatchRouting:
    """Tests for batch routing operations."""

    def test_batch_route_empty_campaign(self, db, lead_router):
        """Test batch routing on empty campaign."""
        metrics = lead_router.batch_route_leads(db, campaign_id=999)
        assert metrics.processed_count == 0

    def test_batch_route_multiple_leads(self, db, lead_router):
        """Test batch routing of multiple leads."""
        # Create campaign
        campaign = CampaignDB(name="Test Routing Campaign")
        db.add(campaign)
        db.commit()
        
        # Create qualified leads
        lead1 = LeadDB(
            campaign_id=campaign.id,
            name="Hot Lead",
            email="hot@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED.value,
            lead_score=0.90,
            enrichment_data={"recent_job_change": True}
        )
        
        lead2 = LeadDB(
            campaign_id=campaign.id,
            name="Warm Lead",
            email="warm@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED.value,
            lead_score=0.75,
            enrichment_data={}
        )
        
        db.add_all([lead1, lead2])
        db.commit()
        
        # Route
        metrics = lead_router.batch_route_leads(db, campaign_id=campaign.id)
        
        assert metrics.processed_count == 2
        assert metrics.routed_count == 2
        assert metrics.hot_count >= 1
        assert metrics.warm_count >= 1

    def test_batch_route_updates_database(self, db, lead_router):
        """Test that batch routing updates database."""
        # Create campaign and lead
        campaign = CampaignDB(name="Update Test Campaign")
        db.add(campaign)
        db.commit()
        
        lead = LeadDB(
            campaign_id=campaign.id,
            name="Hot Lead",
            email="hot@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED.value,
            lead_score=0.90,
            enrichment_data={"recent_job_change": True}
        )
        db.add(lead)
        db.commit()
        
        # Route
        lead_router.batch_route_leads(db, campaign_id=campaign.id)
        
        # Refresh and check
        db.refresh(lead)
        assert lead.status == LeadStatus.ROUTED.value
        assert lead.routing_sequence is not None
        assert lead.sequence_start_at is not None

    def test_batch_route_skips_already_routed(self, db, lead_router):
        """Test that batch routing skips already routed leads."""
        # Create campaign
        campaign = CampaignDB(name="Skip Test Campaign")
        db.add(campaign)
        db.commit()
        
        # Already routed lead
        lead1 = LeadDB(
            campaign_id=campaign.id,
            name="Already Routed",
            email="routed@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ROUTED.value,
            lead_score=0.90
        )
        
        # New lead to route
        lead2 = LeadDB(
            campaign_id=campaign.id,
            name="To Route",
            email="toroute@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED.value,
            lead_score=0.90
        )
        
        db.add_all([lead1, lead2])
        db.commit()
        
        # Route
        metrics = lead_router.batch_route_leads(db, campaign_id=campaign.id)
        
        # Only one lead should be processed
        assert metrics.processed_count == 1

    def test_batch_route_respects_max_leads(self, db, lead_router):
        """Test that batch routing respects max_leads limit."""
        # Create campaign with many leads
        campaign = CampaignDB(name="Max Leads Campaign")
        db.add(campaign)
        db.commit()
        
        leads = [
            LeadDB(
                campaign_id=campaign.id,
                name=f"Lead {i}",
                email=f"lead{i}@company.com",
                source=LeadSource.CSV,
                status=LeadStatus.QUALIFIED.value,
                lead_score=0.80
            )
            for i in range(10)
        ]
        db.add_all(leads)
        db.commit()
        
        # Route with max_leads=3
        metrics = lead_router.batch_route_leads(db, campaign_id=campaign.id, max_leads=3)
        
        assert metrics.processed_count == 3

    def test_batch_route_disabled(self, routing_rules, db):
        """Test that routing can be disabled."""
        routing_rules.enable_auto_routing = False
        router = LeadRouter(routing_rules)
        
        # Create campaign and lead
        campaign = CampaignDB(name="Disabled Campaign")
        db.add(campaign)
        db.commit()
        
        lead = LeadDB(
            campaign_id=campaign.id,
            name="Lead",
            email="lead@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED.value,
            lead_score=0.90
        )
        db.add(lead)
        db.commit()
        
        # Route (should do nothing)
        metrics = router.batch_route_leads(db, campaign_id=campaign.id)
        
        assert metrics.routed_count == 0

    def test_batch_route_handles_manual_review(self, db, lead_router):
        """Test that batch routing handles MANUAL_REVIEW status."""
        # Create campaign
        campaign = CampaignDB(name="Manual Review Campaign")
        db.add(campaign)
        db.commit()
        
        # Manual review lead
        lead = LeadDB(
            campaign_id=campaign.id,
            name="Manual Review",
            email="manual@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.MANUAL_REVIEW.value,
            lead_score=0.90
        )
        db.add(lead)
        db.commit()
        
        # Route
        metrics = lead_router.batch_route_leads(db, campaign_id=campaign.id)
        
        # Should route even though in manual review
        assert metrics.processed_count >= 1

    def test_batch_route_tracks_metrics(self, db, lead_router):
        """Test that batch routing tracks accurate metrics."""
        # Create campaign with mixed leads
        campaign = CampaignDB(name="Metrics Campaign")
        db.add(campaign)
        db.commit()
        
        # Different tier leads
        hot = LeadDB(
            campaign_id=campaign.id,
            name="Hot",
            email="hot@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED.value,
            lead_score=0.95
        )
        
        warm = LeadDB(
            campaign_id=campaign.id,
            name="Warm",
            email="warm@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED.value,
            lead_score=0.75
        )
        
        db.add_all([hot, warm])
        db.commit()
        
        # Route
        metrics = lead_router.batch_route_leads(db, campaign_id=campaign.id)
        
        assert metrics.processed_count == 2
        assert metrics.routed_count == 2
        assert metrics.hot_count >= 1
        assert metrics.warm_count >= 1
        assert metrics.duration_seconds >= 0
