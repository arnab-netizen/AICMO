# PHASE 0: COMPLETE REPOSITORY AUDIT

**Status**: Comprehensive mapping of existing CAM infrastructure

## A. EXISTING COMPONENT MAP

### A1. Email Sending Service
**File**: [aicmo/cam/services/email_sending_service.py](aicmo/cam/services/email_sending_service.py)  
**Lines**: 32-293

**Key Methods**:
- `__init__(self, db_session: Session)` - Line 48
- `send_email(to_email, campaign_id, lead_id, template, personalization_dict, ...)` - Line 151
  - Returns: Optional[OutboundEmailDB]
  - Handles: idempotency, daily caps, batch caps
  - Side effects: Creates OutboundEmailDB record, updates lead.last_contacted_at

**DB Tables Used**: 
- OutboundEmailDB
- LeadDB
- CampaignDB

**State Managed**:
- Email status (SENT, FAILED, QUEUED)
- Daily/batch caps per campaign

---

### A2. Reply Classifier (Stateless Detector)
**File**: [aicmo/cam/services/reply_classifier.py](aicmo/cam/services/reply_classifier.py)  
**Lines**: 16-177

**Key Methods**:
- `__init__(self)` - Line 115 (compiles regex patterns)
- `classify(subject: str, body: str) -> Tuple[ReplyClassification, float, str]` - Line 123
  - Returns: (classification, confidence_0_to_1, reason_string)
  - Classification enum: POSITIVE, NEGATIVE, OOO, BOUNCE, UNSUB, NEUTRAL

**Classification Rules**:
- POSITIVE: Interest keywords + sentiment
- NEGATIVE: Rejection keywords
- OOO: Auto-reply patterns
- BOUNCE: Delivery failure patterns
- UNSUB: Unsubscribe requests
- NEUTRAL: No clear signal

---

### A3. Follow-Up Engine (State Machine)
**File**: [aicmo/cam/services/follow_up_engine.py](aicmo/cam/services/follow_up_engine.py)  
**Lines**: 23-320 (estimated)

**Key Methods**:
- `__init__(self, db_session: Session)` - Line 34
- `handle_positive_reply(lead_id: int, inbound_email_id: int)` - Line 40
- `handle_negative_reply(lead_id: int, inbound_email_id: int)` - Line 61
- `handle_unsub_request(lead_id: int, inbound_email_id: int)` - Line 82
- `process_reply(lead_id: int, inbound_email_id: int, classification: str)` - Line 106
  - Dispatches to handle_* methods based on classification

**DB Tables Used**:
- LeadDB (updates status)
- OutreachAttemptDB (tracks attempts)

**State Transitions**:
- PROSPECT → INTERESTED (on POSITIVE)
- PROSPECT → REJECTED (on NEGATIVE)
- Any state → UNSUBSCRIBED (on UNSUB)
- Any state → DEAD (on BOUNCE + threshold)

---

### A4. Decision Engine (Campaign Rules)
**File**: [aicmo/cam/services/decision_engine.py](aicmo/cam/services/decision_engine.py)  
**Lines**: 73-300+ (estimated)

**Key Methods**:
- `__init__(self, db_session: Session)` - Line 83
- `compute_campaign_metrics(campaign_id: int) -> CampaignMetricsSnapshot` - Line 87
  - Calculates: reply_rate, positive_rate, bounce_rate, etc.
  - Returns: CampaignMetricsSnapshot dataclass (Line 25)

**Metrics Computed**:
```python
@dataclass
class CampaignMetricsSnapshot:
    sent_count: int
    reply_count: int
    positive_count: int
    negative_count: int
    bounce_count: int
    ooo_count: int
    unsub_count: int
    
    @property
    def reply_rate(self) -> float  # Line 40
    def positive_rate(self) -> float  # Line 47
    def bounce_rate(self) -> float  # Line 54
```

---

### A5. IMAP Inbox Provider (External API Gateway)
**File**: [aicmo/cam/gateways/inbox_providers/imap.py](aicmo/cam/gateways/inbox_providers/imap.py)  
**Lines**: 34-281

