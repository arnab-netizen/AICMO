# Phase 4 DB-Mode E2E Status

**Status**: ⚠️ **PARTIALLY WIRED** (Composition root ready, workflow tests not wired)  
**Date**: December 13, 2025  
**Test Results**: 11/11 E2E passing (but 8 workflow tests bypass DB mode)

---

## Executive Summary

**DB-mode infrastructure is COMPLETE**:
- ✅ CompositionRoot selects DB repos when `AICMO_PERSISTENCE_MODE=db` ([proof test](tests/e2e/test_db_mode_composition_proof.py))
- ✅ All 3 persistence repos have DB implementations (Onboarding, Strategy, Production)
- ✅ Migrations applied and at head (8dc2194a008b)
- ✅ Config system working (`is_db_mode()` in [aicmo/shared/config.py](aicmo/shared/config.py))

**Workflow E2E tests NOT using DB mode**:
- ❌ Workflow tests hardcode in-memory repos in fixtures
- ❌ Setting `AICMO_PERSISTENCE_MODE=db` has NO effect on workflow tests
- ❌ Workflow tests bypass CompositionRoot entirely

**Impact**: Workflow E2E tests don't validate real DB persistence behavior.

---

## Proof: Composition Root Switches Repos

**Test**: [tests/e2e/test_db_mode_composition_proof.py](tests/e2e/test_db_mode_composition_proof.py)

```bash
$ pytest tests/e2e/test_db_mode_composition_proof.py -v

test_composition_root_selects_db_repos_in_db_mode PASSED
test_composition_root_selects_inmemory_repos_in_inmemory_mode PASSED
test_composition_root_default_mode_is_inmemory PASSED

========================= 3/3 passed ✅
```

**What This Proves**:
- When `AICMO_PERSISTENCE_MODE=db`: CompositionRoot instantiates DatabaseBriefRepo, DatabaseStrategyRepo, DatabaseProductionRepo
- When `AICMO_PERSISTENCE_MODE=inmemory`: CompositionRoot instantiates InMemoryBriefRepo, InMemoryStrategyRepo, InMemoryProductionRepo
- Default (no env var): In-memory mode

