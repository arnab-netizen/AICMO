# Phase 4 Lane C: HARD DELETE Implementation Strategy

## Overview

This document outlines the complete implementation of DB-backed saga compensation with HARD DELETE semantics. The goal is to replace in-memory compensation with actual database row deletion.

## Current State vs. Target State

### Current (Lane B)
```python
def compensate_brief(inputs: dict) -> dict:
    # ❌ Only updates in-memory state
    state.compensations_applied.append("brief_normalized_reverted")
    return {}
```

### Target (Lane C)
```python
def compensate_brief(inputs: dict) -> dict:
    # ✅ Deletes actual database rows
    with get_session() as session:
        # Delete in reverse dependency order
        session.execute(text("DELETE FROM onboarding_intake WHERE brief_id = :brief_id"), 
                       {"brief_id": str(state.brief_id)})
        session.execute(text("DELETE FROM onboarding_brief WHERE id = :brief_id"),
                       {"brief_id": str(state.brief_id)})
        session.commit()
    
    state.compensations_applied.append("brief_deleted")
    return {}
```

## Implementation Steps

### Step 1: Add workflow_run_id tracking ✅ COMPLETE

**Status**: Migration created, table exists

**Table**: `workflow_runs`
- Primary key: `id` (workflow_run_id)
- Tracks: status, timestamps, errors, concurrency claims
- Purpose: Provides scope for DELETE operations

### Step 2: Modify WorkflowState to include workflow_run_id

**File**: `/workspaces/AICMO/aicmo/orchestration/internal/workflows/client_to_delivery.py`

**Change**:
```python
@dataclass
class WorkflowState:
    """Tracks workflow execution state."""
    workflow_run_id: str  # NEW: DB-backed run identifier
    brief_id: BriefId
    strategy_id: StrategyId = None
    draft_id: DraftId = None
    package_id: DeliveryPackageId = None
    qc_passed: bool = False
    compensations_applied: list[str] = None
```

### Step 3: Create WorkflowRun at workflow start

**File**: `/workspaces/AICMO/aicmo/orchestration/internal/workflows/client_to_delivery.py`

**Change in `execute()` method**:
```python
def execute(self, input_dto: WorkflowInputDTO) -> SagaResultDTO:
    saga_id = SagaId(f"workflow_{input_dto.brief_id}_{int(datetime.utcnow().timestamp())}")
    workflow_run_id = str(saga_id)  # Use saga_id as workflow_run_id
    
    # Create DB-backed workflow run
    with get_session() as session:
        run_repo = WorkflowRunRepository(session)
        run_repo.create_run(
            brief_id=input_dto.brief_id,
            workflow_run_id=workflow_run_id,
            metadata={"force_qc_fail": input_dto.force_qc_fail}
        )
        session.commit()
    
    # Initialize state with workflow_run_id
    state = WorkflowState(
        workflow_run_id=workflow_run_id,
        brief_id=input_dto.brief_id
    )
    self._state[saga_id] = state
    
    # ... rest of workflow execution
```

### Step 4: Implement HARD DELETE in compensation functions

**File**: `/workspaces/AICMO/aicmo/orchestration/internal/workflows/client_to_delivery.py`

**Changes in `_register_actions()` method**:

#### 4.1: compensate_package

```python
def compensate_package(inputs: dict) -> dict:
    """Delete delivery package and artifacts from database."""
    if not state.package_id:
        return {}
    
    with get_session() as session:
        # Delete in reverse dependency order (children first)
        session.execute(
            text("DELETE FROM delivery_artifacts WHERE package_id = :package_id"),
            {"package_id": str(state.package_id)}
        )
        session.execute(
            text("DELETE FROM delivery_packages WHERE id = :package_id"),
            {"package_id": str(state.package_id)}
        )
        session.commit()
    
    state.compensations_applied.append(f"package_{state.package_id}_deleted")
    state.package_id = None
    return {}
```

#### 4.2: compensate_qc

