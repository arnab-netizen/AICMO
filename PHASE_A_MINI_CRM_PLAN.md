# Phase A: Mini-CRM & Sales Pipeline - Implementation Plan

## Objective
Extend the Lead domain and database models with comprehensive CRM fields to support detailed prospect management and grading.

## Current State Analysis

### What Exists ✅
- Basic Lead model with core fields: name, company, role, email, linkedin_url
- LeadStatus enum: NEW, ENRICHED, CONTACTED, REPLIED, QUALIFIED, LOST
- lead_score (0.0-1.0) for basic ranking
- Database persistence via LeadDB + SQLAlchemy
- Lead tagging support via JSON field

### What's Missing ❌
- LeadGrade enum (A/B/C/D for letter grading)
- Company research fields (industry, growth_rate, funding, competitors, website)
- Decision maker tracking (decision_maker_name, decision_maker_email, decision_maker_role)
- Budget & timeline fields (budget_estimate_range, timeline_in_months)
- Pain points tracking (pain_points: JSON list)
- Company size categorization (company_size: early_stage | mid_market | enterprise)
- Revenue indicators (annual_revenue)
- Number of employees tracking (employee_count)
- Conversion probability field (0.0-1.0)
- Lead fit score for service (fit_score_for_service: 0.0-1.0)
- Source of lead discovery (referral_source, referred_by_name)
- Proposal/contract tracking (proposal_generated_at, contract_signed_at)

## Implementation Scope

### Files to Create
```
1. aicmo/cam/lead_grading.py (new)
   - LeadGradeService class with grading logic
   - Methods: assign_grade(), update_grade_async()
   - Grading criteria configuration
```

### Files to Modify
```
1. aicmo/cam/domain.py
   - Add CompanySize enum (early_stage, mid_market, enterprise)
   - Add LeadGrade enum (A, B, C, D with descriptions)
   - Extend Lead class with ~15 new fields

2. aicmo/cam/db_models.py
   - Extend LeadDB with corresponding database columns
   - Add indexes on grade, fit_score, conversion_probability
   - Add migration note for schema changes

3. aicmo/cam/engine/state_machine.py
   - Update grading logic in status transitions
   - Use lead_grade for retry/sequence decisions

4. aicmo/cam/orchestrator.py
   - Call LeadGradeService after enrichment step
   - Update lead_grade before persistence

5. aicmo/operator_services.py
   - Add API endpoints for lead CRUD with new fields
   - Add GET /campaigns/{id}/leads/{id} for lead detail view
   - Add PATCH /campaigns/{id}/leads/{id} for lead updates

6. tests/test_lead_grading.py (new)
   - Test LeadGradeService.assign_grade() with various inputs
   - Test grade persistence to database
   - Test grade updates
   - Test grade-based sequencing (15-18 tests)
```

### Database Migration
```sql
ALTER TABLE cam_leads ADD COLUMN (
    lead_grade VARCHAR(1) DEFAULT 'D',           -- A, B, C, D
    conversion_probability FLOAT DEFAULT 0.0,     -- 0.0-1.0
    fit_score_for_service FLOAT DEFAULT 0.0,      -- 0.0-1.0
    
    -- Company Research
    industry VARCHAR,
    growth_rate VARCHAR,                          -- e.g., "10-20%", "High"
    annual_revenue VARCHAR,                       -- e.g., "$1M-$5M"
    employee_count INT,
    company_website VARCHAR,
    company_headquarters VARCHAR,
    founding_year INT,
    funding_status VARCHAR,                       -- bootstrapped, funded, etc.
    
    -- Decision Maker
    decision_maker_name VARCHAR,
    decision_maker_email VARCHAR,
    decision_maker_role VARCHAR,
    decision_maker_linkedin VARCHAR,
    
    -- Sales Info
    budget_estimate_range VARCHAR,                -- e.g., "$10K-$50K"
    timeline_months INT,
    pain_points TEXT,                             -- JSON array of strings
    buying_signals TEXT,                          -- JSON object with signal data
    
    -- Tracking
    proposal_generated_at DATETIME,
    proposal_content_id VARCHAR,
    contract_signed_at DATETIME,
    referral_source VARCHAR,
    referred_by_name VARCHAR,
    
    -- Auditing
    graded_at DATETIME,
    grade_reason VARCHAR,
    
    -- Indexes
    KEY idx_grade (lead_grade),
    KEY idx_conversion_prob (conversion_probability),
    KEY idx_fit_score (fit_score_for_service)
);
```