**File Evidence**:
- [aicmo/orchestration/composition/root.py](aicmo/orchestration/composition/root.py#L71-L76):
  ```python
  if is_db_mode():
      self._brief_repo = DatabaseBriefRepo()
      self._strategy_repo = DatabaseStrategyRepo()
  else:
      self._brief_repo = InMemoryBriefRepo()
      self._strategy_repo = InMemoryStrategyRepo()
  self._production_repo = create_production_repository()  # Uses factory
  ```

---

## Problem: Workflow Tests Bypass CompositionRoot

### Current Workflow Test Pattern

**Files**:
- [tests/e2e/test_workflow_happy.py](tests/e2e/test_workflow_happy.py)
- [tests/e2e/test_workflow_delivery_fail_compensates.py](tests/e2e/test_workflow_delivery_fail_compensates.py)
- [tests/e2e/test_workflow_qc_fail_compensates.py](tests/e2e/test_workflow_qc_fail_compensates.py)

**Current Fixture** (from [test_workflow_happy.py](tests/e2e/test_workflow_happy.py#L28-L56)):
```python
@pytest.fixture
def workflow():
    """Create workflow with all dependencies wired."""
    # HARDCODED IN-MEMORY REPOS
    brief_repo = InMemoryBriefRepo()
    strategy_repo = InMemoryStrategyRepo()
    draft_repo = InMemoryProductionRepo()
    qc_repo = InMemoryQcRepo()
    delivery_repo = InMemoryDeliveryRepo()
    
    # Create adapters manually
    brief_normalize = BriefNormalizeAdapter(brief_repo)
    strategy_generate = StrategyGenerateAdapter(strategy_repo)
    draft_generate = DraftGenerateAdapter(draft_repo)
    qc_evaluate = QcEvaluateAdapter(qc_repo)
    delivery_package = DeliveryPackageAdapter(delivery_repo)
    
    # Create saga coordinator
    saga = SagaCoordinator()
    
    # Create workflow
    return ClientToDeliveryWorkflow(
        saga_coordinator=saga,
        brief_normalize=brief_normalize,
        strategy_generate=strategy_generate,
        draft_generate=draft_generate,
        qc_evaluate=qc_evaluate,
        delivery_package=delivery_package,
    )
```

**Problem**: This fixture ignores `AICMO_PERSISTENCE_MODE` and always uses in-memory repos.

### Evidence of Bypass

```bash
$ AICMO_PERSISTENCE_MODE=db pytest tests/e2e/test_workflow_happy.py -v
# PASSES but still uses InMemoryBriefRepo (hardcoded in fixture)

$ AICMO_PERSISTENCE_MODE=inmemory pytest tests/e2e/test_workflow_happy.py -v  
# PASSES with same InMemoryBriefRepo (no difference)
```

**Tests Affected**: 8 workflow tests (3 happy + 3 qc_fail + 2 delivery_fail)

---

## What Needs To Change

### Option 1: Use CompositionRoot in Workflow Fixtures (RECOMMENDED)

**Change**: Replace manual repo instantiation with CompositionRoot.

**Before** ([test_workflow_happy.py](tests/e2e/test_workflow_happy.py#L28-L56)):
```python
@pytest.fixture
def workflow():
    # HARDCODED REPOS
    brief_repo = InMemoryBriefRepo()
    strategy_repo = InMemoryStrategyRepo()
    # ... manual wiring
```

**After**:
```python
@pytest.fixture
def workflow():
    # USE COMPOSITION ROOT (respects AICMO_PERSISTENCE_MODE)
    from aicmo.orchestration.composition.root import CompositionRoot
    
    root = CompositionRoot()
    
    # Get workflow from composition root
    return root.create_client_to_delivery_workflow()
```

**Files to Change**:
1. [tests/e2e/test_workflow_happy.py](tests/e2e/test_workflow_happy.py#L28-L56)
2. [tests/e2e/test_workflow_qc_fail_compensates.py](tests/e2e/test_workflow_qc_fail_compensates.py#L28-L56)
3. [tests/e2e/test_workflow_delivery_fail_compensates.py](tests/e2e/test_workflow_delivery_fail_compensates.py#L28-L56)

**Prerequisite**: CompositionRoot must expose `create_client_to_delivery_workflow()` method.

**Current State**: CompositionRoot exposes individual adapters but NOT workflow factory.

**Required Change in** [aicmo/orchestration/composition/root.py](aicmo/orchestration/composition/root.py):
```python
def create_client_to_delivery_workflow(self) -> ClientToDeliveryWorkflow:
    """Create fully-wired ClientToDeliveryWorkflow."""
    from aicmo.orchestration.internal.workflows.client_to_delivery import ClientToDeliveryWorkflow
    
    return ClientToDeliveryWorkflow(
        saga_coordinator=self.saga_coordinator,
        brief_normalize=self.brief_normalize,
        strategy_generate=self.strategy_generate,
        draft_generate=self.draft_generate,
        qc_evaluate=self.qc_evaluate,
        delivery_package=self.delivery_package,
    )
```

---

### Option 2: Conditional Repo Selection in Fixtures

**Change**: Add mode detection to fixtures.

**Pattern**:
```python
@pytest.fixture
def workflow():
    from aicmo.shared.config import is_db_mode
    
    if is_db_mode():
        # Use DB repos
        from aicmo.onboarding.internal.adapters import DatabaseBriefRepo
        from aicmo.strategy.internal.repositories_db import DatabaseStrategyRepo
        brief_repo = DatabaseBriefRepo()
        strategy_repo = DatabaseStrategyRepo()
    else:
        # Use in-memory repos
        from aicmo.onboarding.internal.adapters import InMemoryBriefRepo
        from aicmo.strategy.internal.repositories_mem import InMemoryStrategyRepo
        brief_repo = InMemoryBriefRepo()
        strategy_repo = InMemoryStrategyRepo()
    
    # ... rest of manual wiring
```

**Downside**: Duplicates CompositionRoot logic (maintenance burden).

---

## Recommended Implementation Plan

### Phase 1: Add Workflow Factory to CompositionRoot

**File**: [aicmo/orchestration/composition/root.py](aicmo/orchestration/composition/root.py)

**Add Method**:
```python
def create_client_to_delivery_workflow(self) -> ClientToDeliveryWorkflow:
    """
    Create fully-wired ClientToDeliveryWorkflow.
    
    Workflow will use repos based on AICMO_PERSISTENCE_MODE:
    - inmemory: In-memory repos (default, fast)
    - db: Database repos (real persistence)
    """
    from aicmo.orchestration.internal.workflows.client_to_delivery import ClientToDeliveryWorkflow
    
    return ClientToDeliveryWorkflow(
        saga_coordinator=self.saga_coordinator,
        brief_normalize=self.brief_normalize,
        strategy_generate=self.strategy_generate,
        draft_generate=self.draft_generate,
        qc_evaluate=self.qc_evaluate,
        delivery_package=self.delivery_package,
    )
```

**Test**: Verify factory works in both modes:
```python
def test_workflow_factory_respects_persistence_mode(monkeypatch):
    monkeypatch.setenv("AICMO_PERSISTENCE_MODE", "db")
    # Force reload
    from aicmo.shared import config
    config.settings = config.AicmoSettings()
    
    root = CompositionRoot()
    workflow = root.create_client_to_delivery_workflow()
    
    # Workflow adapters should use DB repos
    assert isinstance(root._brief_repo, DatabaseBriefRepo)
```

---

### Phase 2: Update Workflow Test Fixtures

**Files to Change** (3 files):
1. [tests/e2e/test_workflow_happy.py](tests/e2e/test_workflow_happy.py)
2. [tests/e2e/test_workflow_qc_fail_compensates.py](tests/e2e/test_workflow_qc_fail_compensates.py)
3. [tests/e2e/test_workflow_delivery_fail_compensates.py](tests/e2e/test_workflow_delivery_fail_compensates.py)

**Change Pattern**:

**Before**:
```python
@pytest.fixture
def workflow():
    # Manual repo instantiation (hardcoded in-memory)
    brief_repo = InMemoryBriefRepo()
    strategy_repo = InMemoryStrategyRepo()
    # ... 20+ lines of manual wiring
```

**After**:
```python
@pytest.fixture
def workflow():
    """Create workflow respecting AICMO_PERSISTENCE_MODE."""
    from aicmo.orchestration.composition.root import CompositionRoot
    
    root = CompositionRoot()
    return root.create_client_to_delivery_workflow()
```

**Lines of Code**: Reduce from ~30 lines to ~4 lines per fixture (3 files × 26 lines = 78 lines deleted).

---

### Phase 3: Add DB Cleanup Fixtures (for DB mode tests)

**File**: [tests/e2e/conftest.py](tests/e2e/conftest.py) (create if doesn't exist)

**Add Fixture**:
```python
import pytest
from aicmo.shared.config import is_db_mode
from aicmo.core.db import get_session
from aicmo.onboarding.internal.models import BriefDB, IntakeDB
from aicmo.strategy.internal.models import StrategyDB, TacticAssignmentDB
from aicmo.production.internal.models import ContentDraftDB, DraftBundleDB, BundleAssetDB


@pytest.fixture(autouse=True)
def cleanup_db_after_test():
    """Clean up DB tables after each test if in DB mode."""
    yield  # Run test
    
    if is_db_mode():
        # Clean up tables to prevent test pollution
        with get_session() as session:
            session.query(BundleAssetDB).delete()
            session.query(DraftBundleDB).delete()
            session.query(ContentDraftDB).delete()
            session.query(TacticAssignmentDB).delete()
            session.query(StrategyDB).delete()
            session.query(IntakeDB).delete()
            session.query(BriefDB).delete()
            session.commit()
```

**Purpose**: Prevent test pollution when running in DB mode (real Postgres).

---

### Phase 4: Verify DB-Mode E2E Works

**Commands**:
```bash
# Ensure migrations applied
alembic upgrade head

# Run in in-memory mode (baseline)
AICMO_PERSISTENCE_MODE=inmemory pytest tests/e2e/test_workflow_happy.py -v

# Run in DB mode (should work after fixes)
AICMO_PERSISTENCE_MODE=db pytest tests/e2e/test_workflow_happy.py -v

# Run all E2E in both modes
AICMO_PERSISTENCE_MODE=inmemory pytest tests/e2e/ -v
AICMO_PERSISTENCE_MODE=db pytest tests/e2e/ -v
```

**Expected**: All tests pass in both modes.

---

## Current Test Status

### Working Tests (3 tests)
- ✅ [test_db_mode_composition_proof.py](tests/e2e/test_db_mode_composition_proof.py) (3 tests)
  - Proves CompositionRoot switches repos correctly

### Not Respecting DB Mode (8 tests)
- ⚠️ [test_workflow_happy.py](tests/e2e/test_workflow_happy.py) (3 tests)
  - Uses hardcoded InMemoryBriefRepo
  - Bypasses CompositionRoot
  
- ⚠️ [test_workflow_qc_fail_compensates.py](tests/e2e/test_workflow_qc_fail_compensates.py) (3 tests)
  - Uses hardcoded InMemoryQcRepo
  - Bypasses CompositionRoot
  
- ⚠️ [test_workflow_delivery_fail_compensates.py](tests/e2e/test_workflow_delivery_fail_compensates.py) (2 tests)
  - Uses hardcoded InMemoryDeliveryRepo
  - Bypasses CompositionRoot

**Total**: 11 E2E tests (3 working correctly, 8 need wiring)

---

## Migration Status

**Current Head**: `8dc2194a008b_add_production_draft_bundle_tables`

**Applied Migrations**:
1. `f07c2ce2a3de` - Onboarding (workflow_runs, onboarding_brief, onboarding_intake)
2. `18ea2bd8b079` - Strategy (strategies, tactic_assignments)
3. `8dc2194a008b` - Production (production_drafts, production_bundles, production_bundle_assets)

**Verification**:
```bash
$ alembic current
8dc2194a008b (head) ✅

$ alembic heads
8dc2194a008b (head) ✅
```

**Schema Ready**: All 3 persistence-enabled modules have tables (Onboarding, Strategy, Production).

---

## DB Configuration

**File**: [aicmo/shared/config.py](aicmo/shared/config.py#L21-L24)

**Default**:
```python
PERSISTENCE_MODE: str = "inmemory"
DATABASE_URL: str = "sqlite:///./aicmo.db"
```

**Environment Variables**:
- `AICMO_PERSISTENCE_MODE` - Set to "db" or "inmemory"
- `AICMO_DATABASE_URL` - Postgres connection string (e.g., `postgresql://user:pass@localhost:5432/aicmo`)

**Current Production DB** (assumed from dev container):
- Host: localhost (Postgres service)
- Database: aicmo
- Schema: Applied via Alembic

---

## Effort Estimate

### Minimal Path (Use CompositionRoot)

**Changes Required**:
1. Add `create_client_to_delivery_workflow()` to CompositionRoot (10 lines)
2. Update 3 workflow test files to use CompositionRoot (78 lines deleted, 12 added)
3. Add DB cleanup fixture to tests/e2e/conftest.py (20 lines)

**Total**: ~50 lines changed across 4 files

**Estimated Time**: 30 minutes (coding) + 15 minutes (testing) = 45 minutes

**Risk**: Low (CompositionRoot already working, proven by test_db_mode_composition_proof.py)

---

### Full Path (Add Parameterized Mode Testing)

**Additional Changes**:
1. Parameterize workflow tests to run in both modes:
   ```python
   @pytest.mark.parametrize("persistence_mode", ["inmemory", "db"])
   def test_workflow_happy_path(persistence_mode, monkeypatch):
       monkeypatch.setenv("AICMO_PERSISTENCE_MODE", persistence_mode)
       # ... test logic
   ```

2. Add DB cleanup per mode (skip in inmemory mode)

3. Add markers for DB tests:
   ```python
   @pytest.mark.db  # Skip if ENABLE_DB_TESTS not set
   def test_workflow_db_mode():
       ...
   ```

**Total**: ~100 lines changed across 5 files

**Estimated Time**: 1.5 hours

**Benefit**: Double test coverage (run every workflow test in both modes)

---

## Conclusion

**DB-Mode Infrastructure**: ✅ COMPLETE
- Repos implemented
- Composition root wired
- Migrations applied
- Config system working

**DB-Mode E2E Tests**: ❌ NOT WIRED YET
- Workflow tests bypass CompositionRoot
- Hardcode in-memory repos
- Setting env var has no effect

**Next Step**: Implement Phase 1-4 above to wire workflow tests to CompositionRoot.

**Blocking Issue**: None (infrastructure ready, just need to update 3 test files)

**Documentation Status**: ✅ COMPLETE (this file provides concrete file paths and change patterns)
