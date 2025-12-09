# CAM Phase 9 Integration Guide

## How Review Queue Fits Into the CAM Architecture

### Phase Overview

```
Phase 0-3: Foundations (DB, Models, Auth)
      ↓
Phase 4-5: Core Outreach (Engine, Scoring, Messaging)
      ↓
Phase 6-7: Automation (API, Workflows)
      ↓
Phase 8: Quality Gates
      ↓
Phase 9: HUMAN-IN-THE-LOOP CONTROL ← YOU ARE HERE
      ↓
Phase 10+: Advanced features (Bulk actions, ML-assisted, Escalation)
```

---

## Integration Points with Existing Phases

### ✅ Phase 4-5: Outreach Engine Integration

**Location:** Before sending any outreach message

```python
# File: aicmo/cam/engine/outreach.py (or similar)

from aicmo.cam.engine.review_queue import get_review_queue

def send_campaign_outreach(campaign_id, batch_size=50):
    """Send outreach messages to leads in campaign."""
    
    leads = get_campaign_leads(campaign_id)
    
    for lead in leads:
        # PHASE 9 INTEGRATION: Check review flag
        if lead.requires_human_review:
            logger.info(f"Lead {lead.id} in review queue, skipping")
            continue  # ← BLOCK outreach if review pending
        
        # Existing Phase 4-5 logic
        message = generate_outreach_message(lead)
        send_message(lead.email, message)
```

**Impact:** Prevents automated outreach to flagged leads until operator approves.

---

### ✅ Phase 5: Scoring System Integration

**Location:** In lead scoring logic

```python
# File: aicmo/cam/scoring/scorer.py (or similar)

from aicmo.cam.engine.review_queue import flag_lead_for_review

def score_lead(lead, db_session):
    """Score lead and flag if score is exceptional."""
    
    score = calculate_base_score(lead)  # Phase 5 existing
    
    # PHASE 9 INTEGRATION: Auto-flag high-score prospects
    if score > 90 and not has_recent_activity(lead):
        flag_lead_for_review(
            lead.id,
            db_session,
            review_type="PROPOSAL",
            reason=f"High-value prospect (score={score})"
        )
        logger.info(f"Flagged lead {lead.id} - score {score}")
    
    return score
```

**Impact:** High-value prospects automatically enter review queue for premium treatment.

---

### ✅ Phase 6-7: API Integration

**Location:** New API endpoints (no changes to existing ones)

```python
# File: aicmo/cam/api/app.py

from aicmo.cam.api.review_queue import bp as review_queue_bp

def create_app():
    """Create Flask app with all blueprints."""
    app = Flask(__name__)
    
    # Existing Phase 6-7 blueprints
    app.register_blueprint(lead_bp)
    app.register_blueprint(campaign_bp)
    app.register_blueprint(message_bp)
    
    # PHASE 9 INTEGRATION: New review queue blueprint
    app.register_blueprint(review_queue_bp)  # ← ADD THIS
    
    return app
```

**API Routes Added:**
- `GET /api/v1/review-queue/tasks`
- `POST /api/v1/review-queue/tasks/<id>/approve`
- `POST /api/v1/review-queue/tasks/<id>/reject`
- `POST /api/v1/review-queue/tasks/<id>/flag`
- `GET /api/v1/review-queue/stats`

---

### ✅ Phase 8: Quality Gates Integration

**Location:** In quality gate validation

```python
# File: aicmo/cam/quality/gates.py (or similar)

from aicmo.cam.engine.review_queue import flag_lead_for_review

class QualityGate:
    """Phase 8: Quality enforcement."""
    
    def validate_outreach(self, lead, message, db_session):
        """Validate message before sending."""
        
        issues = []
        
        # Existing Phase 8 checks
        if not self.check_grammar(message):
            issues.append("Grammar errors detected")
        
        if not self.check_tone(message):
            issues.append("Tone not professional")
        
        # PHASE 9 INTEGRATION: Flag if quality issues found
        if len(issues) > 0 and self.SEVERITY[issues[0]] == "HIGH":
            flag_lead_for_review(
                lead.id,
                db_session,
                review_type="MESSAGE",
                reason=f"Quality gate failed: {issues[0]}"
            )
            return False  # Block outreach
        
        return True
```

**Impact:** Quality gate failures automatically flag lead for operator review.

---

## Workflow: End-to-End Example

### Scenario: High-Value B2B Lead

```
1. DISCOVERY (Phase 0-3)
   └─ Lead Jane@AcmeCorp added to campaign

2. SCORING (Phase 5)
   └─ Score calculated: 92/100
   ├─ PHASE 9: Auto-flag for "PROPOSAL" review
   │  (reason: "High-value prospect, score 92")
   └─ Lead enters review queue

3. HUMAN REVIEW
   ├─ Operator sees task in dashboard
   ├─ Views context: Jane, Acme Corp, score 92
   ├─ Decides: "Approve for premium pitch"
   └─ Clicks: Approve button

4. OUTREACH ENGINE (Phase 4-5)
   ├─ Checks: lead.requires_human_review? → False
   ├─ Proceeds: Generate custom proposal
   ├─ Sends: Premium offer email
   └─ Updates: Lead status → INTERESTED

5. FUTURE PHASES (10+)
   ├─ Bulk approval workflows
   ├─ ML-assisted decisions
   └─ Escalation chains
```

---

## Database Schema: No Breaking Changes

### Added to LeadDB (Phase 0-3 model)

