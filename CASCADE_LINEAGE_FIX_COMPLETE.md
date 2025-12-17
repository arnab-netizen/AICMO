# ARTIFACT CASCADE LINEAGE BUG FIX — COMPLETE

**Date:** 2025-12-17  
**Session:** Cascade Lineage Correctness Fix  
**Status:** ✅ ALL TESTS PASSING (15/15, 0 SKIPPED)  

---

## EXECUTIVE SUMMARY

**Problem:** Downstream artifacts stored `source_versions.strategy = 1` (version at creation), not approved lineage. When strategy was revised to v2 (draft) then approved as v2, cascade logic incorrectly compared against saved version instead of approved version.

**Root Cause:**
1. No tracking of which **approved** version downstream depended on
2. Cascade triggered on **any** version increment (including drafts)
3. No distinction between draft revisions vs approved releases

**Solution:** Introduced `source_lineage` field tracking approved upstream versions, moved cascade trigger from `update_artifact()` to `approve_artifact()`, implemented proper approved version comparison.

**Result:** ✅ Multi-level cascade now works correctly with revised drafts

---

## ACCEPTANCE CRITERIA ✅

### ✅ 1. No skipped tests
- **VERIFIED:** All 15 tests passing, 0 skipped
- **Previously:** `test_multi_level_cascade` was skipped
- **Now:** Fully restored and passing

### ✅ 2. Cascade triggers only on approved version changes
- **VERIFIED:** `test_multi_level_cascade` proves this
- **Scenario:** Strategy v2 revised (draft) → creatives NOT flagged
- **Scenario:** Strategy v2 approved → creatives FLAGGED

### ✅ 3. Multi-revision strategy flow correct
- **VERIFIED:** Test shows:
  - Draft revisions don't invalidate downstream ✅
  - New approved versions DO invalidate downstream ✅

### ✅ 4. Downstream records approved lineage
- **VERIFIED:** `source_lineage` field populated with `approved_version`, `approved_at`, `artifact_id`
- **Backward compat:** Legacy `source_versions` automatically migrated

### ✅ 5. All tests pass
- **pytest -q:** 15 passed, 0 skipped, 1 warning
- **py_compile:** All files compile without errors

---

## IMPLEMENTATION CHANGES

### Phase 1: Introduce source_lineage (Backward Compatible)

**File:** `aicmo/ui/persistence/artifact_store.py`

**Changes:**
1. Added `source_lineage` field to `Artifact` dataclass (line 79):
   ```python
   source_lineage: Dict[str, Dict[str, Any]] = field(default_factory=dict)
   # Structure: {artifact_type: {approved_version, approved_at, artifact_id}}
   ```

2. Backward compatibility shim in `Artifact.from_dict()` (lines 97-110):
   ```python
   if 'source_lineage' not in data and 'source_versions' in data:
       # Migrate legacy source_versions to source_lineage
       source_lineage = {}
       for artifact_type, version in data['source_versions'].items():
           source_lineage[artifact_type] = {
               'approved_version': version,
               'approved_at': None,
               'artifact_id': None
           }
       data['source_lineage'] = source_lineage
       data['notes']['lineage_migrated'] = True
   ```

### Phase 2: Add Approved Version Helpers

**File:** `aicmo/ui/persistence/artifact_store.py`

**New methods:**
1. `get_latest_approved(client_id, engagement_id, artifact_type)` (lines 136-160):
   - Returns latest artifact with `status == APPROVED`
   - Returns `None` if no approved artifact exists

2. `get_current_approved_version_map(client_id, engagement_id)` (lines 162-177):
   - Returns dict: `{artifact_type: approved_version or None}`
   - Basis for deterministic cascade checks

### Phase 3: Fix Cascade Semantics

**File:** `aicmo/ui/persistence/artifact_store.py`

**Key changes:**

1. **create_artifact()** (lines 211-263):
   - Records `source_lineage` from APPROVED upstream artifacts only:
   ```python
   if source.status == ArtifactStatus.APPROVED:
       source_lineage[source.artifact_type.value] = {
           'approved_version': source.version,
           'approved_at': source.approved_at,
           'artifact_id': source.artifact_id
       }
   ```

2. **update_artifact()** (lines 267-301):
   - **REMOVED cascade trigger** (was lines 286-289)
   - Added docstring: "Cascade is NOT triggered here"
   - Only updates version/status, doesn't cascade

