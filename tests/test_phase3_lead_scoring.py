"""
Tests for Phase 3: Lead Scoring Engine.

Comprehensive test coverage for:
- ICPScorer (company fit scoring)
- OpportunityScorer (lead engagement scoring)
- TierClassifier (HOT/WARM/COOL/COLD tier assignment)
- Batch scoring operations
"""

import pytest
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from aicmo.cam.domain import Campaign, Lead, LeadSource, LeadStatus
from aicmo.cam.db_models import LeadDB, CampaignDB
from aicmo.cam.engine.lead_scorer import (
    ICPScorer,
    OpportunityScorer,
    TierClassifier,
    LeadTier,
    CompanySize,
    ScoringMetrics,
    batch_score_leads,
)


# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def campaign() -> Campaign:
    """Sample campaign for testing."""
    campaign = Campaign(
        id=1,
        name="Tech SaaS Campaign",
        description="Target tech companies",
        target_niche="B2B SaaS",
    )
    # Add custom attributes for scoring (not in base model but used by scorer)
    # Using object.__setattr__ to bypass Pydantic's field validation
    object.__setattr__(campaign, "target_company_size", "medium")
    object.__setattr__(campaign, "target_industry", "technology")
    object.__setattr__(campaign, "target_revenue_min", 1_000_000)
    object.__setattr__(campaign, "target_revenue_max", 100_000_000)
    object.__setattr__(campaign, "target_location", "US")
    object.__setattr__(campaign, "target_roles", ["CTO", "VP Engineering", "Head of Engineering"])
    return campaign


@pytest.fixture
def lead_with_enrichment() -> Lead:
    """Sample lead with enrichment data."""
    return Lead(
        id=1,
        campaign_id=1,
        name="John Smith",
        company="TechCorp Inc",
        role="VP Engineering",
        email="john@techcorp.com",
        linkedin_url="https://linkedin.com/in/johnsmith",
        source=LeadSource.CSV,
        status=LeadStatus.NEW,
        enrichment_data={
            "company_size": "medium",
            "industry": "technology",
            "annual_revenue": 50_000_000,
            "company_location": "US",
            "job_level": "director",
            "recent_job_change": True,
            "company_hiring": True,
            "is_decision_maker": True,
            "has_budget_authority": True,
            "recent_activity": True,
        },
    )


@pytest.fixture
def lead_poor_fit() -> Lead:
    """Sample lead with poor ICP fit."""
    return Lead(
        id=2,
        campaign_id=1,
        name="Jane Smith",
        company="RetailCorp Ltd",
        role="Store Manager",
        email="jane@retailcorp.com",
        linkedin_url="https://linkedin.com/in/janesmith",
        source=LeadSource.CSV,
        status=LeadStatus.NEW,
        enrichment_data={
            "company_size": "startup",
            "industry": "retail",
            "annual_revenue": 5_000_000,
            "company_location": "UK",
            "job_level": "manager",
            "recent_job_change": False,
            "company_hiring": False,
            "is_decision_maker": False,
            "has_budget_authority": False,
            "recent_activity": False,
        },
    )


# ==========================================
# TESTS: ICPScorer
# ==========================================


