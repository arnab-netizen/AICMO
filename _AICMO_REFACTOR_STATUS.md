# AICMO Modularization Refactor Status

## 🎯 PHASE 1 COMPLETION SUMMARY

### ✅ Phase 1 Completed Successfully

**Start Date**: December 13, 2025 (with Q1-Q4 answers)  
**Duration**: ~2 hours  
**Status**: 100% Complete - Ready for Phase 2

#### What Phase 1 Delivered

1. **Module Skeletons**: 14 modules with api/ + internal/ layout
   - ✅ 10 business modules: onboarding, strategy, production, qc, client_review, delivery, reporting, billing, retention, (cam)
   - ✅ 4 crosscutting modules: orchestration, identity, observability, learning

2. **Contract Skeleton Files**: 39 files created
   - ✅ api/ports.py (13 modules)
   - ✅ api/dtos.py (13 modules)
   - ✅ api/events.py (13 modules)

3. **Deterministic Test Harness**: aicmo/shared/testing.py
   - ✅ Fixed clock fixture (freezegun)
   - ✅ In-memory SQLite DB fixture
   - ✅ Fake provider registry
   - ✅ 6 tests PASSED (100%): smoke test + 5 fixture tests

#### Test Output
```
tests/test_harness_fixtures.py::test_fixed_clock_fixture PASSED        [ 20%]
tests/test_harness_fixtures.py::test_in_memory_db_fixture PASSED       [ 40%]
tests/test_harness_fixtures.py::test_db_session_fixture PASSED         [ 60%]
tests/test_harness_fixtures.py::test_fake_providers_fixture PASSED     [ 80%]
tests/test_harness_fixtures.py::test_all_fixtures_together PASSED      [100%]

aicmo/shared/testing.py::test_harness_smoke PASSED

===== 6 passed in 0.31s =====
```

---

## Current Phase: ✅ PHASE 2 — Contracts Implementation (COMPLETE)

**Status**: All contracts implemented, all tests passing (71/71).  
**Date**: December 13, 2025 (ongoing)  
**Repo**: arnab-netizen/AICMO (main)  
**Codebase**: ~23,760 lines of Python in aicmo/ directory (+ Phase 2 contracts)

**Phase 2 Completion**:
- ✅ CONTRACT_VERSION standardized across 14 modules
- ✅ Ports (abstract interfaces) implemented for all 14 modules
- ✅ DTOs (data contracts) implemented for all 14 modules
- ✅ Events (domain events) implemented for all 14 modules
- ✅ Contract tests pass: 71/71 (100%)
- ✅ Import guard enforced: no internal/domain imports in API layer
- ✅ Test harness verified non-false-green (25 real tables, 3 realism tests)

**Blocking Answers Applied**:

- Q1: backend/ code → B (wrap in ACLs) — scheduled Phase 3
- Q2: aicmo/domain → A (delete entirely; move to aicmo/shared) — scheduled Phase 2.5
- Q3: table ownership → C (phase migration separately) — scheduled Phase 3
- Q4: orchestration → B (create aicmo/orchestration module) — ✅ DONE (Phase 2)

---

## PHASE 0 FINDINGS

### 1. Current Module Structure vs Target

#### Current State:
```
aicmo/
├── acquisition/          (???)
├── agency/               (???)
├── analysis/             (???)
├── analytics/            ← EXISTS but not in target map
├── brand/                (???)
├── cam/                  ✅ TARGET (exists, partially modularized)
├── core/                 (crosscutting infrastructure)
├── creative/             (???)
├── creatives/            ← EXISTS but not in target map
├── crm/                  (???)
├── delivery/             ✅ TARGET (exists, scattered)
├── domain/               ⚠️ GOD MODULE (imported by 29 files)
├── gateways/             (cross-module utilities)
├── generators/           (???)
├── io/                   (???)
├── learning/             ✅ TARGET (exists, minimal)
├── llm/                  (???)
├── media/                (???)
├── memory/               (???)
├── monitoring/           (???)
├── operator/             (???)
├── operator_services.py  (???)
├── pitch/                (???)
├── platform/             ✅ CROSSCUTTING (exists)
├── pm/                   (???)
├── portal/               (???)
├── presets/              (???)
├── publishing/           (???)
├── quality/              (???)
├── renderers/            (???)
├── self_test/            (???)
├── social/               (???)
├── strategy/             ✅ TARGET (exists, scattered)
├── ui/                   (???)
└── utils/                (minimal: just json_safe.py)
```

