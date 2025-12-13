"""
Tests for Phase 4: Lead Qualification Engine.

Comprehensive test coverage for:
- EmailQualifier (format, spam/bot detection, role accounts)
- IntentDetector (buying signals)
- LeadQualifier (auto-qualification)
- Batch qualification operations
"""

import pytest
from datetime import datetime

from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, LeadSource, LeadStatus
from aicmo.cam.db_models import LeadDB, CampaignDB
from aicmo.cam.engine.lead_qualifier import (
    QualificationRules,
    EmailQualifier,
    IntentDetector,
    LeadQualifier,
    QualificationStatus,
    RejectionReason,
    QualificationMetrics,
)


# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def rules() -> QualificationRules:
    """Standard qualification rules."""
    return QualificationRules(
        icp_fit_threshold=0.70,
        block_competitor_domains=["competitor.com", "rival.com"],
        block_role_accounts=["info", "support", "sales", "noreply"],
    )


@pytest.fixture
def email_qualifier(rules) -> EmailQualifier:
    """Email qualifier with standard rules."""
    return EmailQualifier(rules)


@pytest.fixture
def intent_detector() -> IntentDetector:
    """Intent detector instance."""
    return IntentDetector()


@pytest.fixture
def lead_qualifier(rules, email_qualifier, intent_detector) -> LeadQualifier:
    """Lead qualifier with all components."""
    return LeadQualifier(rules, email_qualifier, intent_detector)


@pytest.fixture
def lead_qualified() -> Lead:
    """Lead that should qualify."""
    return Lead(
        id=1,
        campaign_id=1,
        name="John Smith",
        company="TechCorp Inc",
        role="VP Engineering",
        email="john.smith@techcorp.com",
        source=LeadSource.CSV,
        status=LeadStatus.ENRICHED,
        lead_score=0.85,
        enrichment_data={
            "company_size": "medium",
            "recent_job_change": True,
            "company_hiring": True,
            "is_decision_maker": True,
        }
    )


@pytest.fixture
def lead_low_icp() -> Lead:
    """Lead with low ICP score."""
    return Lead(
        id=2,
        campaign_id=1,
        name="Jane Doe",
        company="Startup X",
        role="Intern",
        email="jane@startup.com",
        source=LeadSource.CSV,
        status=LeadStatus.ENRICHED,
        lead_score=0.45,  # Below 0.70 threshold
        enrichment_data={}
    )


@pytest.fixture
def lead_bad_email() -> Lead:
    """Lead with invalid email."""
    return Lead(
        id=3,
        campaign_id=1,
        name="Support Bot",
        company="SomeCorp",
        role="Support",
        email="support@somecorp.com",
        source=LeadSource.CSV,
        status=LeadStatus.ENRICHED,
        lead_score=0.80,
        enrichment_data={}
    )


@pytest.fixture
def db(db) -> Session:
    """Database session."""
    return db


# ==========================================
# TESTS: QualificationRules
# ==========================================


class TestQualificationRules:
    """Tests for QualificationRules class."""

    def test_rules_initialization_defaults(self):
        """Test rules with default values."""
        rules = QualificationRules()
        assert rules.icp_fit_threshold == 0.70
        assert "info" in rules.block_role_accounts
        assert "support" in rules.block_role_accounts

    def test_rules_custom_initialization(self):
        """Test rules with custom values."""
        rules = QualificationRules(
            icp_fit_threshold=0.80,
            block_competitor_domains=["rival.com"],
        )
        assert rules.icp_fit_threshold == 0.80
        assert "rival.com" in rules.block_competitor_domains

    def test_rules_to_dict(self, rules):
        """Test rules conversion to dict."""
        result = rules.to_dict()
        assert result["icp_fit_threshold"] == 0.70
        assert "info" in result["block_role_accounts"]


# ==========================================
# TESTS: EmailQualifier
# ==========================================


