# Phase 5: Quick Reference — Lead Routing

## Setup

```python
from aicmo.cam.engine import LeadRouter, RoutingRules, ContentSequenceType

# Create rules
rules = RoutingRules(hot_tier_min_score=0.85)

# Create router
router = LeadRouter(rules)
```

## Tier Assignment

| Score | Tier | Sequence | Duration | Emails | Goal |
|-------|------|----------|----------|--------|------|
| ≥0.85 | HOT | AGGRESSIVE_CLOSE | 7 days | 3 | Schedule demo |
| ≥0.70 | WARM | REGULAR_NURTURE | 14 days | 4 | Qualify need |
| ≥0.50 | COOL | LONG_TERM_NURTURE | 30 days | 6 | Build relationship |
| <0.50 | COLD | COLD_OUTREACH | 60 days | 8 | Educate |

## Single Lead Routing

```python
# Route one lead
decision = router.route_single_lead(lead)

# Check status
if decision.status == RoutingStatus.ROUTED:
    print(f"Assigned: {decision.sequence_type.value}")
    if decision.boosted_by_intent:
        print("Boosted by intent signals!")
```

## Batch Routing

```python
# Route all qualified leads in campaign
metrics = router.batch_route_leads(
    db=session,
    campaign_id=123,
    max_leads=1000
)

print(metrics.to_dict())
# {
#     'processed_count': 100,
#     'routed_count': 95,
#     'hot_count': 15,
#     'warm_count': 35,
#     'cool_count': 30,
#     'cold_count': 15,
#     ...
# }
```

## Intent Boost

High-intent leads (2+ signals) get +0.15 score boost:

```python
lead = Lead(
    lead_score=0.72,  # WARM threshold
    enrichment_data={
        "recent_job_change": True,
        "company_hiring": True  # 2+ signals = boost to HOT
    }
)

decision = router.route_single_lead(lead)
# decision.sequence_type == ContentSequenceType.AGGRESSIVE_CLOSE
# decision.boosted_by_intent == True
```

## Custom Configuration

```python
rules = RoutingRules(
    hot_tier_min_score=0.90,      # Stricter HOT
    intent_boost_enabled=False,    # Disable boost
    enable_auto_routing=True       # Enable batch routing
)
```

## Statuses

- **ROUTED**: Lead assigned to sequence
- **ALREADY_ROUTED**: Lead already in sequence
- **QUALIFICATION_PENDING**: Not yet qualified
- **REJECTED_LEAD**: Failed qualification (LOST status)

## Database Impact

| Field | Before | After |
|-------|--------|-------|
| `status` | QUALIFIED | ROUTED |
| `routing_sequence` | NULL | "aggressive_close" |
| `sequence_start_at` | NULL | datetime |

## Performance

- Single lead: ~1ms
- Batch (100): ~100ms  
- Batch (1000): ~1.0s

## Testing

```bash
pytest tests/test_phase5_lead_routing.py -v
```

## Pipeline

Harvest → Score → Qualify → **Route** → Nurture