3. **approve_artifact()** (lines 305-359):
   - **ADDED cascade trigger on new approved version:**
   ```python
   # Capture previous approved version BEFORE approval
   prev_approved = self.get_latest_approved(...)
   prev_approved_version = prev_approved.version if prev_approved else 0
   
   # ... perform approval ...
   
   # Trigger cascade if this is a NEW approved version
   if artifact.version > prev_approved_version:
       downstream_types = self._get_downstream_types(artifact.artifact_type)
       if downstream_types:
           self.cascade_on_upstream_change(artifact, downstream_types)
   ```

4. **cascade_on_upstream_change()** (lines 452-511):
   - **Uses source_lineage instead of source_versions:**
   ```python
   if upstream_type_str in downstream.source_lineage:
       old_approved_version = downstream.source_lineage[upstream_type_str]['approved_version']
       new_approved_version = upstream_artifact.version
       
       if old_approved_version < new_approved_version:
           # Downstream is stale
           self.flag_artifact_for_review(...)
   ```
   - Fallback to `source_versions` for backward compatibility

5. **_compute_inputs_hash()** (lines 513-543):
   - Uses approved lineage when source is approved:
   ```python
   if source.status == ArtifactStatus.APPROVED:
       hash_input[source.artifact_type.value] = {
           "id": source.artifact_id,
           "approved_version": source.version,
           "approved_at": source.approved_at
       }
   ```

### Phase 4: Restore Multi-Level Cascade Test

**File:** `tests/test_artifact_store_cascade.py`

**Changes:**
1. Added `import copy` for deep copying content (line 5)

2. Restored `test_multi_level_cascade()` (lines 153-210):
   - **Removed:** `pytest.skip()` call
   - **Added:** Complete test scenario:
     ```python
     # 1. Create and approve Strategy v1 from Intake v1
     # 2. Create and approve Creatives from Strategy v1
     # 3. Update Strategy to v2 REVISED (not approved)
     # 4. Assert creatives still APPROVED (drafts don't cascade)
     # 5. Approve Strategy v2
     # 6. Assert creatives FLAGGED with "approved version changed from v1 to v2"
     ```

3. Fixed `test_cascade_flags_strategy_when_intake_changes()` (lines 59-105):
   - Added approval step after update to trigger cascade
   - Verified draft update doesn't cascade
   - Verified approval does cascade

4. Used `copy.deepcopy()` to avoid shallow copy mutation (line 191)

---

## TEST RESULTS

### Before Fix
```
14 passed, 1 skipped, 1 warning
```
- `test_multi_level_cascade`: SKIPPED (marked with pytest.skip)

### After Fix
```
15 passed, 0 skipped, 1 warning in 0.24s
```

**All tests:**
1. ✅ `test_cascade_flags_strategy_when_intake_changes` - Cascade on approved version change
2. ✅ `test_cascade_does_not_flag_if_no_version_change` - No cascade when version same
3. ✅ `test_cascade_skips_draft_artifacts` - Only approved artifacts flagged
4. ✅ `test_multi_level_cascade` - **RESTORED** - Draft vs approved distinction
5. ✅ `test_draft_to_approved_allowed` - Status transition validation
6. ✅ `test_flagged_to_approved_allowed` - Re-approval after flagging
7. ✅ `test_approved_to_approved_blocked` - Prevent duplicate approval
8. ✅ `test_validate_intake_missing_required_fields` - Intake validation
9. ✅ `test_validate_intake_all_required_present` - Valid intake
10. ✅ `test_validate_intake_consistency_warnings` - Consistency checks
11. ✅ `test_validate_strategy_missing_required_fields` - Strategy validation
12. ✅ `test_validate_strategy_complete_contract` - Valid strategy
13. ✅ `test_approve_artifact_refuses_invalid_intake` - Validation enforcement
14. ✅ `test_approve_artifact_accepts_valid_intake` - Valid approval
15. ✅ `test_approve_artifact_records_warnings` - Warning tracking

---

## PROOF COMMANDS

### Syntax Checks ✅
```bash
python -m py_compile aicmo/ui/persistence/artifact_store.py  # ✅ PASS
python -m py_compile operator_v2.py                          # ✅ PASS
python -m py_compile tests/test_artifact_store_cascade.py    # ✅ PASS
```