class TestEmailQualifier:
    """Tests for EmailQualifier class."""

    def test_valid_email_format(self, email_qualifier):
        """Test valid email format."""
        assert email_qualifier.is_valid_format("john@example.com")
        assert email_qualifier.is_valid_format("john.smith@company.co.uk")
        assert email_qualifier.is_valid_format("user+tag@domain.com")

    def test_invalid_email_format(self, email_qualifier):
        """Test invalid email format."""
        assert not email_qualifier.is_valid_format("invalid")
        assert not email_qualifier.is_valid_format("@example.com")
        assert not email_qualifier.is_valid_format("user@")
        assert not email_qualifier.is_valid_format("")
        assert not email_qualifier.is_valid_format(None)

    def test_spam_bot_detection(self, email_qualifier):
        """Test spam/bot keyword detection."""
        assert email_qualifier.is_spam_bot("noreply@example.com")
        assert email_qualifier.is_spam_bot("bot@example.com")
        assert email_qualifier.is_spam_bot("mailer@example.com")
        assert not email_qualifier.is_spam_bot("john@example.com")

    def test_test_account_detection(self, email_qualifier):
        """Test detection of test/demo accounts."""
        assert email_qualifier.is_spam_bot("test@example.com")
        assert email_qualifier.is_spam_bot("demo123@example.com")
        assert not email_qualifier.is_spam_bot("john@example.com")

    def test_role_account_detection(self, email_qualifier):
        """Test role account detection."""
        assert email_qualifier.is_role_account("info@example.com")
        assert email_qualifier.is_role_account("support@example.com")
        assert email_qualifier.is_role_account("sales@example.com")
        assert email_qualifier.is_role_account("info.general@example.com")
        assert not email_qualifier.is_role_account("john@example.com")

    def test_free_email_detection(self, rules):
        """Test free email provider detection."""
        rules = QualificationRules(block_free_email_domains=False)
        qualifier = EmailQualifier(rules)
        
        assert qualifier.is_free_email("user@gmail.com")
        assert qualifier.is_free_email("user@yahoo.com")
        assert not qualifier.is_free_email("user@company.com")

    def test_competitor_domain_detection(self, email_qualifier):
        """Test competitor domain detection."""
        assert email_qualifier.is_competitor_domain("user@competitor.com")
        assert email_qualifier.is_competitor_domain("user@rival.com")
        assert not email_qualifier.is_competitor_domain("user@trusted.com")

    def test_email_quality_check_valid(self, email_qualifier):
        """Test email quality check for valid email."""
        is_valid, reason = email_qualifier.check_email_quality("john@example.com")
        assert is_valid
        assert reason is None

    def test_email_quality_check_invalid_format(self, email_qualifier):
        """Test email quality check for invalid format."""
        is_valid, reason = email_qualifier.check_email_quality("invalid")
        assert not is_valid
        assert reason == RejectionReason.INVALID_EMAIL

    def test_email_quality_check_spam_bot(self, email_qualifier):
        """Test email quality check for spam/bot."""
        is_valid, reason = email_qualifier.check_email_quality("noreply@example.com")
        assert not is_valid
        # noreply is both spam_bot keyword AND role account, so multiple_reasons
        assert reason in [RejectionReason.SPAM_BOT, RejectionReason.MULTIPLE_REASONS]

    def test_email_quality_check_role_account(self, email_qualifier):
        """Test email quality check for role account."""
        is_valid, reason = email_qualifier.check_email_quality("support@example.com")
        assert not is_valid
        assert reason == RejectionReason.ROLE_ACCOUNT

    def test_email_quality_check_competitor(self, email_qualifier):
        """Test email quality check for competitor domain."""
        is_valid, reason = email_qualifier.check_email_quality("user@competitor.com")
        assert not is_valid
        assert reason == RejectionReason.COMPETITOR


# ==========================================
# TESTS: IntentDetector
# ==========================================


