# CAM Phase 9: Review Queue — Quick Reference

## One-Page Developer Guide

### Installation
```bash
# No additional dependencies required
# Uses existing: Flask, SQLAlchemy, pytest
```

### Core API Usage

**In Python code:**
```python
from aicmo.cam.engine.review_queue import (
    get_review_queue,
    flag_lead_for_review,
    approve_review_task,
)

# Flag a lead for review
flag_lead_for_review(
    lead_id=42,
    db_session=session,
    review_type="PROPOSAL",
    reason="Score 90+, custom offer needed"
)

# Get queue
queue = get_review_queue(db_session, campaign_id=5)
for task in queue:
    print(f"{task.lead_name}: {task.review_reason}")

# Approve after operator review
approve_review_task(42, db_session, action="approve")
```

### REST API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/review-queue/tasks` | GET | List queue |
| `/api/v1/review-queue/tasks?campaign_id=5` | GET | Filter by campaign |
| `/api/v1/review-queue/tasks?review_type=PROPOSAL` | GET | Filter by type |
| `/api/v1/review-queue/tasks/<id>/approve` | POST | Approve task |
| `/api/v1/review-queue/tasks/<id>/reject` | POST | Reject task |
| `/api/v1/review-queue/tasks/<id>/flag` | POST | Re-flag |
| `/api/v1/review-queue/stats` | GET | Queue stats |

### When to Flag

```python
# High-value prospect
if lead_score > 90:
    flag_lead_for_review(lead_id, session, "PROPOSAL", "Premium prospect")

# Sensitive industry
if lead.industry in ["Government", "Finance", "Healthcare"]:
    flag_lead_for_review(lead_id, session, "MESSAGE", "Regulated industry")

# Custom action
if action not in STANDARD_ACTIONS:
    flag_lead_for_review(lead_id, session, "ACTION", f"Non-standard: {action}")

# Before processing
if lead.requires_human_review:
    return  # Skip, wait for operator approval
```

### Integration Checklist

```python
# 1. In Outreach Engine
if lead.requires_human_review:
    logger.info(f"Lead {lead.id} under review, skipping outreach")
    return

# 2. In Proposal Generator
from aicmo.cam.engine.review_queue import flag_lead_for_review

if requires_custom_proposal(lead):
    flag_lead_for_review(lead.id, session, "PROPOSAL", "Custom terms needed")
    return

# 3. In Campaign Controller
from aicmo.cam.engine.review_queue import get_review_queue

def should_process(lead, session):
    if lead.requires_human_review:
        return False  # Skip
    return True
```

### Testing

```bash
# Run all tests
pytest tests/test_review_queue.py -v

# Run specific test
pytest tests/test_review_queue.py::TestReviewQueue::test_flag_lead_for_review -v

# Run with coverage
pytest tests/test_review_queue.py --cov=aicmo.cam.engine.review_queue
```

### Common Tasks

**Manually flag a lead:**
```python
from aicmo.cam.engine.review_queue import flag_lead_for_review

flag_lead_for_review(
    lead_id=123,
    db_session=db_session,
    review_type="MESSAGE",
    reason="Customer requested custom intro"
)
```

**Get queue for dashboard:**
```python
@app.route("/dashboard/review-queue")
def dashboard():
    tasks = get_review_queue(db_session)
    return jsonify([t.to_dict() for t in tasks])
```

**Process operator action:**
```python
@app.route("/api/review-queue/action", methods=["POST"])
def process_review_action():
    data = request.json
    lead_id = data["lead_id"]
    action = data["action"]  # "approve", "skip", "reject"
    
    if action == "approve":
        approve_review_task(lead_id, db_session, action="approve")
    elif action == "skip":
        approve_review_task(lead_id, db_session, action="skip")
    elif action == "reject":
        reject_review_task(lead_id, db_session, reason=data.get("reason"))
    
    return {"status": "ok"}
```

### Monitoring SLA

```python
from datetime import datetime

tasks = get_review_queue(db_session)
now = datetime.utcnow()

stale = [t for t in tasks if (now - t.created_at).total_seconds() > 86400]
if stale:
    logger.warning(f"Queue SLA violation: {len(stale)} tasks > 24h old")
    # Send alert to ops team
```

### Review Types Reference

| Type | When | Example |
|------|------|---------|
| MESSAGE | Sensitive outreach | Government leads |
| PROPOSAL | High-value custom offers | Score > 90 |
| PRICING | Complex deal structures | Negotiation needed |
| ACTION | Non-standard workflows | Custom behavior |
| RETRY | Multiple failures | 4+ attempts failed |

### Database Schema

Added to `LeadDB`:
```python
requires_human_review: bool = False    # Flag state
review_type: str = None                # MESSAGE, PROPOSAL, etc.
review_reason: str = None              # Why flagged
```

### Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | OK |
| 404 | Lead not found | Verify lead_id |
| 500 | Database error | Check logs |

All functions return `False` on failure (no exceptions thrown).

### Debugging

```python
# Check if lead is in review
lead = db_session.query(LeadDB).filter(LeadDB.id == 42).first()
print(f"In review: {lead.requires_human_review}")
print(f"Type: {lead.review_type}")
print(f"Reason: {lead.review_reason}")
print(f"Notes: {lead.notes}")

# Get full queue with details
queue = get_review_queue(db_session)
for task in queue:
    print(f"{task.lead_id}: {task.review_type} - {task.review_reason}")
```

### Key Files

| File | Purpose |
|------|---------|
| `aicmo/cam/engine/review_queue.py` | Core logic (289 lines) |
| `aicmo/cam/api/review_queue.py` | REST routes (197 lines) |
| `tests/test_review_queue.py` | Test suite (14 tests) |
| `CAM_PHASE_9_REVIEW_QUEUE_COMPLETE.md` | Full docs |

---

**Phase 9 Ready** ✅
