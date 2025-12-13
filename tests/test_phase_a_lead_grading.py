"""
Test suite for Phase A: Mini-CRM & Lead Grading Service

Tests cover:
1. LeadGradeService - grade assignment, conversion probability, fit score
2. Domain Model Extensions - new CRM fields on Lead
3. Database Model Extensions - new columns on LeadDB with indexes
4. Orchestrator Integration - auto.py grading call
5. Operator Services - CRUD functions with auto-regrade
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

# Domain and database models
from aicmo.cam.domain import Lead, LeadGrade, CompanySize
from aicmo.cam.db_models import LeadDB, CampaignDB, Base
from aicmo.cam.lead_grading import LeadGradeService
from aicmo.operator_services import (
    get_lead_detail,
    update_lead_crm_fields,
    list_leads_by_grade,
    get_lead_grade_distribution,
)


# ============================================================================
# FIXTURES & SETUP
# ============================================================================

@pytest.fixture
def test_db():
    """Create in-memory SQLite database for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    
    Session = pytest.importorskip("sqlalchemy.orm").sessionmaker(bind=engine)
    db = Session()
    
    yield db
    
    db.close()


@pytest.fixture
def sample_campaign(test_db: Session) -> CampaignDB:
    """Create a test campaign."""
    campaign = CampaignDB(
        name="Test Campaign",
        description="Campaign for Phase A testing",
        target_niche="B2B SaaS",
        active=True,
        created_at=datetime.now(),
    )
    test_db.add(campaign)
    test_db.commit()
    test_db.refresh(campaign)
    
    return campaign