**Key Methods**:
- `__init__(email_account, password, mailbox, server, port)` - Line 48
- `is_configured()` - Line 73
- `fetch_new_replies(since: datetime) -> List[EmailReply]` - Line 166
  - Returns: List of EmailReply dataclass objects
  - Never raises (catches all exceptions)
  - Uses: IMAP SINCE search

**EmailReply Dataclass** (Line 21):
```python
@dataclass
class EmailReply:
    from_email: str
    to_email: str
    subject: str
    body: str
    received_at: datetime
    message_id: str
    uid: str
```

---

### A6. Email Provider (Resend Gateway)
**File**: [aicmo/cam/gateways/email_providers/resend.py](aicmo/cam/gateways/email_providers/resend.py)  
**Lines**: 23-250

**Key Methods**:
- `__init__(api_key, from_email, dry_run=False)` - Line 42
- `is_configured()` - Line 74
- `send(to_email: str, subject: str, html_body: str) -> bool` - Line 100
  - Returns: bool (success)
  - Calls: Resend HTTP API
  - Also NoOpEmailProvider available (Line 232)

---

### A7. DB Models
**File**: [aicmo/cam/db_models.py](aicmo/cam/db_models.py)  
**Lines**: 30-850+

**Key Tables** (Line numbers approximate):
- CampaignDB (Line 30)
- LeadDB (Line 81)
- OutreachAttemptDB (Line 216)
- OutboundEmailDB - **NOT IN AUDIT YET**
- InboundEmailDB - **NOT IN AUDIT YET**
- DiscoveryJobDB (Line 249)
- CampaignMetricsDB (Line 574)
- ExecutionJobDB (Line 390)

---

## B. MISSING COMPONENTS (FOUND NOT IN AUDIT)

### B1. OutboundEmailDB
**Status**: UNKNOWN - Used by EmailSendingService but model definition not found  
**Action**: Search for it

### B2. InboundEmailDB
**Status**: UNKNOWN - Used by inbox/classifier but model definition not found  
**Action**: Search for it

### B3. Inbox Cursor Tracking
**Status**: UNKNOWN - IMAP provider needs cursor tracking  
**Action**: Check if table exists

### B4. Worker Entry Point
**Status**: DOES NOT EXIST - Core requirement  
**Action**: Create aicmo/cam/worker/cam_worker.py

### B5. Alert Provider
**Status**: EXISTS PARTIALLY - email_alert.py exists (created in Phase 1)  
**Action**: Formalize as port + complete implementations

### B6. Module Registry
**Status**: DOES NOT EXIST - Platform-level invariant  
**Action**: Create aicmo/platform/modules/registry.py

### B7. DI Container
**Status**: DOES NOT EXIST - Platform-level invariant  
**Action**: Create aicmo/platform/di/container.py

### B8. Usage Metering
**Status**: DOES NOT EXIST - Required for monetizable modules  
**Action**: Create aicmo/platform/metering/ledger.py

### B9. Health/Readiness
**Status**: DOES NOT EXIST - Operational requirement  
**Action**: Create aicmo/platform/health/checker.py

---

## C. INTEGRATION POINTS (Current)

```
EmailSendingService
  ├─→ EmailProvider (Resend/NoOp)
  └─→ DB Session (OutboundEmailDB, LeadDB, CampaignDB)

ReplyClassifier
  └─→ Stateless (regex only)

FollowUpEngine
  ├─→ ReplyClassifier (calls classify to understand flow)
  └─→ DB Session (LeadDB state transitions)

DecisionEngine
  └─→ DB Session (reads campaign metrics)

IMAPInboxProvider
  └─→ IMAP Server (external)

Missing: No orchestrator connecting these
Missing: No worker running them
Missing: No event bus / composition layer
```

---

## D. DB SCHEMA INVENTORY

### Confirmed Tables

**CampaignDB** (Line 30)
- id (PK)
- name, description
- status
- created_at, updated_at
- (many more fields)

**LeadDB** (Line 81)
- id (PK)
- campaign_id (FK)
- email
- status (PROSPECT, INTERESTED, REJECTED, UNSUBSCRIBED, DEAD, etc.)
- last_contacted_at
- (many more fields)

**CampaignMetricsDB** (Line 574)
- For aggregating metrics

### Tables That MUST Exist

