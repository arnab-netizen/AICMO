# LINEAGE WIRING STATUS

## Completed (Commit A - 4ba2f05)
✅ artifact_store.py with source_lineage field
✅ Cascade only on approved version changes
✅ build_source_lineage() helper
✅ assert_lineage_fresh() helper
✅ Lineage validation in approve_artifact()
✅ Test suite (24 tests passing)

## To Complete (Commit B)
### 1. operator_v2.py Changes

#### run_strategy_step() (line ~1805)
**BEFORE:** Just calls backend, returns markdown
**AFTER:** 
- Call build_source_lineage([INTAKE]) before generation
- If errors, return FAILED with "Upstream intake not approved"
- After backend success, create Strategy artifact with lineage
- Return artifact_id in meta for downstream use

#### run_creatives_step() (line ~1900) 
**BEFORE:** Just calls backend
**AFTER:**
- Call build_source_lineage([STRATEGY]) before generation
- If errors, return FAILED with "Upstream strategy not approved"
- After backend success, create Creatives artifact with lineage
- Return artifact_id in meta

#### run_execution_step() (line ~2000)
**BEFORE:** Just calls backend
**AFTER:**
- Determine required upstream: STRATEGY always, CREATIVES if creative jobs
- Call build_source_lineage(required_types)
- If errors, return FAILED with specific missing upstream
- After backend success, create Execution artifact with lineage
- Return artifact_id in meta

### 2. Session State Keys
After artifact creation, store artifact in session:
- `artifact_strategy`
- `artifact_creatives` 
- `artifact_execution`

### 3. UI Messaging
Gate already enhanced to show:
- "strategy (draft - must be approved)"
- "strategy (STALE: Upstream intake changed from v1 to v2)"

No additional UI changes needed - artifact enforcement already wired in approval button.

## Implementation Plan
Since backend generation logic is NOT using artifacts yet (it's just calling `/aicmo/generate`), we'll:
1. Keep backend calls as-is (generate content)
2. After successful generation, create artifact with lineage
3. Store artifact in session state
4. Approval button (already wired) will validate lineage on approve

This is a "bolt-on" approach - we wire artifacts around existing generation without refactoring the entire backend pipeline.
