# Phase 4 Lane B Step 5: Strategy Module DB Persistence - COMPLETE ✅

**Date**: 2025-06-10  
**Module**: Strategy  
**Migration**: `18ea2bd8b079_add_strategy_document_table.py`

---

## Executive Summary

Successfully implemented DB persistence for Strategy module following Phase 4 Lane B methodology. All 104 tests passing (84 baseline + 20 new persistence tests). Dual-mode verified (inmemory/db). Zero contract changes. No cross-module FKs.

---

## Idempotency Strategy

**Key Decision**: Strategy module has no `workflow_run_id` in ports/DTOs.

**Solution**: Used **(brief_id, version)** as composite idempotency key:
- `brief_id`: Stable identifier from upstream Brief module
- `version`: Integer version counter (1, 2, 3...)
- **DB Enforcement**: `UniqueConstraint('brief_id', 'version', name='uq_strategy_brief_version')`

**Rationale**:
- Both fields already present in `StrategyDocument` DTO
- Deterministic across retries (brief_id stable, version explicit)
- Natural multi-versioning support (list_versions_by_brief)

---

## Implementation Artifacts

### 1. ORM Models
**File**: [aicmo/strategy/internal/models.py](aicmo/strategy/internal/models.py)

```python
class StrategyDocumentDB(Base):
    __tablename__ = 'strategy_document'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brief_id = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    # ... content fields
    
    __table_args__ = (
        UniqueConstraint('brief_id', 'version', name='uq_strategy_brief_version'),
    )
```

**Verification**:
- ✅ Single definition location: `aicmo/strategy/internal/models.py:21`
- ✅ No ForeignKey imports (zero cross-module dependencies)

### 2. Database Repository
**File**: [aicmo/strategy/internal/repositories_db.py](aicmo/strategy/internal/repositories_db.py)

**Key Methods**:
- `save(strategy: StrategyDocument) -> None`: Upsert via merge (idempotent)
- `get_strategy(brief_id: str, version: int) -> Optional[StrategyDocument]`: Single doc retrieval
- `list_versions_by_brief(brief_id: str) -> List[StrategyDocument]`: Multi-version listing (DESC order)

**Session Pattern**:
```python
with get_session() as session:
    session.merge(orm_model)
    session.commit()
```

### 3. In-Memory Repository (Parity)
**File**: [aicmo/strategy/internal/repositories_mem.py](aicmo/strategy/internal/repositories_mem.py)

**Constraint Simulation**:
```python
self._brief_versions: Dict[Tuple[str, int], StrategyDocument] = {}

def save(self, strategy: StrategyDocument) -> None:
    key = (strategy.brief_id, strategy.version)
    if key not in self._brief_versions:
        self._brief_versions[key] = strategy  # New insert
    else:
        self._brief_versions[key] = strategy  # Idempotent update
```

### 4. Adapter Integration
**File**: [aicmo/strategy/internal/adapters.py](aicmo/strategy/internal/adapters.py)

**Before**:
```python
class DefaultStrategyGenerator:
    def __init__(self):
        self._storage: Dict[Tuple[str, int], StrategyDocument] = {}
```

**After**:
```python
class DefaultStrategyGenerator:
    def __init__(self, repo: StrategyRepository):
        self._repo = repo
```

### 5. Composition Root Wiring
**File**: [aicmo/orchestration/composition/root.py](aicmo/orchestration/composition/root.py)

```python
if is_db_mode():
    self._strategy_repo = DatabaseStrategyRepo()
else:
    self._strategy_repo = InMemoryStrategyRepo()

self._strategy_generator = DefaultStrategyGenerator(self._strategy_repo)
self._strategy_approver = DefaultStrategyApprover(self._strategy_repo)
```

### 6. Alembic Migration
**File**: [db/alembic/versions/18ea2bd8b079_add_strategy_document_table.py](db/alembic/versions/18ea2bd8b079_add_strategy_document_table.py)

**Table Schema**:
```sql
CREATE TABLE strategy_document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id VARCHAR NOT NULL,
    version INTEGER NOT NULL,
    status VARCHAR NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    sections TEXT NOT NULL,
    metadata TEXT NOT NULL,
    
    CONSTRAINT uq_strategy_brief_version UNIQUE (brief_id, version)
);
CREATE INDEX ix_strategy_document_brief_id ON strategy_document (brief_id);
```

