# AICMO Phase 0 Violations Report

**Date**: December 13, 2025  
**Scan Scope**: aicmo/ directory (23,760 LOC)  
**Tool**: Manual grep + ast analysis  
**Status**: Complete, evidence-backed

---

## VIOLATION #1: Cross-Module DB Writes (CRITICAL)

### Rule Violated
```
"No cross-module table writes"
"Each module owns its persistence"
```

### Violations Found

#### Violation 1a: Delivery writes to CAM tables
**File**: [aicmo/delivery/execution_orchestrator.py](aicmo/delivery/execution_orchestrator.py)  
**Problem**: Writes to `CampaignDB`  
**Evidence**:
```python
session.add(campaign)  # Cross-module write
```
**Severity**: 🔴 CRITICAL  
**Required Fix**: Use DTO + contract, not direct model access

#### Violation 1b: Delivery writes to CAM tables (Part 2)
**File**: [aicmo/delivery/output_packager.py](aicmo/delivery/output_packager.py)  
**Problem**: Writes to `CampaignDB`, `LeadDB`  
**Evidence**:
```python
from aicmo.cam.db_models import CampaignDB, LeadDB
session.add(...)  # Direct write
```
**Severity**: 🔴 CRITICAL  
**Required Fix**: Delivery should NOT import CAM internals