```python
def compensate_qc(inputs: dict) -> dict:
    """Delete QC results and issues from database."""
    if not state.draft_id:
        return {}
    
    with get_session() as session:
        # Delete QC data associated with this draft
        # First get qc_result_id(s) for this draft
        result = session.execute(
            text("SELECT id FROM qc_results WHERE draft_id = :draft_id"),
            {"draft_id": str(state.draft_id)}
        )
        qc_result_ids = [row[0] for row in result.fetchall()]
        
        # Delete issues first (children)
        for result_id in qc_result_ids:
            session.execute(
                text("DELETE FROM qc_issues WHERE result_id = :result_id"),
                {"result_id": result_id}
            )
        
        # Delete results (parents)
        session.execute(
            text("DELETE FROM qc_results WHERE draft_id = :draft_id"),
            {"draft_id": str(state.draft_id)}
        )
        session.commit()
    
    state.compensations_applied.append("qc_evaluation_deleted")
    state.qc_passed = False
    return {}
```

#### 4.3: compensate_draft

```python
def compensate_draft(inputs: dict) -> dict:
    """Delete production drafts, bundles, and assets from database."""
    if not state.draft_id:
        return {}
    
    with get_session() as session:
        # Delete in reverse dependency order
        # First get bundle_id(s) for this draft
        result = session.execute(
            text("SELECT bundle_id FROM production_bundles WHERE draft_id = :draft_id"),
            {"draft_id": str(state.draft_id)}
        )
        bundle_ids = [row[0] for row in result.fetchall()]
        
        # Delete assets first (deepest children)
        for bundle_id in bundle_ids:
            session.execute(
                text("DELETE FROM production_bundle_assets WHERE bundle_id = :bundle_id"),
                {"bundle_id": bundle_id}
            )
        
        # Delete bundles (children)
        session.execute(
            text("DELETE FROM production_bundles WHERE draft_id = :draft_id"),
            {"draft_id": str(state.draft_id)}
        )
        
        # Delete drafts (parents)
        session.execute(
            text("DELETE FROM production_drafts WHERE draft_id = :draft_id"),
            {"draft_id": str(state.draft_id)}
        )
        session.commit()
    
    state.compensations_applied.append(f"draft_{state.draft_id}_deleted")
    state.draft_id = None
    return {}
```

#### 4.4: compensate_strategy

```python
def compensate_strategy(inputs: dict) -> dict:
    """Delete strategy document from database."""
    if not state.strategy_id:
        return {}
    
    with get_session() as session:
        session.execute(
            text("DELETE FROM strategy_document WHERE id = :strategy_id"),
            {"strategy_id": str(state.strategy_id)}
        )
        session.commit()
    
    state.compensations_applied.append(f"strategy_{state.strategy_id}_deleted")
    state.strategy_id = None
    return {}
```

#### 4.5: compensate_brief

```python
def compensate_brief(inputs: dict) -> dict:
    """Delete onboarding brief and intake from database."""
    with get_session() as session:
        # Delete in reverse dependency order (intake first, then brief)
        session.execute(
            text("DELETE FROM onboarding_intake WHERE brief_id = :brief_id"),
            {"brief_id": str(state.brief_id)}
        )
        session.execute(
            text("DELETE FROM onboarding_brief WHERE id = :brief_id"),
            {"brief_id": str(state.brief_id)}
        )
        session.commit()
    
    state.compensations_applied.append("brief_deleted")
    return {}
```

### Step 5: Update workflow_run status on completion/failure

**File**: `/workspaces/AICMO/aicmo/orchestration/internal/workflows/client_to_delivery.py`

**Change in `execute()` method**:
```python
# Execute saga
result = self._saga.start_saga(saga_id, steps)

# Update workflow_run status
with get_session() as session:
    run_repo = WorkflowRunRepository(session)
    if result.success:
        run_repo.update_status(
            workflow_run_id=workflow_run_id,
            status="COMPLETED",
            completed_at=datetime.now(timezone.utc)
        )
    else:
        run_repo.update_status(
            workflow_run_id=workflow_run_id,
            status="COMPENSATED" if result.compensated else "FAILED",
            error=result.error
        )
    session.commit()

return result
```