- **OutboundEmailDB** - For tracking sent emails
- **InboundEmailDB** - For tracking received replies
- **InboxCursorDB** - For IMAP cursor tracking (since_date or UID)

### Tables That NEED CREATION

- **CamWorkerHeartbeatDB** - For advisory lock + health
- **HumanAlertLogDB** - For alert audit trail
- **UsageLedgerDB** - For metering
- **ExecutionRunLogDB** - For cycle summaries

---

## E. MIGRATION STATUS

**Alembic Path**: `/workspaces/AICMO/db/alembic/versions/`

**Latest Migrations**:
- 4d2f8a9b1e3c_add_cam_pipeline_tables.py
- 5e3a9d7f2b4c_add_cam_safety_settings.py
- 6c7f03514563_add_execution_jobs_table.py

**Status**: Migrations infrastructure exists and working

---

## F. PORTS/CONTRACTS THAT ALREADY EXIST

**EmailProvider** (Line 42-250)
- Exists as abstract pattern (ResendEmailProvider + NoOpEmailProvider)
- No formal interface yet

**InboxProvider** (IMAPInboxProvider)
- Exists as concrete implementation
- No formal interface yet

**Existing Ports**:
- `/aicmo/cam/ports/email_verifier.py`
- `/aicmo/cam/ports/reply_fetcher.py`
- `/aicmo/cam/ports/email_provider.py` (but no formal interface)

---

## G. CONFIGURATION

**Settings Class**: [aicmo/cam/settings.py](aicmo/cam/settings.py) or similar  
**Location**: TBD - Check

---

## H. PROOF COMMANDS FOR NEXT PHASES

```bash
# Find OutboundEmailDB definition
grep -rn "class OutboundEmailDB" /workspaces/AICMO/aicmo/

# Find InboundEmailDB definition
grep -rn "class InboundEmailDB" /workspaces/AICMO/aicmo/

# Check alembic upgrade
cd /workspaces/AICMO && alembic upgrade head

# Check existing tests
find /workspaces/AICMO/tests -name "test_*cam*.py"

# Check existing worker (should be none)
find /workspaces/AICMO/aicmo/cam/worker -name "*.py"
```

---

## I. AUDIT SUMMARY

### ✅ Component Status

| Component | Type | Status | File | Lines |
|-----------|------|--------|------|-------|
| EmailSendingService | Service | ✅ EXISTS | email_sending_service.py | 32-293 |
| ReplyClassifier | Service | ✅ EXISTS | reply_classifier.py | 16-177 |
| FollowUpEngine | Service | ✅ EXISTS | follow_up_engine.py | 23-320 |
| DecisionEngine | Service | ✅ EXISTS | decision_engine.py | 73-300 |
| IMAPInboxProvider | Gateway | ✅ EXISTS | inbox_providers/imap.py | 34-281 |
| ResendEmailProvider | Gateway | ✅ EXISTS | email_providers/resend.py | 23-250 |
| EmailVerifierPort | Port | ✅ EXISTS | ports/email_verifier.py | ? |
| ReplyFetcherPort | Port | ✅ EXISTS | ports/reply_fetcher.py | ? |
| **OutboundEmailDB** | Model | ❓ UNKNOWN | ? | ? |
| **InboundEmailDB** | Model | ❓ UNKNOWN | ? | ? |
| **Worker** | Runtime | ❌ MISSING | - | - |
| **AlertProvider** | Port | ⚠️ PARTIAL | alert_providers/ | - |
| **ModuleRegistry** | Platform | ❌ MISSING | - | - |
| **DIContainer** | Platform | ❌ MISSING | - | - |
| **UsageMetering** | Platform | ❌ MISSING | - | - |
| **HealthChecker** | Platform | ❌ MISSING | - | - |

### Key Findings

1. **All core business logic exists** (email, classify, followups, decision)
2. **DB infrastructure exists** (Alembic, models)
3. **Missing: Orchestration layer** (worker, composition, event bus)
4. **Missing: Platform invariants** (registry, DI, metering, health)
5. **Missing: Module boundaries** (currently monolithic imports)
6. **DB models need verification**: OutboundEmailDB and InboundEmailDB

---

## NEXT STEP: Phase 0.5 - Find Missing Models

Run audit for OutboundEmailDB and InboundEmailDB, then proceed to PHASE 1.