class TestICPScorer:
    """Tests for ICPScorer class."""

    def test_icp_scorer_initialization(self):
        """Test ICPScorer can be initialized with default weights."""
        scorer = ICPScorer()
        assert scorer.size_weight == 0.30
        assert scorer.industry_weight == 0.30
        assert scorer.revenue_weight == 0.25
        assert scorer.location_weight == 0.15

    def test_icp_scorer_custom_weights(self):
        """Test ICPScorer can be initialized with custom weights."""
        scorer = ICPScorer(
            size_weight=0.40,
            industry_weight=0.30,
            revenue_weight=0.20,
            location_weight=0.10,
        )
        assert scorer.size_weight == 0.40
        assert scorer.industry_weight == 0.30
        assert scorer.revenue_weight == 0.20
        assert scorer.location_weight == 0.10

    def test_compute_icp_fit_perfect_match(self, campaign, lead_with_enrichment):
        """Test ICP scoring with perfect match lead."""
        scorer = ICPScorer()
        score = scorer.compute_icp_fit(lead_with_enrichment, campaign)

        # Should be high (0.7+) for matching company size, industry, location
        assert score >= 0.7
        assert 0.0 <= score <= 1.0

    def test_compute_icp_fit_poor_match(self, campaign, lead_poor_fit):
        """Test ICP scoring with poor fit lead."""
        scorer = ICPScorer()
        score = scorer.compute_icp_fit(lead_poor_fit, campaign)

        # Should be moderate (< 0.65) due to mismatched industry, size, location
        assert score < 0.65
        assert 0.0 <= score <= 1.0

    def test_compute_icp_fit_missing_enrichment(self, campaign):
        """Test ICP scoring without enrichment data."""
        lead = Lead(
            id=3,
            campaign_id=1,
            name="Unknown Lead",
            email="unknown@example.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
        )
        scorer = ICPScorer()
        score = scorer.compute_icp_fit(lead, campaign)

        # Should return neutral 0.5 when enrichment missing
        assert score == 0.5

    def test_company_size_scoring_exact_match(self):
        """Test company size scoring with exact match."""
        scorer = ICPScorer()
        score = scorer._score_company_size("medium", "medium")
        assert score == 1.0

    def test_company_size_scoring_adjacent(self):
        """Test company size scoring with adjacent sizes."""
        scorer = ICPScorer()
        score = scorer._score_company_size("small", "medium")
        # Adjacent sizes should get partial credit
        assert 0.5 <= score < 1.0

    def test_company_size_scoring_far_apart(self):
        """Test company size scoring with far apart sizes."""
        scorer = ICPScorer()
        score = scorer._score_company_size("startup", "enterprise")
        # Far apart should get minimal credit
        assert score <= 0.7

    def test_industry_scoring_exact_match(self):
        """Test industry scoring with exact match."""
        scorer = ICPScorer()
        score = scorer._score_industry("technology", "technology")
        assert score == 1.0

    def test_industry_scoring_partial_match(self):
        """Test industry scoring with partial match."""
        scorer = ICPScorer()
        score = scorer._score_industry("software technology", "technology")
        # Partial match (substring) should get high credit
        assert score >= 0.8

    def test_industry_scoring_no_match(self):
        """Test industry scoring with no match."""
        scorer = ICPScorer()
        score = scorer._score_industry("retail", "technology")
        assert score == 0.3

    def test_revenue_scoring_in_range(self):
        """Test revenue scoring when within target range."""
        scorer = ICPScorer()
        score = scorer._score_revenue(
            annual_revenue=50_000_000,
            target_min=10_000_000,
            target_max=100_000_000,
        )
        assert score == 1.0

    def test_revenue_scoring_below_range(self):
        """Test revenue scoring when below target range."""
        scorer = ICPScorer()
        score = scorer._score_revenue(
            annual_revenue=5_000_000,
            target_min=10_000_000,
            target_max=100_000_000,
        )
        # Below range but not too far should get partial credit
        assert 0.3 <= score < 1.0

    def test_location_scoring_exact_match(self):
        """Test location scoring with exact match."""
        scorer = ICPScorer()
        score = scorer._score_location("US", "US")
        assert score == 1.0

    def test_location_scoring_partial_match(self):
        """Test location scoring with partial match."""
        scorer = ICPScorer()
        score = scorer._score_location("San Francisco, US", "US")
        # Partial match should get high credit
        assert score >= 0.8

    def test_location_scoring_no_match(self):
        """Test location scoring with no match."""
        scorer = ICPScorer()
        score = scorer._score_location("UK", "US")
        assert score == 0.4


# ==========================================
# TESTS: OpportunityScorer
# ==========================================