**Applied**: ✅ `alembic upgrade head` successful (18ea2bd8b079)

---

## Test Coverage

### Persistence Tests (20 total, all passing)

#### Memory Repository Tests (7)
**File**: [tests/persistence/test_strategy_repo_mem_roundtrip.py](tests/persistence/test_strategy_repo_mem_roundtrip.py)

1. ✅ `test_save_and_retrieve_single_strategy`: Create → save → get (exact match)
2. ✅ `test_save_overwrites_same_version`: Idempotent upsert on (brief_id, version)
3. ✅ `test_list_versions_by_brief`: Multi-version listing (DESC order)
4. ✅ `test_get_nonexistent_strategy`: Returns None for missing doc
5. ✅ `test_list_versions_empty_brief`: Returns [] for unknown brief
6. ✅ `test_save_multiple_versions`: Independent versions (v1, v2, v3)
7. ✅ `test_get_specific_version`: Version isolation (get v2 ≠ v1)

#### Database Repository Tests (8)
**File**: [tests/persistence/test_strategy_repo_db_roundtrip.py](tests/persistence/test_strategy_repo_db_roundtrip.py)

1. ✅ `test_save_and_retrieve_single_strategy`: Full roundtrip (create → commit → query)
2. ✅ `test_save_overwrites_same_version`: Upsert via merge (no duplicates)
3. ✅ `test_unique_constraint_enforced`: Direct SQL INSERT violation raises IntegrityError
4. ✅ `test_list_versions_by_brief`: Multi-version DESC ordering
5. ✅ `test_get_nonexistent_strategy`: Query returns None
6. ✅ `test_list_versions_empty_brief`: Query returns []
7. ✅ `test_rollback_on_error`: Session cleanup (error → rollback → clean state)
8. ✅ `test_no_mutation_on_read`: Read-only operations don't persist stale data

#### Parity Tests (5)
**File**: [tests/persistence/test_strategy_repo_parity_mem_vs_db.py](tests/persistence/test_strategy_repo_parity_mem_vs_db.py)

1. ✅ `test_save_and_get_parity`: Identical roundtrip behavior
2. ✅ `test_list_versions_parity`: Same ordering and filtering
3. ✅ `test_idempotent_save_parity`: Both handle duplicate (brief_id, version)
4. ✅ `test_nonexistent_get_parity`: Both return None for missing docs
5. ✅ `test_multiple_versions_parity`: Both isolate versions correctly

**Key Proof Points**:
- **Idempotency**: Saving same (brief_id, version) twice → no duplicates, latest content wins
- **Read-Only Safety**: GET/LIST don't persist uncommitted changes
- **Rollback Safety**: Errors clean up session state (no orphaned objects)
- **Mem/DB Parity**: Both implementations produce identical observable behavior

---

## Test Suite Results

```bash
# Enforcement Baseline (5 tests)
$ pytest tests/enforcement/ -q
5 passed in 0.70s ✅

# Contract Baseline (71 tests)
$ pytest tests/contracts/ -q
71 passed in 0.51s ✅

# New Persistence Tests (20 tests)
$ pytest tests/persistence/test_strategy_repo_* -v
20 passed in 33.00s ✅

# E2E Workflow Tests (8 tests)
$ pytest tests/e2e/ -q
8 passed in 0.26s ✅

TOTAL: 104/104 PASSING ✅
```

---

## Architectural Verification

### Rule: No Contract Changes
✅ **Verified**: Zero modifications to:
- `aicmo/strategy/ports/generator.py`
- `aicmo/strategy/ports/approver.py`
- `aicmo/strategy/ports/dtos.py`

### Rule: No Cross-Module FKs
✅ **Verified**: 
```bash
$ grep -n "ForeignKey" aicmo/strategy/internal/models.py
# Exit code 1 (zero matches)
```

### Rule: Module Boundary Respect
✅ **Verified**: StrategyDocumentDB only in strategy module:
```bash
$ grep -rn "class .*Strategy.*DB" aicmo
aicmo/strategy/internal/models.py:21:class StrategyDocumentDB(Base):
# Single definition, no cross-references
```