@pytest.fixture
def sample_lead(test_db: Session, sample_campaign: CampaignDB) -> LeadDB:
    """Create a test lead with basic fields."""
    lead = LeadDB(
        campaign_id=sample_campaign.id,
        name="John Smith",
        email="john@example.com",
        company="Acme Corp",
        lead_score=0.7,
        status="NEW",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    test_db.add(lead)
    test_db.commit()
    test_db.refresh(lead)
    
    return lead


# ============================================================================
# TEST: DOMAIN MODEL EXTENSIONS
# ============================================================================

class TestLeadDomainExtensions:
    """Test new CRM fields added to Lead domain model."""
    
    def test_lead_grade_enum_exists(self):
        """Verify LeadGrade enum exists with A/B/C/D values."""
        assert LeadGrade.A
        assert LeadGrade.B
        assert LeadGrade.C
        assert LeadGrade.D
    
    def test_company_size_enum_exists(self):
        """Verify CompanySize enum exists."""
        assert CompanySize.EARLY_STAGE
        assert CompanySize.MID_MARKET
        assert CompanySize.ENTERPRISE
    
    def test_lead_instantiation_with_crm_fields(self):
        """Test creating a Lead with new CRM fields."""
        lead = Lead(
            id=1,
            name="Alice Johnson",
            email="alice@company.com",
            company="Tech Corp",
            lead_score=0.75,
            company_size="mid_market",
            industry="SaaS",
            budget_estimate_range="$50K-$100K",
            timeline_months=3,
        )
        
        assert lead.company_size == "mid_market"
        assert lead.industry == "SaaS"
        assert lead.budget_estimate_range == "$50K-$100K"
        assert lead.timeline_months == 3


# ============================================================================
# TEST: DATABASE MODEL EXTENSIONS
# ============================================================================

class TestLeadDatabaseExtensions:
    """Test new columns added to LeadDB."""
    
    def test_leaddb_has_crm_columns(self, sample_lead: LeadDB):
        """Verify LeadDB has all new CRM columns."""
        # Company info
        assert hasattr(sample_lead, 'company_size')
        assert hasattr(sample_lead, 'industry')
        
        # Decision maker
        assert hasattr(sample_lead, 'decision_maker_name')
        assert hasattr(sample_lead, 'decision_maker_email')
        
        # Sales
        assert hasattr(sample_lead, 'budget_estimate_range')
        assert hasattr(sample_lead, 'timeline_months')
        assert hasattr(sample_lead, 'pain_points')
        
        # Grading
        assert hasattr(sample_lead, 'lead_grade')
        assert hasattr(sample_lead, 'conversion_probability')
    
    def test_leaddb_crm_fields_persistence(self, test_db: Session, sample_campaign: CampaignDB):
        """Test that CRM fields persist to database."""
        lead = LeadDB(
            campaign_id=sample_campaign.id,
            name="Sarah Miller",
            email="sarah@techco.com",
            company="TechCo",
            lead_score=0.8,
            company_size="enterprise",
            industry="FinTech",
            budget_estimate_range="$500K-$1M",
            timeline_months=2,
            decision_maker_name="Jane Doe",
            decision_maker_email="jane@techco.com",
            created_at=datetime.now(),
        )
        
        test_db.add(lead)
        test_db.commit()
        test_db.refresh(lead)
        
        # Query it back
        retrieved = test_db.query(LeadDB).filter(LeadDB.id == lead.id).first()
        assert retrieved is not None
        assert retrieved.company_size == "enterprise"
        assert retrieved.budget_estimate_range == "$500K-$1M"


# ============================================================================
# TEST: LEAD GRADING SERVICE
# ============================================================================

class TestLeadGradingService:
    """Test LeadGradeService grade assignment logic."""
    
    def test_assign_grade_with_high_score_and_signals(self):
        """Test grade assignment with high score and clear signals."""
        lead = Lead(
            id=1,
            name="Hot Prospect",
            email="hot@company.com",
            company="Big Corp",
            lead_score=0.9,
            budget_estimate_range="$1M+",
            timeline_months=1,
        )
        
        grade, prob, reason = LeadGradeService.assign_grade(lead)
        
        # High score + budget + timeline should yield A-grade
        assert grade == LeadGrade.A
        assert prob > 0.5
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_assign_grade_with_moderate_score(self):
        """Test grade assignment with moderate score."""
        lead = Lead(
            id=2,
            name="Warm Prospect",
            email="warm@company.com",
            company="Mid Corp",
            lead_score=0.65,
            budget_estimate_range="$100K-$500K",
            timeline_months=3,
        )
        
        grade, prob, reason = LeadGradeService.assign_grade(lead)
        
        # Moderate score should get B or higher
        assert grade in [LeadGrade.A, LeadGrade.B]
        assert 0.0 <= prob <= 1.0
    
    def test_assign_grade_with_low_score(self):
        """Test grade assignment with low score."""
        lead = Lead(
            id=3,
            name="Cold Lead",
            email="cold@company.com",
            company="Unknown Corp",
            lead_score=0.2,
        )
        
        grade, prob, reason = LeadGradeService.assign_grade(lead)
        
        # Low score should get C or D
        assert grade in [LeadGrade.C, LeadGrade.D]
        assert 0.0 <= prob <= 1.0
    
    def test_assign_grade_without_budget_falls_back(self):
        """Test that missing budget/timeline causes fallback to B even with high fit."""
        lead = Lead(
            id=4,
            name="No Budget Lead",
            email="nobudget@company.com",
            company="Corp",
            lead_score=0.9,  # High score
            # No budget_estimate_range - should prevent A grade
        )
        
        grade, prob, reason = LeadGradeService.assign_grade(lead)
        
        # Should fall back to B even with high fit_score
        assert grade == LeadGrade.B
        assert "missing" in reason.lower() or "budget" in reason.lower()
    
    def test_conversion_probability_in_valid_range(self):
        """Test that conversion probability is always 0.0-1.0."""
        leads = [
            Lead(id=1, name="L1", lead_score=0.0),
            Lead(id=2, name="L2", lead_score=0.5),
            Lead(id=3, name="L3", lead_score=1.0),
            Lead(id=4, name="L4", lead_score=0.7, timeline_months=2),
        ]
        
        for lead in leads:
            grade, prob, reason = LeadGradeService.assign_grade(lead)
            assert 0.0 <= prob <= 1.0
    
    def test_update_lead_grade_persists_to_db(self, test_db: Session, sample_lead: LeadDB):
        """Test that update_lead_grade persists changes to database."""
        lead_domain = Lead(
            id=sample_lead.id,
            name=sample_lead.name,
            email=sample_lead.email,
            company=sample_lead.company,
            lead_score=0.85,
            budget_estimate_range="$200K-$500K",
            timeline_months=2,
        )
        
        LeadGradeService.update_lead_grade(test_db, sample_lead.id, lead_domain)
        
        # Verify in database
        updated = test_db.query(LeadDB).filter(LeadDB.id == sample_lead.id).first()
        assert updated.lead_grade is not None
        assert updated.conversion_probability is not None
        assert updated.graded_at is not None


# ============================================================================
# TEST: OPERATOR SERVICES CRUD
# ============================================================================

class TestOperatorServicesCrud:
    """Test operator_services CRUD functions."""
    
    def test_get_lead_detail_returns_crm_fields(self, test_db: Session, sample_lead: LeadDB, sample_campaign: CampaignDB):
        """Test that get_lead_detail returns CRM fields."""
        sample_lead.company_size = "mid_market"
        sample_lead.industry = "SaaS"
        sample_lead.lead_grade = "B"
        test_db.commit()
        
        detail = get_lead_detail(test_db, sample_campaign.id, sample_lead.id)
        
        assert detail['id'] == sample_lead.id
        assert detail['company_size'] == "mid_market"
        assert detail['industry'] == "SaaS"
    
    def test_get_lead_detail_invalid_lead(self, test_db: Session, sample_campaign: CampaignDB):
        """Test get_lead_detail with non-existent lead."""
        result = get_lead_detail(test_db, sample_campaign.id, 99999)
        assert 'error' in result
    
    def test_update_lead_crm_fields(self, test_db: Session, sample_lead: LeadDB, sample_campaign: CampaignDB):
        """Test updating CRM fields."""
        updates = {
            "company_size": "enterprise",
            "industry": "FinTech",
            "budget_estimate_range": "$500K-$1M",
            "timeline_months": 2,
        }
        
        result = update_lead_crm_fields(
            test_db, sample_campaign.id, sample_lead.id, updates, auto_regrade=False
        )
        
        assert result['company_size'] == "enterprise"
        assert result['industry'] == "FinTech"
    
    def test_update_lead_with_auto_regrade(self, test_db: Session, sample_lead: LeadDB, sample_campaign: CampaignDB):
        """Test that auto_regrade triggers grade recalculation."""
        updates = {
            "budget_estimate_range": "$500K+",
            "timeline_months": 1,
        }
        
        result = update_lead_crm_fields(
            test_db, sample_campaign.id, sample_lead.id, updates, auto_regrade=True
        )
        
        # Should have graded the lead
        assert result['lead_grade'] is not None
    
    def test_list_leads_by_grade(self, test_db: Session, sample_campaign: CampaignDB):
        """Test filtering leads by grade."""
        # Create leads with different grades
        for i, grade in enumerate(['A', 'B', 'C']):
            lead = LeadDB(
                campaign_id=sample_campaign.id,
                name=f"Lead {i}",
                email=f"lead{i}@co.com",
                company="Test Co",
                lead_score=0.5,
                lead_grade=grade,
                status="NEW",
                created_at=datetime.now(),
            )
            test_db.add(lead)
        test_db.commit()
        
        result_a = list_leads_by_grade(test_db, sample_campaign.id, grade='A')
        assert 'leads' in result_a
        assert 'total' in result_a
    
    def test_get_lead_grade_distribution(self, test_db: Session, sample_campaign: CampaignDB):
        """Test grade distribution counts."""
        for i, grade in enumerate(['A', 'A', 'B', 'C']):
            lead = LeadDB(
                campaign_id=sample_campaign.id,
                name=f"Lead {i}",
                email=f"lead{i}@co.com",
                company="Test Co",
                lead_score=0.5,
                lead_grade=grade,
                status="NEW",
                created_at=datetime.now(),
            )
            test_db.add(lead)
        test_db.commit()
        
        distribution = get_lead_grade_distribution(test_db, sample_campaign.id)
        
        assert distribution['A'] == 2
        assert distribution['B'] == 1
        assert distribution['C'] == 1
        assert distribution['total'] == 4


# ============================================================================
# TEST: INTEGRATION
# ============================================================================

class TestPhaseAIntegration:
    """Integration tests for Phase A functionality."""
    
    def test_complete_lead_workflow(self, test_db: Session, sample_campaign: CampaignDB):
        """Test complete workflow: create lead → enrich → grade → query."""
        # 1. Create lead
        lead = LeadDB(
            campaign_id=sample_campaign.id,
            name="Test Lead",
            email="test@co.com",
            company="Test Co",
            lead_score=0.75,
            status="NEW",
            created_at=datetime.now(),
        )
        test_db.add(lead)
        test_db.commit()
        test_db.refresh(lead)
        
        # 2. Enrich with CRM data
        updates = {
            "company_size": "mid_market",
            "industry": "SaaS",
            "budget_estimate_range": "$250K-$500K",
            "timeline_months": 2,
        }
        
        detail = update_lead_crm_fields(test_db, sample_campaign.id, lead.id, updates, auto_regrade=True)
        
        # 3. Verify enrichment
        assert detail['company_size'] == "mid_market"
        assert detail['lead_grade'] is not None
        
        # 4. Query by grade
        dist = get_lead_grade_distribution(test_db, sample_campaign.id)
        assert dist['total'] == 1
    
    def test_auto_py_integration_exists(self):
        """Test that auto.py has LeadGradingService integration."""
        with open('/workspaces/AICMO/aicmo/cam/auto.py', 'r') as f:
            content = f.read()
        
        assert 'LeadGradeService' in content
        assert 'update_lead_grade' in content


# ============================================================================
# TEST: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and graceful degradation."""
    
    def test_grade_with_no_signals(self):
        """Test grading with minimal input."""
        lead = Lead(id=1, name="Minimal", email="m@co.com")
        grade, prob, reason = LeadGradeService.assign_grade(lead)
        
        assert grade in [LeadGrade.A, LeadGrade.B, LeadGrade.C, LeadGrade.D]
        assert 0.0 <= prob <= 1.0
    
    def test_grade_with_zero_score(self):
        """Test grading with lead_score of 0."""
        lead = Lead(id=1, name="Zero", email="z@co.com", lead_score=0.0)
        grade, prob, reason = LeadGradeService.assign_grade(lead)
        
        assert grade in [LeadGrade.A, LeadGrade.B, LeadGrade.C, LeadGrade.D]
    
    def test_grade_with_max_score(self):
        """Test grading with lead_score of 1.0."""
        lead = Lead(id=1, name="Max", email="m@co.com", lead_score=1.0)
        grade, prob, reason = LeadGradeService.assign_grade(lead)
        
        assert grade in [LeadGrade.A, LeadGrade.B, LeadGrade.C, LeadGrade.D]


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