```python
class LeadDB(Base):
    # ... existing Phase 0-3 fields ...
    
    # PHASE 9 ADDITIONS (all optional/nullable):
    requires_human_review = Column(Boolean, default=False)  # Flag state
    review_type = Column(String(50), nullable=True)          # MESSAGE, PROPOSAL, etc.
    review_reason = Column(String(500), nullable=True)       # Why flagged
    
    # Existing fields still intact - full backward compatibility
```

**Migration Path:**
- New deployments: Fields auto-created
- Existing databases: Fields optional, default to NULL/False
- No data migration needed

---

## Testing Integration: Verification Steps

### Unit Test Integration
```bash
# Run Phase 9 tests in isolation
pytest tests/test_review_queue.py -v

# Run all CAM tests to verify no regressions
pytest tests/test_outreach.py tests/test_scoring.py tests/test_review_queue.py -v
```

### Integration Test Example
```python
def test_full_workflow():
    """Test: Lead → Score → Flag → Review → Approve → Outreach"""
    
    # 1. Create lead (Phase 0-3)
    lead = LeadDB(name="Jane", company="Acme", email="jane@acme.com")
    db_session.add(lead)
    db_session.commit()
    
    # 2. Score lead (Phase 5)
    score = score_lead(lead, db_session)  # → 92
    
    # 3. Verify flagged (Phase 9)
    refreshed = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
    assert refreshed.requires_human_review == True
    
    # 4. Operator approves (Phase 9)
    approve_review_task(lead.id, db_session, action="approve")
    
    # 5. Refresh and verify unflagged
    refreshed = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
    assert refreshed.requires_human_review == False
    
    # 6. Outreach proceeds (Phase 4-5)
    assert not lead.requires_human_review  # Can proceed
    send_outreach(lead)  # Works as normal
```

---

## Configuration: Environment Variables (Optional)

```bash
# Optional Phase 9 settings
CAM_REVIEW_QUEUE_AUTO_FLAG_SCORE=90      # Auto-flag at this score
CAM_REVIEW_QUEUE_MAX_QUEUE_SIZE=100      # Alert if queue > size
CAM_REVIEW_QUEUE_SLA_HOURS=24            # SLA threshold
CAM_REVIEW_QUEUE_ENABLED=true            # Can disable globally
```

---

## Monitoring: Metrics to Track

### Per-Phase Metrics

| Phase | Metric | Target |
|-------|--------|--------|
| **Phase 5** | Leads scoring > 90 | 2-5% of total |
| **Phase 9** | Leads in review queue | < 50 pending |
| **Phase 9** | Queue SLA compliance | > 95% (< 24h) |
| **Phase 4-5** | Outreach skipped due to review | 2-5% |

### Alert Conditions

```python
# Alert if queue health degrades
if queue_stats["total_pending"] > 100:
    alert("CRITICAL: Review queue overflow")

if queue_stats["oldest_task_age_hours"] > 48:
    alert("CRITICAL: SLA violation - stale tasks")

if approval_rate < 0.6:  # < 60%
    alert("WARNING: Low approval rate - possible process issue")
```

---

## Rollback Strategy: If Needed

**Scenario:** Phase 9 causes unexpected issues

**Steps:**
1. Revert API routes (disable blueprint)
2. Set all leads: `requires_human_review = False` (SQL)
3. Revert outreach engine integration check
4. Monitor error logs

```sql
-- Emergency reset: Clear all review flags
UPDATE leads SET requires_human_review = FALSE, review_type = NULL;
```

**Rollback Time:** < 5 minutes

---

## Phase 9 → Phase 10 Roadmap

### Phase 10: Advanced Features
```
├─ Bulk Actions (approve/reject 10+ at once)
├─ Review Templates (pre-configured rules)
├─ Notifications (alert ops when tasks enter queue)
└─ Reassignment (route to specific team members)
```

### Phase 11: ML Integration
```
├─ Decision Suggestions (AI recommends approve/reject)
├─ Pattern Learning (learns from operator decisions)
└─ Auto-approve (AI approves low-risk tasks)
```

---

## Success Criteria: Phase 9 Integration

✅ **Functional**
- Review queue appears in operator dashboard
- API endpoints respond correctly
- Database stores review flags

✅ **Operational**
- Operators can approve/reject tasks
- Outreach engine respects review flags
- No leads outreached while in review

✅ **Performance**
- Queue retrieval < 100ms for typical workloads
- Flagging/unflagging < 50ms
- No impact on existing outreach throughput

✅ **Compliance**
- All review actions logged in lead notes
- Audit trail preserved for compliance
- No data loss on phase upgrade

---

## File Dependencies

```
Phase 9 Files:
├─ aicmo/cam/engine/review_queue.py        (Core logic)
├─ aicmo/cam/api/review_queue.py           (REST API)
├─ tests/test_review_queue.py              (Tests)
└─ Documentation files

Depends On:
├─ aicmo/cam/db_models.py                  (LeadDB, CampaignDB)
├─ aicmo/cam/domain.py                     (LeadStatus enum)
└─ Flask, SQLAlchemy, pytest               (Standard libs)

Integrates With:
├─ aicmo/cam/engine/outreach.py            (Phase 4-5)
├─ aicmo/cam/scoring/scorer.py             (Phase 5)
├─ aicmo/cam/quality/gates.py              (Phase 8)
└─ aicmo/cam/api/app.py                    (Phase 6-7)
```

---

**Phase 9 Integration Complete** ✅

Next: Deploy, test with operators, gather feedback for Phase 10