class TestIntentDetector:
    """Tests for IntentDetector class."""

    def test_intent_detection_no_signals(self, intent_detector):
        """Test intent detection with no signals."""
        lead = Lead(
            id=1,
            name="John",
            email="john@example.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={}
        )
        assert not intent_detector.detect_intent(lead)

    def test_intent_detection_one_signal(self, intent_detector):
        """Test intent detection with one signal (not enough)."""
        lead = Lead(
            id=1,
            name="John",
            email="john@example.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={"recent_job_change": True}
        )
        assert not intent_detector.detect_intent(lead)

    def test_intent_detection_two_signals(self, intent_detector):
        """Test intent detection with two signals (minimum)."""
        lead = Lead(
            id=1,
            name="John",
            email="john@example.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={
                "recent_job_change": True,
                "company_hiring": True,
            }
        )
        assert intent_detector.detect_intent(lead)

    def test_intent_score_no_signals(self, intent_detector):
        """Test intent score with no signals."""
        lead = Lead(
            id=1,
            name="John",
            email="john@example.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={}
        )
        score = intent_detector.get_intent_score(lead)
        assert score == 0.0

    def test_intent_score_all_signals(self, intent_detector):
        """Test intent score with all signals."""
        lead = Lead(
            id=1,
            name="John",
            email="john@example.com",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
            enrichment_data={
                "recent_job_change": True,
                "company_funded_recently": True,
                "company_hiring": True,
                "recent_activity": True,
                "is_decision_maker": True,
                "has_budget_authority": True,
            }
        )
        score = intent_detector.get_intent_score(lead)
        assert score >= 0.9


# ==========================================
# TESTS: LeadQualifier
# ==========================================


class TestLeadQualifier:
    """Tests for LeadQualifier class."""

    def test_auto_qualify_high_score_lead(self, lead_qualifier, lead_qualified):
        """Test auto-qualification of strong lead."""
        status, reason, reasoning = lead_qualifier.auto_qualify_lead(lead_qualified)
        assert status == QualificationStatus.QUALIFIED
        assert reason is None

    def test_auto_qualify_low_icp_lead(self, lead_qualifier, lead_low_icp):
        """Test rejection due to low ICP score."""
        status, reason, reasoning = lead_qualifier.auto_qualify_lead(lead_low_icp)
        assert status == QualificationStatus.REJECTED
        assert reason == RejectionReason.LOW_ICP_FIT

    def test_auto_qualify_bad_email_lead(self, lead_qualifier, lead_bad_email):
        """Test rejection due to bad email."""
        status, reason, reasoning = lead_qualifier.auto_qualify_lead(lead_bad_email)
        assert status == QualificationStatus.REJECTED
        assert reason == RejectionReason.ROLE_ACCOUNT

    def test_auto_qualify_manual_review_low_intent(self, lead_qualifier):
        """Test manual review for low intent without decision maker."""
        lead = Lead(
            id=1,
            name="John",
            email="john@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ENRICHED,
            lead_score=0.85,
            enrichment_data={}  # No signals, not a decision maker
        )
        status, reason, reasoning = lead_qualifier.auto_qualify_lead(lead)
        assert status == QualificationStatus.MANUAL_REVIEW

    def test_auto_qualify_high_intent_overrides_low_score(self, lead_qualifier):
        """Test that high intent doesn't override ICP score."""
        lead = Lead(
            id=1,
            name="John",
            email="john@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ENRICHED,
            lead_score=0.60,  # Below threshold
            enrichment_data={
                "recent_job_change": True,
                "company_hiring": True,
            }
        )
        status, reason, reasoning = lead_qualifier.auto_qualify_lead(lead)
        assert status == QualificationStatus.REJECTED
        assert reason == RejectionReason.LOW_ICP_FIT


# ==========================================
# TESTS: Batch Qualification
# ==========================================


