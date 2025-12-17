# WIRING MAP: Artifact Creation Sites in operator_v2.py

## Current State (Before Lineage Wiring)

### Intake Tab (✅ Already uses ArtifactStore)
- **Line 1750:** `artifact_store.create_artifact(ArtifactType.INTAKE, ...)` 
- **Handler:** `run_intake_step()` at line ~1600
- **Status:** ALREADY creates artifact with proper source_lineage (no upstream deps)

### Strategy Tab (❌ NEEDS WIRING)
- **Line 1805:** `run_strategy_step()` - Currently just calls backend `/aicmo/generate`
- **Current behavior:** Returns markdown, no artifact creation
- **Required:** Must create Strategy artifact with `source_lineage.intake`
- **Blocker check:** Must verify intake is approved before allowing generation

### Creatives Tab (❌ NEEDS WIRING)
- **Line ~1900:** `run_creatives_step()` - Currently just calls backend
- **Current behavior:** Returns markdown/manifest, no artifact creation
- **Required:** Must create Creatives artifact with `source_lineage.strategy` (+ optional intake)
- **Blocker check:** Must verify strategy is approved

### Execution Tab (❌ NEEDS WIRING)
- **Line ~2000:** `run_execution_step()` - Currently just calls backend
- **Current behavior:** Returns schedule, no artifact creation
- **Required:** Must create Execution artifact with `source_lineage.strategy` + `source_lineage.creatives` (if creative jobs selected)
- **Blocker check:** Must verify strategy approved, creatives approved if needed

### System Tab (✅ Test code only)
- **Lines 2812-2921:** Test artifact creation in self-test suite
- **Status:** No changes needed (test code)

## Wiring Required

### Phase 1: Add Store Helpers (artifact_store.py)
1. `build_source_lineage(client_id, engagement_id, required_types) -> dict | errors`
2. `assert_lineage_fresh(lineage, client_id, engagement_id) -> (ok, errors)`
3. `ensure_lineage_on_artifact(artifact) -> (ok, errors)` - validation helper

### Phase 2: Wire Runner Functions (operator_v2.py)
1. **run_strategy_step()** (line 1805):
   - Check intake approved (gate)
   - After backend generation, create Strategy artifact
   - Attach source_lineage.intake from latest approved
   
2. **run_creatives_step()** (line ~1900):
   - Check strategy approved (gate)
   - After backend generation, create Creatives artifact
   - Attach source_lineage.strategy (+ intake if available)

3. **run_execution_step()** (line ~2000):
   - Check strategy approved (gate)
   - Check creatives approved if creative jobs selected
   - After backend generation, create Execution artifact
   - Attach source_lineage.strategy + source_lineage.creatives

### Phase 3: Validation (artifact_store.py)
1. Add `validate_strategy_contract()` enhancement (already exists, just ensure lineage check)
2. Add `validate_creatives_content()` - check lineage present
3. Add `validate_execution_content()` - check lineage present

### Phase 4: Approval Flow (Already implemented in artifact_store.py)
- `approve_artifact()` already validates content
- Need to add lineage validation to content validators

## Dependencies
- No source_versions usage found in operator_v2.py ✅
- All artifact creation centralized in ArtifactStore ✅
- Approval flow already wired through store ✅