---

## Dual-Mode Configuration

**Environment Variable**: `AICMO_PERSISTENCE_MODE`

### In-Memory Mode (default)
```bash
export AICMO_PERSISTENCE_MODE=inmemory
python app.py  # Uses InMemoryStrategyRepo
```

### Database Mode
```bash
export AICMO_PERSISTENCE_MODE=db
alembic upgrade head  # Apply migrations
python app.py  # Uses DatabaseStrategyRepo
```

**Composition Logic**:
```python
def is_db_mode() -> bool:
    from aicmo.orchestration.composition.config import PersistenceConfig
    config = PersistenceConfig()
    return config.mode == "db"
```

---

## Git Change Summary

```bash
$ git diff --stat main
 aicmo/orchestration/composition/root.py                          |  12 ++++-
 aicmo/strategy/internal/adapters.py                              |  28 +++++-----
 aicmo/strategy/internal/models.py                                |  52 ++++++++++++++++++++
 aicmo/strategy/internal/repositories_db.py                       | 103 ++++++++++++++++++++++++++++++++++++++
 aicmo/strategy/internal/repositories_mem.py                      |  68 ++++++++++++++++++++++++
 db/alembic/versions/18ea2bd8b079_add_strategy_document_table.py |  45 +++++++++++++++++
 docs/persistence/PERSISTENCE_SURFACE_PHASE4_B.md                 |  28 +++++++++-
 tests/e2e/test_onboarding_to_strategy.py                         |   4 +-
 tests/persistence/test_strategy_repo_db_roundtrip.py             | 184 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/persistence/test_strategy_repo_mem_roundtrip.py            | 149 ++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/persistence/test_strategy_repo_parity_mem_vs_db.py         | 127 +++++++++++++++++++++++++++++++++++++++++++++

 11 files changed, 785 insertions(+), 15 deletions(-)
```

**Key Changes**:
- **3 new files**: models.py, repositories_db.py, repositories_mem.py
- **1 migration**: 18ea2bd8b079 (strategy_document table)
- **3 test files**: 20 new persistence tests
- **Updated**: adapters.py (protocol-based DI), root.py (dual-mode wiring)

---

## Completion Checklist

- [x] Step 5.0: Pre-flight gates (5+71+8 passing)
- [x] Step 5.1: Port/DTO inspection (no workflow_run_id)
- [x] Step 5.2: Persistence surface doc updated
- [x] Step 5.3: ORM models created (StrategyDocumentDB)
- [x] Step 5.4: DB repository implemented (DatabaseStrategyRepo)
- [x] Step 5.5: Memory repository with parity (InMemoryStrategyRepo)
- [x] Step 5.6: Adapter updates (protocol-based DI)
- [x] Step 5.7: Composition root wiring (dual-mode selection)
- [x] Step 5.8: Migration created and applied (18ea2bd8b079)
- [x] Step 5.9: Persistence tests (20 tests: 7 mem + 8 db + 5 parity)
- [x] Step 5.10: All gates passing (104/104 tests ✅)
- [x] Step 5.11: Evidence documentation (this file)

---

## Known Limitations

1. **No workflow_run_id**: Strategy module uses (brief_id, version) instead
   - Rationale: No workflow_run_id in ports/DTOs
   - Risk: Accepts deterministic idempotency key based on brief lineage

2. **Optimistic Locking**: Uses `merge()` for upserts (last-write-wins)
   - Rationale: No concurrent multi-user edit scenarios expected
   - Risk: Race condition on parallel version updates (mitigated by version counter design)

3. **Soft Delete**: Not implemented (no `deleted_at` column)
   - Rationale: Strategy documents immutable after approval
   - Risk: No audit trail for withdrawn strategies (future enhancement)

---

## Next Steps

**Ready for Step 6**: Production Module Persistence
- Follow same 11-step methodology
- Reuse repository patterns from Onboarding/Strategy
- Expected idempotency key: TBD (inspect Production ports first)

---

**Phase 4 Lane B Step 5 Status**: ✅ **COMPLETE**