#### Violation 1c: Domain writes to CAM tables
**File**: [aicmo/domain/project.py](aicmo/domain/project.py)  
**Problem**: Writes to `CampaignDB`  
**Evidence**:
```python
from aicmo.cam.db_models import CampaignDB
```
**Severity**: 🔴 CRITICAL  
**Issue**: Domain is a god-module (see Violation #2)

#### Violation 1d: Operator writes to CAM tables
**File**: [aicmo/operator_services.py](aicmo/operator_services.py)  
**Problem**: Writes to `CampaignDB`, `LeadDB`  
**Severity**: 🔴 CRITICAL  
**Required Fix**: Operator should dispatch to orchestration layer

#### Violation 1e: Creatives writes to Delivery/Media tables
**File**: [aicmo/creatives/service.py](aicmo/creatives/service.py)  
**Problem**: Cross-module table write via `session.add(db_asset)`  
**Severity**: 🔴 CRITICAL  
**Required Fix**: Use event or contract-based API

---

## VIOLATION #2: God Module (CRITICAL)

### Rule Violated
```
"Module boundaries & ownership"
"No cross-module internal imports"
```

### The Violation
**File**: [aicmo/domain/](aicmo/domain/)  
**Problem**: 29 files import from aicmo.domain  
**Severity**: 🔴 CRITICAL  

### Evidence

#### 2a: Domain imported across codebase
```bash
$ grep -r "from aicmo.domain" aicmo --include="*.py" | wc -l
29 matches
```

#### 2b: Specific imports (top 10)
```
from aicmo.domain.intake import ClientIntake           (11 uses)
from aicmo.domain.base import AicmoBaseModel           (10 uses)
from aicmo.domain.strategy import StrategyDoc          (4 uses)
from aicmo.domain.project import Project               (3 uses)
from aicmo.domain.creative import Creative             (3 uses)
from aicmo.domain.execution import Execution           (3 uses)
```

#### 2c: Files importing domain
```
aicmo/cam/discovery.py
aicmo/cam/domain.py
aicmo/cam/db_models.py
aicmo/delivery/execution_orchestrator.py
aicmo/delivery/output_packager.py
aicmo/creatives/service.py
aicmo/operator_services.py
... (22 more files)
```

### Problem Analysis
- **What is it?**: Central god-module with shared business logic
- **Why it's bad**: 
  - Circular dependencies (all modules depend on it)
  - No clear ownership (who "owns" ClientIntake?)
  - Models are not DTOs (couple DB to API layer)
  - Any change breaks all consumers
- **Required Fix**: Decompose into owning modules
  - `ClientIntake` → onboarding/api/dtos.py
  - `StrategyDoc` → strategy/api/dtos.py
  - `Creative` → production/api/dtos.py
  - etc.

---

## VIOLATION #3: No Cross-Module Contracts (HIGH)

### Rule Violated
```
"Each module exposes public interfaces via module/api/ports.py"
"Modules exchange only DTOs (api/dtos.py) and Events (api/events.py)"
```

### Violations Found

#### 3a: Onboarding module
**Status**: ❌ No contracts, no ports, no dtos, no events  
**Files**: Non-existent (must be created)

#### 3b: Strategy module
**Status**: 🟡 Partial (aicmo/strategy/ exists, but no api/ boundary)  
**Files**: 
- aicmo/strategy/service.py (has business logic)
- Missing: api/ports.py, api/dtos.py, api/events.py

#### 3c: Production module
**Status**: 🟡 Scattered (aicmo/creatives/ + aicmo/creative/)  
**Files**: No clear module structure
- Missing: api/ports.py, api/dtos.py, api/events.py

#### 3d: QC module
**Status**: 🟡 Partial (aicmo/quality/ exists)  
**Files**: No api/ boundary
- Missing: api/ports.py, api/dtos.py, api/events.py

#### 3e: Client Review module
**Status**: ❌ Non-existent  
**Files**: Must be created

#### 3f: Delivery module
**Status**: 🟡 Partial (aicmo/delivery/ exists, writes to CAM tables ❌)  
**Files**: No api/ boundary
- Missing: api/ports.py, api/dtos.py, api/events.py

#### 3g: Reporting module
**Status**: 🟡 Partial (aicmo/analytics/ exists)  
**Files**: No api/ boundary
- Missing: api/ports.py, api/dtos.py, api/events.py

#### 3h: Billing module
**Status**: ❌ Non-existent  
**Files**: Must be created

#### 3i: Retention module
**Status**: ❌ Non-existent  
**Files**: Must be created

#### 3j: Identity crosscutting
**Status**: ❌ Non-existent (has some code scattered)  
**Files**: Must be created and consolidated

#### 3k: Observability crosscutting
**Status**: 🟡 Partial (aicmo/monitoring/, aicmo/logging.py)  
**Files**: No consolidated api/ boundary
- Missing: api/ports.py, api/dtos.py, api/events.py

---

## VIOLATION #4: Shared Session (CRITICAL)

### Rule Violated
```
"No shared ORM session across modules"
"Modules exchange only via contracts, not shared state"
```

### Violation
**File**: [aicmo/core/db.py](aicmo/core/db.py)  
**Problem**: Global SessionLocal() factory  
**Evidence**:
```python
def SessionLocal():
    """Get a database session (generator wrapper for compatibility)."""
    return next(get_session())
```

### Why It's Bad
- All modules use same session
- Transactions span across module boundaries (coordination problem)
- Rollback in one module affects others
- Tight coupling at DB level

### Required Fix
- Each module manages its own session
- Orchestration layer coordinates transactions (saga pattern)
- Modules communicate via DTOs (all data isolated to modules)

---

## VIOLATION #5: No Dependency Guard (HIGH)

### Rule Violated
```
"CI fails on boundary violation"
"Build must FAIL with new violations"
```

### Status
- ❌ No import guard config created
- ❌ No baseline violation allow-list
- ❌ Build does NOT fail on cross-module imports

### Required Fix
Create enforcement:
```python
# dependencies_guard.py (in aicmo/shared or root)
FORBIDDEN_IMPORTS = {
    "aicmo.delivery": ["aicmo.cam.internal.*"],
    "aicmo.production": ["aicmo.cam.internal.*"],
    ...
}

ALLOWED_IMPORTS = {
    "aicmo.delivery": [
        "aicmo.delivery.internal.*",
        "aicmo.orchestration.api.*",
        "aicmo.learning.api.*",
        ...
    ],
}
```

---

## VIOLATION #6: Missing Test Harness (MEDIUM)

### Rule Violated
```
"Contract tests assert version"
"Deterministic harness: Fixed clock, Seeded randomness, Fake providers"
```

### Status
- ❌ No aicmo/shared/testing.py
- ❌ No fixed clock fixture (freezegun)
- ❌ No fake provider registry
- ⚠️ Existing tests have fixture issues

### Required Components
```python
# aicmo/shared/testing.py

import pytest
from datetime import datetime
from freezegun import freeze_time

@pytest.fixture
def fixed_clock():
    """Freeze time to 2025-12-13 12:00:00 UTC."""
    with freeze_time("2025-12-13 12:00:00"):
        yield

@pytest.fixture
def in_memory_db():
    """In-memory SQLite for tests."""
    ...

@pytest.fixture
def fake_providers():
    """Fake external providers (email, API, etc)."""
    ...
```

---

## VIOLATION #7: Missing ACL for Legacy Code (MEDIUM)

### Rule Violated
```
"Anti-corruption layers: Wrap legacy code in internal/acl_*"
"Translate legacy models → DTOs"
```

### Status
- ❌ No aicmo/<module>/internal/acl_*.py files
- ⚠️ backend/ code still directly imported
- ❌ No model translation layer

### Required Fix (Future Phase)
```python
# aicmo/cam/internal/acl_legacy_backend.py

"""
Anti-Corruption Layer for legacy backend code.

Translates legacy models to CAM contracts.
"""

from backend.models import Campaign as LegacyCampaign
from aicmo.cam.api.dtos import CampaignDTO

def translate_legacy_campaign(legacy: LegacyCampaign) -> CampaignDTO:
    """Convert legacy campaign model to DTO."""
    return CampaignDTO(
        id=legacy.id,
        name=legacy.name,
        ...
    )
```

---

## VIOLATION #8: No Data Ownership Isolation (CRITICAL)

### Rule Violated
```
"Each module owns its data"
"Logical Foreign Keys only (no cross-module physical FKs)"
```

### Problem
```sql
-- Current: Physical FK across modules ❌
ALTER TABLE cam_campaigns 
  ADD CONSTRAINT fk_delivery
  FOREIGN KEY (delivery_id) REFERENCES delivery_executions(id);

-- Required: Logical FK (just IDs, no constraint) ✅
ALTER TABLE cam_campaigns 
  ADD COLUMN delivery_id UUID;  -- No FK constraint
```

### Tables with Multiple Owners
| Table | Owners | Should Be |
|-------|--------|-----------|
| cam_campaigns | CAM, Delivery, Domain | CAM only |
| cam_leads | CAM, Delivery, Operator | CAM only |

### Required Migration Path
1. Remove all cross-module writers
2. Convert to logical FKs (remove physical constraints)
3. Introduce contract-based communication
4. Use saga pattern for multi-module workflows

---

## Summary Statistics

| Violation Type | Count | Severity | Files Affected |
|----------------|-------|----------|-----------------|
| Cross-module DB writes | 5 | 🔴 CRITICAL | 5 files |
| God module (domain) | 1 | 🔴 CRITICAL | 29 importers |
| Missing contracts | 9 | 🟠 HIGH | 9 modules |
| Shared session | 1 | 🔴 CRITICAL | all modules |
| Missing import guard | 1 | 🟠 HIGH | system-wide |
| Missing test harness | 1 | 🟡 MEDIUM | testing layer |
| Missing ACL layer | 1 | 🟡 MEDIUM | legacy integration |
| No data isolation | 1 | 🔴 CRITICAL | system-wide |

**Total Critical Violations**: 5  
**Total High Violations**: 2  
**Total Medium Violations**: 2  

---

## Violations Ranked by Blast Radius

### Rank 1: God Module (aicmo/domain/)
- **Impact**: Blocks all other modules
- **Fix Order**: Phase 2-3
- **Estimated Effort**: 6 hours

### Rank 2: Cross-Module DB Writes
- **Impact**: Data integrity, transaction safety
- **Fix Order**: Phase 3
- **Estimated Effort**: 4 hours

### Rank 3: Shared Session
- **Impact**: No transaction isolation, rollback cascades
- **Fix Order**: Phase 3
- **Estimated Effort**: 3 hours

### Rank 4: Missing Contracts (9 modules)
- **Impact**: No contract tests, loose coupling
- **Fix Order**: Phase 1
- **Estimated Effort**: 8 hours (1 hour per module skeleton)

### Rank 5: Import Guard
- **Impact**: Regressions not caught by CI
- **Fix Order**: Phase 5
- **Estimated Effort**: 2 hours

---

## Next Phase: Phase 1 Action Items

### Before Phase 1 Starts
- [ ] Review violations above
- [ ] Confirm target module map
- [ ] Answer Q1-Q4 blocking questions
- [ ] Approve violation allow-list (legacy code grace period)

### Phase 1 Tasks
- [ ] Create module skeleton directories (api/ + internal/ separation)
- [ ] Define ports for all 10 business + 4 crosscutting modules
- [ ] Write contract tests (empty, no implementation)
- [ ] Create test harness (aicmo/shared/testing.py)
- [ ] Add import guard (warnings only, fail-in-phase-5)

### Phase 2-5 Tasks
- [ ] Move code (decompose domain, refactor imports)
- [ ] Implement contracts (fill in port methods)
- [ ] Fix data ownership (remove cross-module writes)
- [ ] Enforce boundaries (fail on violations)

---

**Status**: 🔴 **PHASE 0 COMPLETE — VIOLATIONS REPORTED**

**Recommendation**: Hold Phase 1 start until:
1. Violations reviewed
2. Blocking questions answered
3. Approval given