## Implementation Steps

### Step 1: Update Domain Models (30 min)
**File:** `aicmo/cam/domain.py`

Changes:
```python
# Add new enum
class CompanySize(str, Enum):
    """Company size category."""
    EARLY_STAGE = "early_stage"      # < 10 employees
    MID_MARKET = "mid_market"        # 10-500 employees
    ENTERPRISE = "enterprise"        # 500+ employees

class LeadGrade(str, Enum):
    """Lead quality grade."""
    A = "A"  # Hot lead - high fit, budget, timeline
    B = "B"  # Warm lead - good fit, some signals
    C = "C"  # Cool lead - potential, needs nurturing
    D = "D"  # Cold lead - low fit, early stage

# Extend Lead class
class Lead(AicmoBaseModel):
    # ... existing fields ...
    
    # CRM Fields - Company Info
    company_size: Optional[str] = None  # CompanySize enum value
    industry: Optional[str] = None
    growth_rate: Optional[str] = None  # e.g., "10-20%"
    annual_revenue: Optional[str] = None  # e.g., "$1M-$5M"
    employee_count: Optional[int] = None
    company_website: Optional[str] = None
    company_headquarters: Optional[str] = None
    founding_year: Optional[int] = None
    funding_status: Optional[str] = None
    
    # CRM Fields - Decision Maker
    decision_maker_name: Optional[str] = None
    decision_maker_email: Optional[str] = None
    decision_maker_role: Optional[str] = None
    decision_maker_linkedin: Optional[str] = None
    
    # CRM Fields - Sales
    budget_estimate_range: Optional[str] = None  # e.g., "$10K-$50K"
    timeline_months: Optional[int] = None
    pain_points: Optional[List[str]] = None
    buying_signals: Optional[Dict[str, Any]] = None
    
    # CRM Fields - Grading
    lead_grade: Optional[str] = None  # LeadGrade enum value
    conversion_probability: Optional[float] = None  # 0.0-1.0
    fit_score_for_service: Optional[float] = None  # 0.0-1.0
    graded_at: Optional[datetime] = None
    grade_reason: Optional[str] = None
    
    # CRM Fields - Tracking
    proposal_generated_at: Optional[datetime] = None
    proposal_content_id: Optional[str] = None
    contract_signed_at: Optional[datetime] = None
    referral_source: Optional[str] = None
    referred_by_name: Optional[str] = None
```

### Step 2: Update Database Models (30 min)
**File:** `aicmo/cam/db_models.py`

