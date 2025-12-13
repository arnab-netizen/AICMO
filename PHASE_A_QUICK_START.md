# Phase A Quick Reference — Mini-CRM & Lead Grading

## What's New

### 1. Lead Grades (A/B/C/D)
- **A (Hot):** fit_score ≥ 0.8 + clear budget + timeline
- **B (Warm):** fit_score ≥ 0.6 OR high fit but missing budget/timeline
- **C (Cool):** fit_score ≥ 0.4, potential with nurturing
- **D (Cold):** fit_score < 0.4, low priority

### 2. New Lead Fields (25 total)

**Company Info:** company_size, industry, growth_rate, annual_revenue, employee_count, company_website, company_headquarters, founding_year, funding_status

**Decision Maker:** decision_maker_name, decision_maker_email, decision_maker_role, decision_maker_linkedin

**Sales:** budget_estimate_range, timeline_months, pain_points, buying_signals

**Grading:** lead_grade, conversion_probability, fit_score_for_service, graded_at, grade_reason

**Tracking:** proposal_generated_at, proposal_content_id, contract_signed_at, referral_source, referred_by_name

### 3. Usage Examples

#### Automatic Grading (in auto.py)
```python
from aicmo.cam.lead_grading import LeadGradeService

# Create domain model from DB record
lead_domain = Lead(
    id=lead_db.id,
    name=lead_db.name,
    email=lead_db.email,
    lead_score=lead_db.lead_score,
    budget_estimate_range=lead_db.budget_estimate_range,
    timeline_months=lead_db.timeline_months,
)

# Grade automatically persists to DB
LeadGradeService.update_lead_grade(db, lead_db.id, lead_domain)
```

#### Get Lead Detail
```python
from aicmo.operator_services import get_lead_detail

detail = get_lead_detail(db, campaign_id=1, lead_id=42)
# Returns: {
#   "id": 42,
#   "name": "John Smith",
#   "company": "Acme Corp",
#   "lead_grade": "A",
#   "conversion_probability": 0.85,
#   "fit_score_for_service": 0.82,
#   ...all CRM fields...
# }
```

#### Update Lead & Auto-Regrade
```python
from aicmo.operator_services import update_lead_crm_fields

result = update_lead_crm_fields(
    db,
    campaign_id=1,
    lead_id=42,
    updates={
        "company_size": "enterprise",
        "budget_estimate_range": "$500K-$1M",
        "timeline_months": 2,
    },
    auto_regrade=True  # Automatically recalculates grade
)
# Returns updated lead with new grade
```

#### List Leads by Grade
```python
from aicmo.operator_services import list_leads_by_grade

a_leads = list_leads_by_grade(db, campaign_id=1, grade='A')
# Returns: {
#   "total": 10,
#   "grade_filter": "A",
#   "leads": [
#     {"id": 1, "name": "...", "lead_grade": "A", ...},
#     ...
#   ]
# }
```

#### Get Grade Distribution
```python
from aicmo.operator_services import get_lead_grade_distribution

dist = get_lead_grade_distribution(db, campaign_id=1)
# Returns: {"A": 5, "B": 12, "C": 20, "D": 8, "total": 45}
```

## Grading Algorithm

```
1. base_score = lead_score (0.0-1.0)
2. Bonuses:
   - budget_estimate_range? +0.2
   - timeline_months? +0.1
   - pain_points.length > 0? +0.1
3. fit_score = min(1.0, base_score + bonuses)
4. conversion_prob = fit_score * 0.7 + engagement * 0.3

5. Grade Assignment:
   if fit_score >= 0.8 AND budget AND timeline:
     grade = A
   elif fit_score >= 0.8:  # High fit but missing signals
     grade = B
   elif fit_score >= 0.6:
     grade = B
   elif fit_score >= 0.4:
     grade = C
   else:
     grade = D
```

## Database Indexes

Three performance indexes added to LeadDB:
- `idx_lead_grade` — for filtering by grade
- `idx_conversion_probability` — for sorting by quality
- `idx_fit_score_for_service` — for analytics

## Test Execution

```bash
# Run Phase A tests
pytest tests/test_phase_a_lead_grading.py -v

# Run all tests (check for regressions)
pytest tests/ -v --tb=short

# Quick status
pytest tests/test_phase_a_lead_grading.py -q
```

**Expected:** 22 tests passing

## Integration Points

### auto.py — Automatic Grading
- Grading called after message generation
- Graceful degradation if service fails
- Non-blocking

### operator_services.py — CRUD Operations
- `get_lead_detail()` — Detail view
- `update_lead_crm_fields()` — Update with optional auto-regrade
- `list_leads_by_grade()` — Filter by grade
- `get_lead_grade_distribution()` — Metrics

### Domain Models (domain.py)
- New enums: CompanySize, LeadGrade
- Extended Lead class with 25 new fields

### Database Models (db_models.py)
- Extended LeadDB with 45 new columns
- 3 performance indexes

## Next Steps (Phase B)

Phase B will add:
- Email outreach channel
- LinkedIn outreach channel
- Contact form channel
- Multi-channel sequencing
- Estimated: 2-3 days

---

**Phase A Status:** ✅ COMPLETE | 22 tests passing | Ready for Phase B