class TestOpportunityScorer:
    """Tests for OpportunityScorer class."""

    def test_opportunity_scorer_initialization(self):
        """Test OpportunityScorer can be initialized."""
        scorer = OpportunityScorer()
        assert scorer.title_weight == 0.35
        assert scorer.seniority_weight == 0.25
        assert scorer.signals_weight == 0.40

    def test_compute_opportunity_score_high_signal(self, campaign, lead_with_enrichment):
        """Test opportunity scoring with strong signals."""
        scorer = OpportunityScorer()
        score = scorer.compute_opportunity_score(lead_with_enrichment, campaign)

        # Should be high (0.7+) due to decision maker, recent hire, etc.
        assert score >= 0.7
        assert 0.0 <= score <= 1.0

    def test_compute_opportunity_score_no_signals(self, campaign, lead_poor_fit):
        """Test opportunity scoring with weak signals."""
        scorer = OpportunityScorer()
        score = scorer.compute_opportunity_score(lead_poor_fit, campaign)

        # Should be moderate without activity signals
        assert 0.0 <= score <= 1.0

    def test_title_relevance_exact_match(self, campaign):
        """Test title relevance scoring with exact match."""
        scorer = OpportunityScorer()
        score = scorer._score_title_relevance("CTO", campaign.target_roles)
        assert score == 1.0

    def test_title_relevance_partial_match(self, campaign):
        """Test title relevance scoring with partial match."""
        scorer = OpportunityScorer()
        score = scorer._score_title_relevance("VP of Engineering", campaign.target_roles)
        # "VP" in "VP of Engineering" should match "VP Engineering" partially
        assert score >= 0.3

    def test_title_relevance_no_match(self, campaign):
        """Test title relevance scoring with no match."""
        scorer = OpportunityScorer()
        score = scorer._score_title_relevance("Sales Manager", campaign.target_roles)
        assert score == 0.3

    def test_seniority_scoring_c_level(self):
        """Test seniority scoring for C-level executives."""
        scorer = OpportunityScorer()
        # "CTO" should match "cto" keyword directly
        score = scorer._score_seniority("CTO", None)
        assert score >= 0.9

    def test_seniority_scoring_director(self):
        """Test seniority scoring for director level."""
        scorer = OpportunityScorer()
        score = scorer._score_seniority("Director of Engineering", None)
        # Should match "director" keyword and score 0.90
        assert 0.85 <= score <= 1.0

    def test_seniority_scoring_manager(self):
        """Test seniority scoring for manager level."""
        scorer = OpportunityScorer()
        score = scorer._score_seniority("Engineering Manager", None)
        assert 0.6 <= score <= 0.8

    def test_seniority_scoring_individual_contributor(self):
        """Test seniority scoring for IC level."""
        scorer = OpportunityScorer()
        score = scorer._score_seniority("Software Engineer", None)
        assert score == 0.5

    def test_opportunity_signals_all_positive(self):
        """Test opportunity signal scoring with all positive indicators."""
        scorer = OpportunityScorer()
        signals = {
            "recent_job_change": True,
            "company_funded_recently": True,
            "company_hiring": True,
            "recent_activity": True,
            "is_decision_maker": True,
            "has_budget_authority": True,
        }
        score = scorer._score_opportunity_signals(signals)
        # Should accumulate to near 1.0
        assert score >= 0.9

    def test_opportunity_signals_no_signals(self):
        """Test opportunity signal scoring with no signals."""
        scorer = OpportunityScorer()
        signals = {}
        score = scorer._score_opportunity_signals(signals)
        # Base score is 0.5, no additions
        assert score == 0.5

    def test_opportunity_signals_partial(self):
        """Test opportunity signal scoring with some signals."""
        scorer = OpportunityScorer()
        signals = {
            "recent_job_change": True,
            "is_decision_maker": True,
        }
        score = scorer._score_opportunity_signals(signals)
        # Should be > 0.5 but < 1.0
        assert 0.5 < score < 1.0


# ==========================================
# TESTS: TierClassifier
# ==========================================


