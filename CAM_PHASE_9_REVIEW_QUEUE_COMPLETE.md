# CAM Phase 9: Review Queue Engine — Operational Guide

## Overview

Phase 9 adds **human-in-the-loop control** to CAM, enabling operators to review and approve high-value or sensitive actions before they execute.

This prevents accidental mass outreach, ensures quality, and maintains legal/compliance guardrails.

---

## Architecture

### Review Queue Workflow

```
Lead needs attention
         ↓
     Flag for review
         ↓
     Enters Review Queue
         ↓
  Operator sees task
         ↓
Approve/Edit/Reject
         ↓
  Lead proceeds or archived
```

### Key Components

| Component | Purpose |
|-----------|---------|
| **ReviewTask** | Single unit in queue (immutable task definition) |
| **get_review_queue()** | Retrieve all pending review tasks |
| **approve_review_task()** | Operator approves, clears hold |
| **reject_review_task()** | Operator rejects, marks LOST |
| **flag_lead_for_review()** | Backend flags lead for human review |
| **Review Queue API** | REST endpoints for UI/automation |

---

## When to Flag Leads for Review

Auto-flag when ANY of these conditions occur:

### 1. **High-Value Prospects** (PROPOSAL review)
```python
if lead_score > 90 and not has_recent_touchpoint:
    flag_lead_for_review(
        lead.id,
        db_session,
        review_type="PROPOSAL",
        reason="Score 90+, preparing premium pitch"
    )
```

### 2. **Sensitive Industries** (MESSAGE review)
```python
SENSITIVE_INDUSTRIES = ["Government", "Finance", "Healthcare"]

if lead.industry in SENSITIVE_INDUSTRIES and not approved_for_outreach:
    flag_lead_for_review(
        lead.id,
        db_session,
        review_type="MESSAGE",
        reason=f"Sensitive industry: {lead.industry}"
    )
```

### 3. **Custom/Unusual Actions** (ACTION review)
```python
if action not in STANDARD_ACTIONS:
    flag_lead_for_review(
        lead.id,
        db_session,
        review_type="ACTION",
        reason=f"Non-standard action: {action}"
    )
```

### 4. **After X Failed Attempts** (RETRY review)
```python
if lead.failed_attempts > 3 and lead.status != LeadStatus.LOST:
    flag_lead_for_review(
        lead.id,
        db_session,
        review_type="RETRY",
        reason="Multiple failed attempts, assess alternative approach"
    )
```

---

## Operator Workflow

### View Review Queue

```bash
GET /api/v1/review-queue/tasks
```

**Response:**
```json
{
  "total": 12,
  "summary": {
    "MESSAGE": 5,
    "PROPOSAL": 4,
    "ACTION": 3
  },
  "tasks": [
    {
      "lead_id": 42,
      "lead_name": "Jane Acme",
      "lead_company": "Acme Corp",
      "lead_email": "jane@acme.com",
      "review_type": "PROPOSAL",
      "review_reason": "Score 90+, preparing premium pitch",
      "lead_score": 92.5,
      "created_at": "2024-01-15T10:30:00Z"
    },
    ...
  ]
}
```

### Approve a Task (Allow Outreach)

```bash
POST /api/v1/review-queue/tasks/42/approve
Content-Type: application/json

{
  "action": "approve",
  "custom_message": "Approved for outreach. Use attached case study."
}
```

**Result:** Lead `requires_human_review` flag cleared, CAM can proceed.

### Skip a Task (No Follow-up)

```bash
POST /api/v1/review-queue/tasks/42/approve
Content-Type: application/json

{
  "action": "skip"
}
```

**Result:** Lead marked LOST, tagged `operator_skip`.

### Reject a Task (Archive)

```bash
POST /api/v1/review-queue/tasks/42/reject
Content-Type: application/json

{
  "reason": "Not a fit for product. Wrong decision-maker."
}
```

**Result:** Lead marked LOST, tagged `operator_reject`, reason logged.

### Flag Additional Context

```bash
POST /api/v1/review-queue/tasks/42/flag
Content-Type: application/json

{
  "review_type": "PRICING",
  "reason": "Client requested custom pricing model, needs sales approval"
}
```