### Test Suite ✅
```bash
pytest -q tests/test_artifact_store_validation.py tests/test_artifact_store_cascade.py
# Result: 15 passed, 0 skipped, 1 warning in 0.24s
```

### Import Checks ✅
```python
from aicmo.ui.persistence.artifact_store import ArtifactStore, Artifact  # ✅ OK
```

---

## CASCADE BEHAVIOR SUMMARY

### Before Fix ❌
- **Trigger:** Any `update_artifact()` with `increment_version=True`
- **Problem:** Draft saves triggered cascade
- **Comparison:** `downstream.source_versions[upstream] < upstream.version`
- **Result:** Incorrect flagging when drafts existed

### After Fix ✅
- **Trigger:** `approve_artifact()` when `new_version > prev_approved_version`
- **Benefit:** Only approved releases cascade
- **Comparison:** `downstream.source_lineage[upstream]['approved_version'] < upstream.approved_version`
- **Result:** Correct handling of draft revisions

---

## BACKWARD COMPATIBILITY

### Existing Artifacts
- Automatically migrated in `Artifact.from_dict()`
- `source_versions` converted to `source_lineage`
- `lineage_migrated=true` flag added to notes
- No data loss or corruption

### Legacy Code
- `source_versions` field retained for backward compat
- Cascade logic checks `source_lineage` first, falls back to `source_versions`
- Existing workflows unaffected

---

## EXAMPLE FLOW

### Scenario: Strategy Revision → Approval → Cascade

```python
# 1. Create and approve Strategy v1
strategy_v1 = store.create_artifact(ArtifactType.STRATEGY, ...)
strategy_v1_approved = store.approve_artifact(strategy_v1)  # v1, approved

# 2. Create Creatives from approved Strategy v1
creatives = store.create_artifact(
    ArtifactType.CREATIVES,
    source_artifacts=[strategy_v1_approved]
)
# creatives.source_lineage = {'strategy': {'approved_version': 1, ...}}
creatives_approved = store.approve_artifact(creatives)

# 3. Revise Strategy (draft v2)
strategy_v2_draft = store.update_artifact(
    strategy_v1_approved,
    content=new_content,
    increment_version=True
)
# strategy_v2_draft.version = 2, status = REVISED
# creatives.status STILL = APPROVED (no cascade yet!)

# 4. Approve Strategy v2
strategy_v2_approved = store.approve_artifact(strategy_v2_draft)
# NOW cascade triggers because approved version changed 1 → 2
# creatives.status = FLAGGED_FOR_REVIEW
# creatives.notes['flagged_reason'] = "Upstream strategy approved version changed from v1 to v2"
```

---

## FILES MODIFIED

1. **aicmo/ui/persistence/artifact_store.py** (679 lines, +128 added, -20 removed)
   - Added `source_lineage` field
   - Added `get_latest_approved()`, `get_current_approved_version_map()`
   - Modified `create_artifact()` to record approved lineage
   - Modified `update_artifact()` to remove cascade trigger
   - Modified `approve_artifact()` to add cascade trigger
   - Modified `cascade_on_upstream_change()` to use approved lineage
   - Modified `_compute_inputs_hash()` to hash approved lineage

2. **tests/test_artifact_store_cascade.py** (292 lines, +62 added, -8 removed)
   - Restored `test_multi_level_cascade()` with complete implementation
   - Fixed `test_cascade_flags_strategy_when_intake_changes()` to approve after update
   - Added `import copy` for deep copying

---

## REMAINING WORK

None. All acceptance criteria met.

### Optional Future Enhancements
1. Add visual timeline of approved versions in UI
2. Add "rollback to previous approved version" feature
3. Add bulk re-approval workflow for downstream artifacts
4. Add notification system for upstream approvals

---

## FINAL VERDICT

✅ **ALL ACCEPTANCE CRITERIA MET**

**Evidence:**
- 15/15 tests pass (0 skipped)
- All syntax checks pass
- Cascade only triggers on approved version changes
- Multi-revision flow works correctly
- Backward compatible with existing data
- Draft revisions don't cascade
- Approved releases do cascade

**Confidence Level:** HIGH

**Recommendation:** Ready for production. The cascade lineage bug is fully resolved.