#### Target Required Modules:
**Business Modules**:
- ✅ cam → Client Acquisition (EXISTS, partially modularized)
- ❌ onboarding → Client Intake & Onboarding (MISSING)
- ❌ strategy → Strategy & Planning (SCATTERED across aicmo/strategy/, backend/)
- ❌ production → Production & Creative (UNCLEAR - split between creatives/, creative/)
- ❌ qc → Quality Control & Review (UNCLEAR - might be aicmo/quality/)
- ❌ client_review → Client Review & Revision (MISSING)
- ✅ delivery → Delivery & Execution (EXISTS, scattered)
- ❌ reporting → Reporting & Performance (UNCLEAR - aicmo/analytics/)
- ❌ billing → Billing, Finance & Commercials (MISSING)
- ❌ retention → Retention, Growth & Lifecycle (MISSING)

**Crosscutting Modules**:
- 🟡 orchestration → Control plane (PARTIAL: aicmo/platform/orchestration.py exists)
- 🟡 learning → Intelligence / Memory plane (PARTIAL: aicmo/learning/ exists)
- ❌ identity → AuthN / AuthZ boundary (MISSING)
- ❌ observability → Logs / metrics / tracing (MISSING - aicmo/monitoring/, aicmo/logging.py)

---

### 2. Import Violations (CRITICAL)

#### God Module: `aicmo.domain`
**Imported by 29 files across the codebase**:
```python
from aicmo.domain.intake import ClientIntake
from aicmo.domain.project import Project
from aicmo.domain.strategy import StrategyDoc
from aicmo.domain.creative import Creative
from aicmo.domain.execution import Execution
```