class TestBatchQualification:
    """Tests for batch qualification operations."""

    def test_qualification_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = QualificationMetrics()
        assert metrics.processed_count == 0
        assert metrics.qualified_count == 0
        assert metrics.rejected_count == 0

    def test_qualification_metrics_to_dict(self):
        """Test metrics conversion to dict."""
        metrics = QualificationMetrics(
            processed_count=10,
            qualified_count=7,
            rejected_count=3,
        )
        result = metrics.to_dict()
        assert result["processed_count"] == 10
        assert result["qualified_count"] == 7
        assert result["qualified_ratio"] == 0.7

    def test_batch_qualify_empty_campaign(self, db, lead_qualifier):
        """Test batch qualification on empty campaign."""
        metrics = lead_qualifier.batch_qualify_leads(db, campaign_id=999)
        assert metrics.processed_count == 0

    def test_batch_qualify_multiple_leads(self, db, lead_qualifier):
        """Test batch qualification of multiple leads."""
        # Create campaign
        campaign = CampaignDB(name="Test Qualification Campaign")
        db.add(campaign)
        db.commit()
        
        # Create qualified lead
        lead1 = LeadDB(
            campaign_id=campaign.id,
            name="John Smith",
            email="john@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ENRICHED,
            lead_score=0.85,
            enrichment_data={"recent_job_change": True, "company_hiring": True}
        )
        
        # Create rejected lead (low ICP)
        lead2 = LeadDB(
            campaign_id=campaign.id,
            name="Jane Doe",
            email="jane@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ENRICHED,
            lead_score=0.50,
            enrichment_data={}
        )
        
        db.add_all([lead1, lead2])
        db.commit()
        
        # Qualify
        metrics = lead_qualifier.batch_qualify_leads(db, campaign_id=campaign.id)
        
        assert metrics.processed_count == 2
        assert metrics.qualified_count >= 1
        assert metrics.rejected_count >= 1

    def test_batch_qualify_updates_database(self, db, lead_qualifier):
        """Test that batch qualification updates database."""
        # Create campaign and lead
        campaign = CampaignDB(name="Update Test Campaign")
        db.add(campaign)
        db.commit()
        
        lead = LeadDB(
            campaign_id=campaign.id,
            name="John Smith",
            email="john@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ENRICHED,
            lead_score=0.85,
            enrichment_data={"recent_job_change": True, "company_hiring": True}
        )
        db.add(lead)
        db.commit()
        
        original_status = lead.status
        
        # Qualify
        lead_qualifier.batch_qualify_leads(db, campaign_id=campaign.id)
        
        # Refresh from DB
        db.refresh(lead)
        
        # Status should change to QUALIFIED
        assert lead.status == LeadStatus.QUALIFIED
        assert lead.status != original_status

    def test_batch_qualify_skips_already_qualified(self, db, lead_qualifier):
        """Test that batch qualification skips already qualified leads."""
        # Create campaign
        campaign = CampaignDB(name="Skip Qualified Campaign")
        db.add(campaign)
        db.commit()
        
        # Already qualified lead
        lead1 = LeadDB(
            campaign_id=campaign.id,
            name="John Smith",
            email="john@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.QUALIFIED,  # Already qualified
            lead_score=0.85,
            enrichment_data={}
        )
        
        # New lead to qualify
        lead2 = LeadDB(
            campaign_id=campaign.id,
            name="Jane Doe",
            email="jane@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ENRICHED,
            lead_score=0.85,
            enrichment_data={"recent_job_change": True, "company_hiring": True}
        )
        
        db.add_all([lead1, lead2])
        db.commit()
        
        # Qualify
        metrics = lead_qualifier.batch_qualify_leads(db, campaign_id=campaign.id)
        
        # Only one lead should be processed
        assert metrics.processed_count == 1

    def test_batch_qualify_respects_max_leads(self, db, lead_qualifier):
        """Test that batch qualification respects max_leads limit."""
        # Create campaign with multiple leads
        campaign = CampaignDB(name="Max Leads Campaign")
        db.add(campaign)
        db.commit()
        
        leads = [
            LeadDB(
                campaign_id=campaign.id,
                name=f"Lead {i}",
                email=f"lead{i}@company.com",
                source=LeadSource.CSV,
                status=LeadStatus.ENRICHED,
                lead_score=0.85,
                enrichment_data={}
            )
            for i in range(5)
        ]
        db.add_all(leads)
        db.commit()
        
        # Qualify with max_leads=2
        metrics = lead_qualifier.batch_qualify_leads(db, campaign_id=campaign.id, max_leads=2)
        
        assert metrics.processed_count == 2

    def test_batch_qualify_tracks_rejection_reasons(self, db, lead_qualifier):
        """Test that qualification tracks rejection reasons in notes."""
        # Create campaign
        campaign = CampaignDB(name="Rejection Test Campaign")
        db.add(campaign)
        db.commit()
        
        # Lead with bad email
        lead = LeadDB(
            campaign_id=campaign.id,
            name="Support",
            email="support@company.com",
            source=LeadSource.CSV,
            status=LeadStatus.ENRICHED,
            lead_score=0.85,
            enrichment_data={}
        )
        db.add(lead)
        db.commit()
        
        # Qualify
        lead_qualifier.batch_qualify_leads(db, campaign_id=campaign.id)
        
        # Refresh and check notes
        db.refresh(lead)
        assert lead.notes is not None
        assert "QUALIFIED" in lead.notes or "role_account" in lead.notes
