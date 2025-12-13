# Phase 3: Lead Scoring Engine — Quick Reference

**Status**: ✅ COMPLETE | **Tests**: 44/44 passing | **Code**: 592 lines

## What It Does

Scores leads on two dimensions and classifies them into tiers:

```
Lead → ICP Fit Score (0.0-1.0)     [Company match]
     → Opportunity Score (0.0-1.0) [Engagement likelihood]
     → Combined Score → Tier Classification
                        ├─ HOT (≥0.85)
                        ├─ WARM (0.65-0.84)
                        ├─ COOL (0.40-0.64)
                        └─ COLD (<0.40)
```

## Key Classes

### ICPScorer
Evaluates company fit (size, industry, revenue, location)
```python
scorer = ICPScorer(size_weight=0.30, industry_weight=0.30, ...)
score = scorer.compute_icp_fit(lead, campaign)  # → 0.0-1.0
```

### OpportunityScorer
Evaluates engagement likelihood (title, seniority, buying signals)
```python
scorer = OpportunityScorer()
score = scorer.compute_opportunity_score(lead, campaign)  # → 0.0-1.0
```

### TierClassifier
Combines scores and assigns tier
```python
classifier = TierClassifier(icp_weight=0.50, opportunity_weight=0.50)
tier = classifier.classify_lead_tier(0.90, 0.85)  # → LeadTier.HOT
```

### batch_score_leads()
Score all unscored leads in a campaign
```python
metrics = batch_score_leads(db, campaign_id=1, max_leads=500)
print(f"HOT: {metrics.hot_count}, avg score: {metrics.avg_combined_score:.2f}")
```

## Usage Pattern

```python
from aicmo.cam.engine import (
    batch_score_leads,
    ICPScorer,
    OpportunityScorer,
    TierClassifier,
)

# Batch score all enriched leads
metrics = batch_score_leads(db, campaign_id=my_campaign.id)

# Check results
print(f"Scored: {metrics.scored_count}")
print(f"HOT leads (ready): {metrics.hot_count}")
print(f"Execution time: {metrics.duration_seconds:.2f}s")
```

## Scoring Breakdown

**ICP Fit** (company-level):
- Company size match (exact/adjacent/far)
- Industry alignment (exact/partial/none)
- Revenue in range
- Geographic fit

**Opportunity** (person-level):
- Job title relevance
- Seniority (C-level, VP, Director, Manager, IC)
- Buying signals:
  - Recent job change
  - Company hiring
  - Company funded
  - Budget authority
  - Decision-maker status
  - Recent activity

**Combined** → Tier assignment

## Output

Leads are updated with:
- `lead.lead_score` (0.0-1.0)
- `lead.tags` (["HOT"], ["WARM"], ["COOL"], or ["COLD"])

## Test Coverage

44 tests covering:
- ✅ ICP scoring edge cases
- ✅ Opportunity signal detection
- ✅ Tier boundaries and transitions
- ✅ Batch processing with database updates
- ✅ Error handling and recovery
- ✅ Metrics accuracy

## Files

- `aicmo/cam/engine/lead_scorer.py` (592 lines)
- `tests/test_phase3_lead_scoring.py` (643 lines)
- `PHASE_3_LEAD_SCORING_COMPLETE.md` (529 lines)

## Integration

Works with Phase 2 Harvester:
```
Harvest enriched leads → batch_score_leads → Scored leads ready for Phase 4
```

## Next Phase

Phase 4 will add qualification rules to filter and route scored leads.