Changes:
```python
class LeadDB(Base):
    # ... existing fields ...
    
    # Company Info
    company_size = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    growth_rate = Column(String, nullable=True)
    annual_revenue = Column(String, nullable=True)
    employee_count = Column(Integer, nullable=True)
    company_website = Column(String, nullable=True)
    company_headquarters = Column(String, nullable=True)
    founding_year = Column(Integer, nullable=True)
    funding_status = Column(String, nullable=True)
    
    # Decision Maker
    decision_maker_name = Column(String, nullable=True)
    decision_maker_email = Column(String, nullable=True)
    decision_maker_role = Column(String, nullable=True)
    decision_maker_linkedin = Column(String, nullable=True)
    
    # Sales
    budget_estimate_range = Column(String, nullable=True)
    timeline_months = Column(Integer, nullable=True)
    pain_points = Column(JSON, nullable=True)
    buying_signals = Column(JSON, nullable=True)
    
    # Grading
    lead_grade = Column(String, nullable=True, default="D")
    conversion_probability = Column(Float, nullable=True, default=0.0)
    fit_score_for_service = Column(Float, nullable=True, default=0.0)
    graded_at = Column(DateTime, nullable=True)
    grade_reason = Column(String, nullable=True)
    
    # Tracking
    proposal_generated_at = Column(DateTime, nullable=True)
    proposal_content_id = Column(String, nullable=True)
    contract_signed_at = Column(DateTime, nullable=True)
    referral_source = Column(String, nullable=True)
    referred_by_name = Column(String, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_lead_grade', 'lead_grade'),
        Index('idx_conversion_probability', 'conversion_probability'),
        Index('idx_fit_score_for_service', 'fit_score_for_service'),
    )
```

### Step 3: Create LeadGradingService (45 min)
**File:** `aicmo/cam/lead_grading.py`

```python
"""
Lead Grading Service — Phase A

Assigns letter grades (A/B/C/D) to leads based on company fit, budget, timeline, engagement.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, LeadGrade
from aicmo.cam.db_models import LeadDB

import logging

logger = logging.getLogger(__name__)


class LeadGradeService:
    """
    Assigns letter grades to leads based on multi-factor scoring.
    
    Grading Criteria:
    - A: Hot lead (fit_score >= 0.8, budget + timeline clear)
    - B: Warm lead (fit_score >= 0.6, some buying signals)
    - C: Cool lead (fit_score >= 0.4, potential, needs nurturing)
    - D: Cold lead (fit_score < 0.4, low priority)
    """
    
    GRADE_THRESHOLDS = {
        LeadGrade.A: {'fit_score': 0.8, 'conversion_prob': 0.7},
        LeadGrade.B: {'fit_score': 0.6, 'conversion_prob': 0.4},
        LeadGrade.C: {'fit_score': 0.4, 'conversion_prob': 0.2},
        LeadGrade.D: {'fit_score': 0.0, 'conversion_prob': 0.0},
    }
    
    @staticmethod
    def assign_grade(lead: Lead) -> tuple[str, float, str]:
        """
        Assign a letter grade to a lead.
        
        Returns:
            tuple: (grade: A/B/C/D, conversion_probability: 0.0-1.0, reason: explanation)
        """
        # Base score from lead_score
        base_score = lead.lead_score or 0.0
        
        # Bonus points for buying signals
        budget_bonus = 0.2 if lead.budget_estimate_range else 0.0
        timeline_bonus = 0.1 if lead.timeline_months else 0.0
        pain_points_bonus = 0.1 if lead.pain_points and len(lead.pain_points) > 0 else 0.0
        
        # Fit score: 0.0-1.0
        fit_score = min(1.0, base_score + budget_bonus + timeline_bonus + pain_points_bonus)
        
        # Determine conversion probability based on engagement + fit
        engagement_factor = min(1.0, (lead.tags.__len__() or 0) * 0.1)  # Tag count
        conversion_prob = fit_score * 0.7 + engagement_factor * 0.3
        
        # Assign grade based on thresholds
        if fit_score >= LeadGradeService.GRADE_THRESHOLDS[LeadGrade.A]['fit_score']:
            if lead.budget_estimate_range and lead.timeline_months:
                grade = LeadGrade.A
                reason = "High fit + clear budget and timeline"
            else:
                grade = LeadGrade.B
                reason = "High fit but missing budget/timeline clarity"
        elif fit_score >= LeadGradeService.GRADE_THRESHOLDS[LeadGrade.B]['fit_score']:
            grade = LeadGrade.B
            reason = "Good fit with some buying signals"
        elif fit_score >= LeadGradeService.GRADE_THRESHOLDS[LeadGrade.C]['fit_score']:
            grade = LeadGrade.C
            reason = "Moderate fit, potential with nurturing"
        else:
            grade = LeadGrade.D
            reason = "Low fit, cold lead"
        
        return grade, conversion_prob, reason
    
    @staticmethod
    def update_lead_grade(
        db: Session,
        lead_id: int,
        lead: Lead,
    ) -> LeadDB:
        """
        Update a lead's grade in the database.
        
        Args:
            db: Database session
            lead_id: Lead ID
            lead: Lead domain model with updated fields
            
        Returns:
            Updated LeadDB instance
        """
        lead_db = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
        if not lead_db:
            logger.warning(f"Lead {lead_id} not found for grading")
            return None
        
        # Assign new grade
        grade, conversion_prob, reason = LeadGradeService.assign_grade(lead)
        
        # Update database
        lead_db.lead_grade = grade
        lead_db.conversion_probability = conversion_prob
        lead_db.fit_score_for_service = lead.lead_score or 0.0
        lead_db.grade_reason = reason
        lead_db.graded_at = datetime.utcnow()
        
        db.commit()
        db.refresh(lead_db)
        
        logger.info(f"Lead {lead_id} graded as {grade}: {reason}")
        
        return lead_db
```