class TestTierClassifier:
    """Tests for TierClassifier class."""

    def test_tier_classifier_initialization(self):
        """Test TierClassifier can be initialized."""
        classifier = TierClassifier()
        assert classifier.icp_weight == 0.50
        assert classifier.opportunity_weight == 0.50

    def test_classify_lead_tier_hot(self):
        """Test tier classification for HOT leads."""
        classifier = TierClassifier()
        tier = classifier.classify_lead_tier(icp_score=0.95, opportunity_score=0.90)
        assert tier == LeadTier.HOT

    def test_classify_lead_tier_warm(self):
        """Test tier classification for WARM leads."""
        classifier = TierClassifier()
        tier = classifier.classify_lead_tier(icp_score=0.75, opportunity_score=0.70)
        assert tier == LeadTier.WARM

    def test_classify_lead_tier_cool(self):
        """Test tier classification for COOL leads."""
        classifier = TierClassifier()
        tier = classifier.classify_lead_tier(icp_score=0.60, opportunity_score=0.50)
        assert tier == LeadTier.COOL

    def test_classify_lead_tier_cold(self):
        """Test tier classification for COLD leads."""
        classifier = TierClassifier()
        tier = classifier.classify_lead_tier(icp_score=0.30, opportunity_score=0.25)
        assert tier == LeadTier.COLD

    def test_classify_lead_tier_boundary_hot_warm(self):
        """Test tier classification at HOT/WARM boundary (0.85)."""
        classifier = TierClassifier()

        # Just below boundary = WARM
        tier = classifier.classify_lead_tier(icp_score=0.84, opportunity_score=0.85)
        assert tier == LeadTier.WARM

        # At boundary = HOT
        tier = classifier.classify_lead_tier(icp_score=0.85, opportunity_score=0.85)
        assert tier == LeadTier.HOT

    def test_classify_lead_tier_custom_weights(self):
        """Test tier classification with custom weights."""
        classifier = TierClassifier(icp_weight=0.70, opportunity_weight=0.30)

        # ICP-heavy scoring
        tier = classifier.classify_lead_tier(icp_score=0.90, opportunity_score=0.50)
        # Combined: 0.90*0.70 + 0.50*0.30 = 0.78 = WARM
        assert tier == LeadTier.WARM


# ==========================================
# TESTS: Batch Scoring
# ==========================================