**Result:** Lead re-flagged with new context, added back to queue.

### View Queue Statistics

```bash
GET /api/v1/review-queue/stats
```

**Response:**
```json
{
  "total_pending": 12,
  "by_type": {
    "MESSAGE": 5,
    "PROPOSAL": 4,
    "ACTION": 3
  },
  "oldest_task_created_at": "2024-01-14T08:15:00Z"
}
```

---

## Integration Points

### 1. **Outreach Engine**
```python
from aicmo.cam.engine.review_queue import get_review_queue

# Before sending message:
if lead.requires_human_review:
    log_info(f"Lead {lead.id} requires review, skipping outreach")
    return  # Don't send until approved
```

### 2. **Proposal Generator**
```python
# Before generating proposal:
from aicmo.cam.engine.review_queue import flag_lead_for_review

if REQUIRES_REVIEW(lead, proposal_config):
    flag_lead_for_review(
        lead.id,
        db_session,
        review_type="PROPOSAL",
        reason="Custom proposal rules triggered"
    )
    return  # Don't generate until approved
```

### 3. **Campaign Controller**
```python
# In main dispatch loop:
from aicmo.cam.engine.review_queue import get_review_queue

def should_process_lead(lead, db_session):
    # Skip if flagged for review
    if lead.requires_human_review:
        return False
    
    # Otherwise, proceed normally
    return True
```

---

## Testing Review Queue

Run test suite:
```bash
pytest tests/test_review_queue.py -v
```

### Key Test Cases

1. **Flag & Retrieve**: Lead flagged, appears in queue
2. **Approve Workflow**: Lead unflagged, CAM proceeds
3. **Reject Workflow**: Lead marked LOST
4. **Campaign Filtering**: Filter queue by campaign
5. **Edge Cases**: Empty queue, nonexistent leads
6. **Note Accumulation**: History preserved

---

## Best Practices

### ✅ DO

- Flag high-value prospects **before** sending premium offers
- Use descriptive `review_reason` (helps operators understand context)
- Review queue daily to prevent backlog
- Archive rejected leads to keep queue clean
- Monitor queue stats to identify patterns

### ❌ DON'T

- Flag leads without clear reason (confuses operators)
- Leave leads in queue indefinitely (breeds stale data)
- Bypass review queue for sensitive actions
- Override queue without logging reason
- Flag the same lead twice for same reason

---

## Monitoring & SLAs

### Queue Health Metrics

```python
def queue_health_check(db_session):
    """Monitor review queue performance."""
    tasks = get_review_queue(db_session)
    
    # SLA targets
    CRITICAL_AGE = 24  # hours
    WARNING_AGE = 12  # hours
    
    critical = []
    warning = []
    
    for task in tasks:
        age_hours = (datetime.utcnow() - task.created_at).total_seconds() / 3600
        
        if age_hours > CRITICAL_AGE:
            critical.append(task)
        elif age_hours > WARNING_AGE:
            warning.append(task)
    
    return {
        "total": len(tasks),
        "critical": len(critical),
        "warning": len(warning),
        "health": "OK" if len(critical) == 0 else "ALERT",
    }
```

**Recommended SLAs:**
- Review tasks within **12 hours** (warning)
- Resolve tasks within **24 hours** (critical)

---

## FAQ

**Q: Can multiple operators review the same lead?**
A: Yes, each operator sees full queue. Only one needs to approve/reject. System handles concurrency via DB locks.

**Q: What happens if operator disapproves but CAM already sent message?**
A: Review flag prevents automatic follow-up. Operator marks as LOST to prevent cascading messages.

**Q: How do I override a review flag?**
A: Use `flag_lead_for_review()` with new reason. Flag always clears previous block.

**Q: Can I batch-approve multiple leads?**
A: Not yet. Single approvals ensure deliberate review. Consider adding bulk actions in Phase 10.

---

## Phase 9 Completion Checklist

- ✅ ReviewTask data structure defined
- ✅ Review queue engine implemented
- ✅ REST API endpoints created
- ✅ Integration tests passing
- ✅ Operator documentation complete
- ✅ Monitoring utilities provided
- ✅ Edge cases handled

**Phase 9 Ready for Deployment** ✓