### Step 4: Integrate into Orchestrator (20 min)
**File:** `aicmo/cam/orchestrator.py`

Add to enrichment step:
```python
from aicmo.cam.lead_grading import LeadGradeService

def enrich_and_grade_leads(db: Session, campaign_db: CampaignDB):
    """
    Enrich leads and assign grades.
    """
    # ... existing enrichment logic ...
    
    for lead_db in leads:
        # Convert to domain model
        lead = _to_domain_lead(lead_db)
        
        # Enrich (existing logic)
        enriched_lead = await enrich_lead(lead, enrichers)
        
        # GRADE (NEW)
        grading_service = LeadGradeService()
        grading_service.update_lead_grade(db, lead_db.id, enriched_lead)
        
        # Persist
        lead_db = _persist_lead_updates(db, lead_db, enriched_lead)
```

### Step 5: Update API Endpoints (45 min)
**File:** `aicmo/operator_services.py`

Add/modify endpoints:
```python
# GET /campaigns/{id}/leads/{id} - Get lead detail
@app.get("/campaigns/{campaign_id}/leads/{lead_id}")
async def get_lead_detail(campaign_id: int, lead_id: int):
    """Get detailed lead information including new CRM fields."""
    with get_db_session() as db:
        lead = db.query(LeadDB).filter(
            LeadDB.id == lead_id,
            LeadDB.campaign_id == campaign_id
        ).first()
        
        if not lead:
            return {"error": "Lead not found"}
        
        return {
            # ... existing fields ...
            "lead_grade": lead.lead_grade,
            "conversion_probability": lead.conversion_probability,
            "fit_score_for_service": lead.fit_score_for_service,
            "company_size": lead.company_size,
            "industry": lead.industry,
            "budget_estimate_range": lead.budget_estimate_range,
            "timeline_months": lead.timeline_months,
            "decision_maker_name": lead.decision_maker_name,
            "decision_maker_email": lead.decision_maker_email,
            "pain_points": lead.pain_points,
            "graded_at": lead.graded_at,
            "grade_reason": lead.grade_reason,
        }

# PATCH /campaigns/{id}/leads/{id} - Update lead
@app.patch("/campaigns/{campaign_id}/leads/{lead_id}")
async def update_lead(campaign_id: int, lead_id: int, updates: dict):
    """Update lead CRM fields."""
    with get_db_session() as db:
        lead = db.query(LeadDB).filter(
            LeadDB.id == lead_id,
            LeadDB.campaign_id == campaign_id
        ).first()
        
        if not lead:
            return {"error": "Lead not found"}
        
        # Map update fields to database columns
        allowed_fields = [
            'company_size', 'industry', 'growth_rate', 'annual_revenue',
            'employee_count', 'budget_estimate_range', 'timeline_months',
            'decision_maker_name', 'decision_maker_email', 'decision_maker_role',
            'pain_points', 'buying_signals'
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(lead, field, value)
        
        db.commit()
        
        # Re-grade after updates
        lead_domain = _to_domain_lead(lead)
        LeadGradeService.update_lead_grade(db, lead_id, lead_domain)
        
        return {"success": True, "lead_id": lead_id}

# GET /campaigns/{id}/leads - List leads with grades
@app.get("/campaigns/{campaign_id}/leads")
async def list_leads(campaign_id: int, grade: Optional[str] = None):
    """List leads, optionally filtered by grade."""
    with get_db_session() as db:
        query = db.query(LeadDB).filter(LeadDB.campaign_id == campaign_id)
        
        if grade:
            query = query.filter(LeadDB.lead_grade == grade)
        
        leads = query.all()
        
        return {
            "leads": [
                {
                    "id": l.id,
                    "name": l.name,
                    "company": l.company,
                    "email": l.email,
                    "lead_grade": l.lead_grade,
                    "conversion_probability": l.conversion_probability,
                    "status": l.status,
                }
                for l in leads
            ]
        }
```