## Deletion Order Safety

**Critical Rule**: Always delete children before parents to respect foreign key constraints (even though we use logical FKs, not database FKs).

**Order**:
1. delivery_artifacts → delivery_packages
2. qc_issues → qc_results
3. production_bundle_assets → production_bundles → production_drafts
4. strategy_document
5. onboarding_intake → onboarding_brief

## Testing Strategy

### Unit Tests
- Test each compensation function individually
- Verify rows are deleted from database
- Verify state is updated correctly

### Integration Tests
- Test full workflow compensation on failure
- Verify all rows are deleted in correct order
- Verify no orphan rows remain

### Negative Safety Tests
- Create workflow A (completes successfully)
- Create workflow B (fails and compensates)
- Verify workflow A's rows are untouched

### Idempotency Tests
- Run compensation twice
- Verify second run is idempotent (no errors)

### Concurrency Tests
- Start two workflows simultaneously
- Verify each has its own workflow_run_id
- Verify compensation only deletes its own rows

## Performance Considerations

1. **Batch Deletes**: Where possible, use single DELETE statements with WHERE clauses
2. **Connection Pooling**: Reuse database connections
3. **Transaction Boundaries**: Keep transactions small (per-step, not per-workflow)
4. **Indexes**: Ensure indexes exist on foreign key columns (draft_id, bundle_id, etc.)

## Migration Checklist

- [x] Create workflow_runs table
- [x] Add composite index for concurrency
- [ ] Update WorkflowState with workflow_run_id
- [ ] Create WorkflowRun at workflow start
- [ ] Implement HARD DELETE in compensate_package
- [ ] Implement HARD DELETE in compensate_qc
- [ ] Implement HARD DELETE in compensate_draft
- [ ] Implement HARD DELETE in compensate_strategy
- [ ] Implement HARD DELETE in compensate_brief
- [ ] Update workflow_run status on completion/failure
- [ ] Add unit tests for each compensation function
- [ ] Add integration tests for full workflow compensation
- [ ] Add negative safety tests
- [ ] Add idempotency tests
- [ ] Add concurrency tests
- [ ] Run performance benchmarks
- [ ] Update documentation

## Exit Criteria

- [ ] 9/9 DB compensation tests pass (currently 0/9)
- [ ] E2E passes twice back-to-back in DB mode
- [ ] Zero orphans proven by DB queries after compensation
- [ ] Negative test passes (unrelated rows survive)
- [ ] Idempotency test passes (second run succeeds)
- [ ] Concurrency test passes (parallel workflows isolated)
- [ ] Performance <5x slowdown or <10s (currently 33x)

## Implementation Files

### Core Files
1. `/workspaces/AICMO/aicmo/orchestration/internal/models.py` ✅ Created
2. `/workspaces/AICMO/aicmo/orchestration/internal/repository.py` ✅ Created
3. `/workspaces/AICMO/aicmo/orchestration/internal/workflows/client_to_delivery.py` 🚧 Needs Update
4. `/workspaces/AICMO/db/alembic/versions/bb0885d50953_add_workflow_runs_table_for_saga_run_.py` ✅ Created

### Test Files
1. `/workspaces/AICMO/tests/e2e/test_db_qc_fail_compensation.py` 🚧 Needs Update
2. `/workspaces/AICMO/tests/e2e/test_db_delivery_fail_compensation.py` 🚧 Needs Update

## Next Actions

1. Implement all compensation functions with HARD DELETE
2. Update workflow execution to create/update workflow_runs
3. Run tests and verify all 9 compensation tests pass
4. Add negative safety test
5. Add idempotency and concurrency tests
6. Optimize performance
7. Document final results in evidence file