**Files importing from aicmo.domain:**
- aicmo/cam/*, aicmo/delivery/*, aicmo/creatives/*, aicmo/operator_services.py, etc.

**Problem**: Domain models are shared across modules without proper contracts. This violates:
- ✗ "Modules exchange only DTOs/Events"
- ✗ "DTOs designed for use case, not database"
- ✗ "No cross-module internal imports"

#### Cross-Module DB Writes (HIGH SEVERITY)
**Non-CAM modules writing to CAM tables**:
```
aicmo/delivery/execution_orchestrator.py → writes to CampaignDB
aicmo/delivery/output_packager.py         → writes to CampaignDB, LeadDB
aicmo/domain/project.py                   → writes to CampaignDB
aicmo/operator_services.py                → writes to CampaignDB, LeadDB
aicmo/creatives/service.py                → writes via session.add()
```

**Problem**: Violates:
- ✗ "Each module owns its persistence"
- ✗ "No cross-module table writes"
- ✗ "No shared ORM session across modules"

#### CAM Module DB Model Imports
**37 files in aicmo/cam/ import db_models directly**:
```python
from aicmo.cam.db_models import CampaignDB, LeadDB, AttemptDB
```

**Within CAM** (internal), this is acceptable.  
**Outside CAM** (4 violations found above), this is forbidden.

---

### 3. Data Ownership Conflicts (CRITICAL)

#### CAM Module (aicmo/cam/db_models.py)
- **Tables**: cam_campaigns, cam_leads, cam_attempts, cam_discovery_jobs, cam_discovered_profiles, cam_outbound_emails, cam_inbound_emails, cam_worker_heartbeats, cam_human_alert_logs
- **Current Writers**:
  - ✅ aicmo/cam/* (internal, allowed)
  - ❌ aicmo/delivery/* (VIOLATION)
  - ❌ aicmo/domain/* (VIOLATION)
  - ❌ aicmo/operator_services.py (VIOLATION)

#### Delivery Module
- **Issue**: Reads from & writes to CAM tables
- **Example**: `aicmo/delivery/execution_orchestrator.py` calls `session.add(campaign)`
- **Problem**: Should use logical FK + contract-based communication

#### Shared DB Session Issue
- **Current**: `aicmo/core/db.py` provides global `SessionLocal()` factory
- **Problem**: Same session used across modules → tight coupling
- **Required Fix**: Each module gets its own session; composition orchestrates transactions

---

### 4. Database Migrations & Schema History

#### Alembic Setup
- **Primary**: `/workspaces/AICMO/db/alembic/` (18 migration files)
- **Legacy**: `/workspaces/AICMO/backend/alembic/` (not reviewed)

#### Recent Migrations (Last 5)
```
7d9e4a2b1c3f_add_cam_modular_tables.py           (Dec 12) - CAM modular tables
5f6a8c9d0e1f_add_missing_cam_lead_columns.py     (Dec 9)  - CAM lead fields
5e3a9d7f2b4c_add_cam_safety_settings.py          (Dec 8)  - CAM safety
4d2f8a9b1e3c_add_cam_pipeline_tables.py          (Dec 8)  - CAM pipeline
3b1561457c07_add_cam_tables.py                   (Dec 8)  - CAM bootstrap
```

#### Migration Safety Status
- ✅ No migrations deleted (history intact)
- ✅ Down-revisions link correctly
- ✅ ForeignKey constraints inside cam_* tables only
- ❌ **RISK**: Upcoming refactor will need to move data between modules
  - Moving CAM data → new modules requires careful migration sequencing
  - Must create "refactor" migrations (e.g., `add_delivery_tables.py` + data copy + `drop_cam_*_columns.py`)

---

### 5. Existing Contracts & Ports (Partial)

#### CAM Module Already Has:
✅ **Contracts**: `aicmo/cam/contracts/__init__.py` (362 lines)
- 11 Pydantic models (SendEmailRequest/Response, ClassifyReplyRequest, FetchInboxRequest, etc.)
- 3 Enums (ReplyClassificationEnum, LeadStateEnum, WorkerStatusEnum)
- Status: Uses Pydantic v2

✅ **Ports**: `aicmo/cam/ports/module_ports.py` (331 lines)
- 6 abstract module interfaces (EmailModule, ClassificationModule, FollowUpModule, etc.)
- Status: ABC-based, documented, tested

✅ **Orchestration**: `aicmo/platform/orchestration.py` (215 lines)
- DIContainer + ModuleRegistry
- Status: Factory pattern, creates 6 services

✅ **Composition Layer**: `aicmo/cam/composition/flow_runner.py` (540+ lines)
- CamFlowRunner with 7-step autonomous cycle
- Status: Functional, tested (4/11 E2E tests passing)

#### Missing for Other Modules
- ❌ onboarding: No contracts, no ports
- ❌ strategy: No contracts, no ports
- ❌ production: No contracts, no ports
- ❌ qc: No contracts, no ports
- ❌ client_review: No contracts, no ports
- ❌ delivery: No contracts, no ports
- ❌ reporting: No contracts, no ports
- ❌ billing: No contracts, no ports
- ❌ retention: No contracts, no ports

---

### 6. Dependency Direction Analysis

#### Current Problems
1. **CAM depends on domain** (violated rule)
   - `from aicmo.domain.strategy import StrategyDoc`
   - Domain should be in CAM, not shared

2. **Delivery depends on CAM**
   - `from aicmo.cam.db_models import CampaignDB`
   - Should communicate via contracts only

3. **No clear orchestration control plane**
   - Workers run in multiple places
   - Need: Explicit orchestration → business modules flow

#### Required Fix
```
❌ CURRENT:
    CAM ↔ Delivery ↔ Domain (circular, tight coupling)

✅ REQUIRED:
    Orchestration → (CAM, Delivery, Strategy, etc.)
        ↑
        └─ Each module imports ONLY:
           - Own aicmo/<module>/internal/*
           - aicmo/<module>/api/* (ports/dtos/events)
           - Cross-cutting: orchestration, learning, identity, observability
           - Shared: aicmo/shared/* (generic only)
```

---

### 7. Test Coverage & Harness

#### Existing Tests
- ✅ `tests/test_modular_boundary_enforcement.py` (13 tests, 9 passing)
- ✅ `tests/test_modular_e2e_smoke.py` (15 tests, 4 passing)
- ⚠️ Tests have fixture issues (not architecture issues)
- ❌ No contract tests for other modules
- ❌ No deterministic test harness (fixed clock, seeded random)
- ❌ No fake provider registry

#### Required Test Harness
Missing: `aicmo/shared/testing.py`
- Fixed clock (freezegun)
- Seeded randomness
- In-memory DB fixture
- Fake external providers
- Must be referenced by all contract tests

---

### 8. Legacy Code & Migration Risk

#### Backend Monolith Still Active
- **Path**: `/workspaces/AICMO/backend/`
- **Size**: Large (models.py, main.py, routers/, services/, api/)
- **Issue**: aicmo/ imports from backend/
  ```python
  from backend.db.base import Base
  from backend.db.session import get_session
  ```
- **Risk**: Moving code without updating imports = broken legacy API

#### Anti-Corruption Layers
- **Currently**: None exist
- **Required**: For any legacy code that stays during refactor
  - Wrap in `aicmo/<module>/internal/acl_<legacy_name>.py`
  - Translate legacy models → DTOs
  - Do NOT rewrite blindly

---

### 9. Known Violations (Enforcement Baseline)

#### Will-FAIL Violations (Must Fix Before Phase 1 Complete)
1. ❌ `aicmo/delivery/execution_orchestrator.py` imports `CampaignDB` + writes
2. ❌ `aicmo/delivery/output_packager.py` imports `LeadDB` + writes
3. ❌ `aicmo/domain/project.py` imports `CampaignDB` + writes
4. ❌ `aicmo/operator_services.py` imports CAM models + writes
5. ❌ `aicmo/cam/` imports `aicmo/domain/*` (should be contracts only)
6. ❌ 29 files import `aicmo/domain` (god module, must decompose)

#### Acceptable (For Now)
- ⚠️ CAM module imports own db_models (internal, allowed)
- ⚠️ Legacy backend/ code exists (marked for future ACL wrapping)
- ⚠️ Global session factory in aicmo/core/db.py (will be replaced per-module)

---

### 10. Database Schema Analysis

#### Tables Currently in Scope (CAM)
| Table | Owner | Writers | Status |
|-------|-------|---------|--------|
| cam_campaigns | CAM | CAM + Delivery + Domain + Operator ❌ | VIOLATION |
| cam_leads | CAM | CAM + Delivery + Operator ❌ | VIOLATION |
| cam_attempts | CAM | CAM | ✓ OK |
| cam_discovery_jobs | CAM | CAM | ✓ OK |
| cam_discovered_profiles | CAM | CAM | ✓ OK |
| cam_outbound_emails | CAM | CAM | ✓ OK |
| cam_inbound_emails | CAM | CAM | ✓ OK |
| cam_worker_heartbeats | CAM | CAM | ✓ OK |
| cam_human_alert_logs | CAM | CAM | ✓ OK |

#### Tables in Other Modules
| Table | Owner | Current State | Status |
|-------|-------|---------------|--------|
| (delivery) | Delivery | No separate schema | ❌ MUST CREATE |
| (onboarding) | Onboarding | No schema | ❌ MUST CREATE |
| (strategy) | Strategy | No schema | ❌ MUST CREATE |
| (production) | Production | No schema | ❌ MUST CREATE |
| (qc) | QC | No schema | ❌ MUST CREATE |
| (client_review) | ClientReview | No schema | ❌ MUST CREATE |
| (reporting) | Reporting | No schema | ❌ MUST CREATE |
| (billing) | Billing | No schema | ❌ MUST CREATE |
| (retention) | Retention | No schema | ❌ MUST CREATE |

---

## PHASE 0 CONCLUSION

### What's Broken (Violations Found)

| Violation | Severity | Count | Files |
|-----------|----------|-------|-------|
| Cross-module DB writes | 🔴 CRITICAL | 4 | delivery/*, domain/*, operator_services.py |
| Cross-module internal imports | 🔴 CRITICAL | 29 | *domain* imports |
| God module exists | 🔴 CRITICAL | 1 | aicmo/domain/ |
| No contracts for 9/10 business modules | 🟠 HIGH | 9 | onboarding, strategy, production, qc, client_review, delivery, reporting, billing, retention |
| No data ownership isolation | 🟠 HIGH | Full | All modules share session |
| No test harness | 🟡 MEDIUM | — | aicmo/shared/testing.py missing |
| No ACL for legacy code | 🟡 MEDIUM | — | backend/* not wrapped |

### What's Partially OK (CAM)

- ✅ Contracts defined
- ✅ Ports defined
- ✅ DIContainer factory works
- ✅ CamFlowRunner orchestrates cycle
- ✅ Tests in place
- ❌ But still imports aicmo/domain (god module)
- ❌ Still has cross-module writers to its tables

### What Must Happen Before Continuing

1. **Phase 0 Sign-Off**: This document reviewed, violations confirmed
2. **Phase 1 Execution**: Must create module skeletons (api/, internal/ separation)
3. **Circular Dependency Fix**: domain → decomposed into owning modules
4. **Data Ownership Fix**: Cross-module writers removed via contracts + sagas
5. **Enforcement**: Build must fail on NEW violations (legacy allowed for now)

---

## Phase 0 Violation Summary Table

```
VIOLATIONS BY CATEGORY

[A] Boundaries & Ownership
    ❌ aicmo/delivery/ imports aicmo/cam/db_models          → 2 files
    ❌ aicmo/domain/ imports aicmo/cam/db_models            → 1 file
    ❌ aicmo/operator_services.py imports aicmo/cam/db_models → 1 file
    ❌ aicmo/domain/ is god module (29 importers)           → CRITICAL

[B] Database & Migration Safety
    ❌ cam_campaigns table has 4 writers (should be 1)       → CAM only
    ❌ cam_leads table has 3 writers (should be 1)          → CAM only
    ⚠️ Upcoming refactor needs "move" migrations             → PLAN NOW

[C] Dependency Direction
    ❌ No clear orchestration → modules flow                 → MISSING
    ❌ Modules importing internals                           → 29 files
    ❌ No DTO/event boundaries defined                       → 9/10 modules

[D] Transactions & Consistency
    ⚠️ Shared session across modules                         → WILL BREAK
    ❌ No saga pattern for multi-step flows                  → MISSING

[E] Enforcement (CI)
    ❌ No import guard config                                → MISSING
    ❌ No baseline violation allow-list                      → MUST CREATE

[F] Context Preservation
    ✅ This file (_AICMO_REFACTOR_STATUS.md) created         → PHASE 0 DONE

[G] Tests
    ⚠️ Existing tests for CAM only                           → 28 tests
    ❌ No contract tests for 9 other modules                 → MUST CREATE
    ❌ No deterministic test harness                         → MUST CREATE

[H] Contract Versioning
    ✅ CAM has CONTRACT_VERSION in contracts/__init__.py     → OK
    ❌ Other modules have no contracts                       → MISSING

[I] Legacy & ACL
    ❌ backend/* not wrapped in ACL                          → PENDING
    ❌ No aicmo/<module>/internal/acl_*.py files             → PENDING
```

---

## BLOCKERS FOR PHASE 1

### Must Decide Before Starting Phase 1

**Q1: Should backend/ code be:**
- [ ] A. Completely rewritten (delete, reimplement in aicmo/)
- [ ] B. Wrapped in ACLs (keep, translate to contracts)
- [ ] C. Gradually migrated (Phase-by-phase refactor)

**Q2: What is aicmo/domain supposed to be?**
- [ ] A. Deleted entirely (logic moves into owning modules)
- [ ] B. Kept as shared value objects (non-business types only)
- [ ] C. Refactored into module-specific domains

**Q3: Table ownership for new modules:**
- [ ] A. Create new tables immediately in Phase 1 (migration risk)
- [ ] B. Use logical FKs to existing cam_* tables (temporary)
- [ ] C. Phase migration separately (Phase 5)

**Q4: Orchestration layer:**
- [ ] A. Use existing aicmo/platform/orchestration (extend it)
- [ ] B. Create new aicmo/orchestration module (cleaner, separate)
- [ ] C. Use external system (Airflow, Temporal, etc.)

---

## Next Steps (Phase 1 Waiting)

After Phase 0 sign-off, Phase 1 will:

1. **Create module skeleton directories** (api/, internal/ separation)
2. **Define contracts for all 10 business modules** + 4 cross-cutting
3. **Create test harness** (aicmo/shared/testing.py)
4. **Write contract tests** (empty ports first, tests first)
5. **No code moves yet** (structure only)

---

## Files Affected (Preview)

```
Phase 1 Will Create:
├── aicmo/onboarding/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ports.py       (abstract interfaces)
│   │   ├── dtos.py        (input/output contracts)
│   │   └── events.py      (domain events)
│   └── internal/
│       └── .gitkeep
├── aicmo/strategy/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ports.py
│   │   ├── dtos.py
│   │   └── events.py
│   └── internal/
│       └── .gitkeep
... (8 more business modules)
├── aicmo/orchestration/       (NEW or extend platform/)
├── aicmo/identity/            (NEW)
├── aicmo/observability/       (NEW)
└── aicmo/shared/
    ├── testing.py             (NEW - test harness)
    ├── clock.py               (maybe)
    ├── ids.py                 (maybe)
    └── errors.py              (maybe)

Phase 1 Will Create Tests:
└── tests/contracts/
    ├── test_cam_ports.py          ✅ (exists)
    ├── test_onboarding_ports.py   (NEW)
    ├── test_strategy_ports.py     (NEW)
    ... (8 more)
```

---

**Status**: 🟡 **PHASE 0 COMPLETE — AWAITING APPROVAL**

**Recommendations**:
1. Answer Q1-Q4 blocking questions above
2. Confirm target module map is correct
3. Approve violation list
4. Proceed to Phase 1

**Estimated Phase 1 Duration**: 2-3 hours (structure + test harness only, no logic moves)