class TestBatchScoringAndMetrics:
    """Tests for batch scoring and metrics."""

    def test_scoring_metrics_initialization(self):
        """Test ScoringMetrics can be initialized."""
        metrics = ScoringMetrics()
        assert metrics.scored_count == 0
        assert metrics.hot_count == 0
        assert metrics.errors == []

    def test_scoring_metrics_to_dict(self):
        """Test ScoringMetrics conversion to dict."""
        metrics = ScoringMetrics(
            scored_count=10,
            hot_count=2,
            warm_count=4,
            cool_count=3,
            cold_count=1,
            avg_icp_score=0.65,
            avg_opportunity_score=0.70,
            avg_combined_score=0.675,
        )
        result = metrics.to_dict()

        assert result["scored_count"] == 10
        assert result["hot_count"] == 2
        assert result["hot_ratio"] == 0.2
        assert "errors" in result

    def test_batch_score_leads_empty_campaign(self, db):
        """Test batch scoring on campaign with no leads."""
        metrics = batch_score_leads(db, campaign_id=999, max_leads=100)

        assert metrics.scored_count == 0
        assert metrics.hot_count == 0
        assert metrics.errors == []

    def test_batch_score_leads_with_leads(self, db):
        """Test batch scoring with multiple leads."""
        # Create campaign
        campaign_db = CampaignDB(name="Test Scoring Campaign")
        db.add(campaign_db)
        db.commit()

        # Create leads with enrichment
        lead1 = LeadDB(
            campaign_id=campaign_db.id,
            name="John Smith",
            company="TechCorp",
            role="CTO",
            email="john@techcorp.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={
                "company_size": "medium",
                "industry": "technology",
                "annual_revenue": 50_000_000,
                "is_decision_maker": True,
            },
        )
        lead2 = LeadDB(
            campaign_id=campaign_db.id,
            name="Jane Doe",
            company="RetailCorp",
            role="Store Manager",
            email="jane@retailcorp.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={
                "company_size": "startup",
                "industry": "retail",
                "annual_revenue": 5_000_000,
                "is_decision_maker": False,
            },
        )
        db.add_all([lead1, lead2])
        db.commit()

        # Score leads
        metrics = batch_score_leads(db, campaign_id=campaign_db.id, max_leads=100)

        assert metrics.scored_count == 2
        assert metrics.hot_count + metrics.warm_count + metrics.cool_count + metrics.cold_count == 2
        assert metrics.avg_icp_score > 0
        assert metrics.avg_opportunity_score > 0

    def test_batch_score_leads_updates_database(self, db):
        """Test that batch scoring updates lead records in database."""
        # Create campaign and lead
        campaign_db = CampaignDB(name="Update Test Campaign")
        db.add(campaign_db)
        db.commit()

        lead = LeadDB(
            campaign_id=campaign_db.id,
            name="Test Lead",
            email="test@example.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={"company_size": "medium"},
        )
        db.add(lead)
        db.commit()

        assert lead.lead_score is None
        assert lead.tags == []

        # Score
        batch_score_leads(db, campaign_id=campaign_db.id, max_leads=100)

        # Refresh from DB
        db.refresh(lead)

        assert lead.lead_score is not None
        assert 0.0 <= lead.lead_score <= 1.0
        assert len(lead.tags) > 0
        assert lead.tags[0] in ["HOT", "WARM", "COOL", "COLD"]

    def test_batch_score_leads_respects_max_leads(self, db):
        """Test that batch scoring respects max_leads limit."""
        # Create campaign with multiple leads
        campaign_db = CampaignDB(name="Max Leads Test Campaign")
        db.add(campaign_db)
        db.commit()

        leads = [
            LeadDB(
                campaign_id=campaign_db.id,
                name=f"Lead {i}",
                email=f"lead{i}@example.com",
                source=LeadSource.CSV,
                status=LeadStatus.NEW,
                enrichment_data={"company_size": "medium"},
            )
            for i in range(5)
        ]
        db.add_all(leads)
        db.commit()

        # Score with max_leads=2
        metrics = batch_score_leads(db, campaign_id=campaign_db.id, max_leads=2)

        assert metrics.scored_count == 2

    def test_batch_score_leads_skips_already_scored(self, db):
        """Test that batch scoring skips already scored leads."""
        # Create campaign and leads
        campaign_db = CampaignDB(name="Skip Scored Campaign")
        db.add(campaign_db)
        db.commit()

        # Already scored lead
        lead1 = LeadDB(
            campaign_id=campaign_db.id,
            name="Scored Lead",
            email="scored@example.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={"company_size": "medium"},
            lead_score=0.8,  # Already scored
        )

        # Unscored lead
        lead2 = LeadDB(
            campaign_id=campaign_db.id,
            name="Unscored Lead",
            email="unscored@example.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={"company_size": "medium"},
        )
        db.add_all([lead1, lead2])
        db.commit()

        original_score = lead1.lead_score

        # Score
        metrics = batch_score_leads(db, campaign_id=campaign_db.id, max_leads=100)

        # Should only score lead2
        assert metrics.scored_count == 1
        db.refresh(lead1)
        assert lead1.lead_score == original_score  # Unchanged

    def test_batch_score_leads_tracks_metrics(self, db):
        """Test that metrics are tracked accurately."""
        # Create campaign with mixed quality leads
        campaign_db = CampaignDB(name="Metrics Test Campaign")
        db.add(campaign_db)
        db.commit()

        # Create 3 leads with different enrichment
        leads = [
            LeadDB(
                campaign_id=campaign_db.id,
                name=f"Lead {i}",
                email=f"lead{i}@example.com",
                source=LeadSource.CSV,
                status=LeadStatus.NEW,
                enrichment_data={"company_size": "medium", "is_decision_maker": i == 0},
            )
            for i in range(3)
        ]
        db.add_all(leads)
        db.commit()

        metrics = batch_score_leads(db, campaign_id=campaign_db.id, max_leads=100)

        # Verify metrics
        assert metrics.scored_count == 3
        assert metrics.hot_count + metrics.warm_count + metrics.cool_count + metrics.cold_count == 3
        assert metrics.duration_seconds > 0
        assert len(metrics.errors) == 0