### Step 6: Create Comprehensive Test Suite (90 min)
**File:** `tests/test_lead_grading.py`

```python
"""
Tests for Lead Grading Service — Phase A
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, LeadGrade
from aicmo.cam.db_models import LeadDB, CampaignDB
from aicmo.cam.lead_grading import LeadGradeService
from aicmo.core.db import get_session


class TestLeadGradingService:
    """Test suite for LeadGradeService."""
    
    def test_assign_grade_hot_lead(self):
        """A-grade: High fit + budget + timeline."""
        lead = Lead(
            name="John Smith",
            company="TechCorp",
            email="john@techcorp.com",
            lead_score=0.85,
            budget_estimate_range="$50K-$100K",
            timeline_months=3,
            pain_points=["slow growth", "high CAC"],
            tags=["qualified", "urgent"]
        )
        
        grade, conversion_prob, reason = LeadGradeService.assign_grade(lead)
        
        assert grade == LeadGrade.A
        assert conversion_prob > 0.7
        assert "High fit" in reason
    
    def test_assign_grade_warm_lead(self):
        """B-grade: Good fit with some signals."""
        lead = Lead(
            name="Jane Doe",
            company="MarketingCo",
            email="jane@marketingco.com",
            lead_score=0.65,
            budget_estimate_range="$20K-$50K",
            pain_points=["low conversion rate"],
            tags=["interested"]
        )
        
        grade, conversion_prob, reason = LeadGradeService.assign_grade(lead)
        
        assert grade == LeadGrade.B
        assert conversion_prob > 0.4
        assert "Good fit" in reason or "warm" in reason.lower()
    
    def test_assign_grade_cool_lead(self):
        """C-grade: Moderate fit, nurture needed."""
        lead = Lead(
            name="Bob Wilson",
            company="StartupXYZ",
            email="bob@startupxyz.com",
            lead_score=0.50,
            pain_points=["scaling challenges"]
        )
        
        grade, conversion_prob, reason = LeadGradeService.assign_grade(lead)
        
        assert grade == LeadGrade.C
        assert conversion_prob > 0.0
        assert "Moderate fit" in reason or "nurtur" in reason.lower()
    
    def test_assign_grade_cold_lead(self):
        """D-grade: Low fit, cold."""
        lead = Lead(
            name="Alice Cooper",
            company="OldIndustries",
            email="alice@oldindustries.com",
            lead_score=0.2
        )
        
        grade, conversion_prob, reason = LeadGradeService.assign_grade(lead)
        
        assert grade == LeadGrade.D
        assert conversion_prob < 0.3
        assert "Low fit" in reason or "cold" in reason.lower()
    
    def test_assign_grade_no_lead_score(self):
        """Handle leads with no lead_score."""
        lead = Lead(
            name="Charlie Brown",
            company="UnknownCo",
            email="charlie@unknown.com",
            lead_score=None
        )
        
        grade, conversion_prob, reason = LeadGradeService.assign_grade(lead)
        
        assert grade == LeadGrade.D
        assert conversion_prob >= 0.0
    
    def test_assign_grade_with_all_signals(self):
        """Lead with all positive signals should be A-grade."""
        lead = Lead(
            name="David Smith",
            company="BigCorp",
            email="david@bigcorp.com",
            lead_score=0.9,
            budget_estimate_range="$100K+",
            timeline_months=2,
            pain_points=["high bounce rate", "low engagement", "scaling"],
            tags=["hot", "urgent", "vip"],
            company_size="enterprise",
            industry="technology",
            employee_count=500
        )
        
        grade, conversion_prob, reason = LeadGradeService.assign_grade(lead)
        
        assert grade == LeadGrade.A
        assert conversion_prob > 0.75
    
    def test_update_lead_grade_in_database(self, db_session: Session):
        """Test persisting grade to database."""
        # Create campaign
        campaign = CampaignDB(name="Test Campaign", active=True)
        db_session.add(campaign)
        db_session.flush()
        
        # Create lead
        lead_db = LeadDB(
            campaign_id=campaign.id,
            name="Test Lead",
            company="TestCo",
            email="test@testco.com",
            lead_score=0.75,
            budget_estimate_range="$50K",
            timeline_months=2
        )
        db_session.add(lead_db)
        db_session.flush()
        
        # Convert to domain, grade, and update
        lead_domain = Lead(
            name="Test Lead",
            company="TestCo",
            email="test@testco.com",
            lead_score=0.75,
            budget_estimate_range="$50K",
            timeline_months=2
        )
        
        updated_lead = LeadGradeService.update_lead_grade(db_session, lead_db.id, lead_domain)
        
        assert updated_lead.lead_grade in [LeadGrade.A, LeadGrade.B, LeadGrade.C, LeadGrade.D]
        assert updated_lead.conversion_probability is not None
        assert updated_lead.graded_at is not None
        assert updated_lead.grade_reason is not None
    
    def test_conversion_probability_capped_at_1(self):
        """Conversion probability should never exceed 1.0."""
        lead = Lead(
            name="Over-optimistic Lead",
            company="AlmostCertain",
            email="almost@certain.com",
            lead_score=1.0,
            budget_estimate_range="$500K+",
            timeline_months=1,
            pain_points=["urgent"] * 10,
            tags=["hot", "qualified", "ready", "urgent"]
        )
        
        grade, conversion_prob, reason = LeadGradeService.assign_grade(lead)
        
        assert conversion_prob <= 1.0
    
    def test_grade_upgrade_after_new_signals(self, db_session: Session):
        """Grade should upgrade when new buying signals added."""
        # Create campaign and lead
        campaign = CampaignDB(name="Test Campaign 2", active=True)
        db_session.add(campaign)
        db_session.flush()
        
        lead_db = LeadDB(
            campaign_id=campaign.id,
            name="Upgrading Lead",
            company="UpgradeCo",
            email="upgrade@upgradeco.com",
            lead_score=0.50,
            lead_grade="C"
        )
        db_session.add(lead_db)
        db_session.flush()
        
        # First grade: C
        lead_domain = Lead(
            name="Upgrading Lead",
            company="UpgradeCo",
            email="upgrade@upgradeco.com",
            lead_score=0.50
        )
        LeadGradeService.update_lead_grade(db_session, lead_db.id, lead_domain)
        db_session.refresh(lead_db)
        initial_grade = lead_db.lead_grade
        
        # Add budget and timeline, re-grade
        lead_domain.lead_score = 0.70
        lead_domain.budget_estimate_range = "$50K"
        lead_domain.timeline_months = 2
        LeadGradeService.update_lead_grade(db_session, lead_db.id, lead_domain)
        db_session.refresh(lead_db)
        upgraded_grade = lead_db.lead_grade
        
        # Grade should improve
        grade_order = [LeadGrade.D, LeadGrade.C, LeadGrade.B, LeadGrade.A]
        assert grade_order.index(upgraded_grade) > grade_order.index(initial_grade)


class TestLeadCRMFields:
    """Test that new CRM fields are properly persisted."""
    
    def test_lead_company_size_field(self, db_session: Session):
        """Test company_size field persistence."""
        campaign = CampaignDB(name="CRM Test Campaign", active=True)
        db_session.add(campaign)
        db_session.flush()
        
        lead = LeadDB(
            campaign_id=campaign.id,
            name="Enterprise Lead",
            company="BigCorp Inc",
            email="contact@bigcorp.com",
            company_size="enterprise",
            employee_count=5000
        )
        db_session.add(lead)
        db_session.commit()
        
        retrieved = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        assert retrieved.company_size == "enterprise"
        assert retrieved.employee_count == 5000
    
    def test_lead_decision_maker_fields(self, db_session: Session):
        """Test decision maker tracking."""
        campaign = CampaignDB(name="Decision Maker Test", active=True)
        db_session.add(campaign)
        db_session.flush()
        
        lead = LeadDB(
            campaign_id=campaign.id,
            name="Company Contact",
            company="DecisionCorp",
            email="company@decisioncorp.com",
            decision_maker_name="John Executive",
            decision_maker_email="john@decisioncorp.com",
            decision_maker_role="VP of Operations",
            decision_maker_linkedin="linkedin.com/in/johnexec"
        )
        db_session.add(lead)
        db_session.commit()
        
        retrieved = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        assert retrieved.decision_maker_name == "John Executive"
        assert retrieved.decision_maker_email == "john@decisioncorp.com"
        assert retrieved.decision_maker_role == "VP of Operations"
    
    def test_lead_pain_points_json(self, db_session: Session):
        """Test pain_points JSON storage."""
        campaign = CampaignDB(name="Pain Points Test", active=True)
        db_session.add(campaign)
        db_session.flush()
        
        pain_points = ["high CAC", "low retention", "scaling challenges"]
        
        lead = LeadDB(
            campaign_id=campaign.id,
            name="Problem Company",
            company="ProblemsInc",
            email="help@problemsinc.com",
            pain_points=pain_points
        )
        db_session.add(lead)
        db_session.commit()
        
        retrieved = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        assert retrieved.pain_points == pain_points
        assert len(retrieved.pain_points) == 3
```

## Testing Command

```bash
cd /workspaces/AICMO

# Run Phase A tests only
python -m pytest tests/test_lead_grading.py -v

# Run all tests to ensure no regressions
python -m pytest tests/ -v --tb=short
```

## Success Criteria

- [ ] LeadGrade enum defined (A/B/C/D)
- [ ] LeadGradeService implemented with grading logic
- [ ] Lead domain extended with 15+ new CRM fields
- [ ] LeadDB extended with corresponding columns
- [ ] All 15+ database columns properly indexed
- [ ] Orchestrator calls LeadGradeService after enrichment
- [ ] API endpoints added: GET /leads/{id}, PATCH /leads/{id}, GET /leads?grade=A
- [ ] 18 tests written and all passing
- [ ] No regressions in existing tests (63/64 still passing + new 18 = 81 total)
- [ ] Code reviewed and pushed to origin/main
- [ ] AICMO_ACQUISITION_STATUS.md updated with Phase A completion

## Estimated Effort
- Implementation: 2-3 hours
- Testing: 1.5-2 hours
- Total: 3.5-5 hours (can complete in 1 day)

## Next Phase
Phase B: Outreach Channels (Email + LinkedIn + Contact Forms)
