# LINEAGE ENFORCEMENT HARDENING — FINDINGS & FIXES

**Date:** 2025-12-17  
**Session:** Production Risk Verification & Hardening  

---

## PHASE 0 — HARD VERIFICATION RESULTS

### 0.1 UI Approval Bypass Search ✅ VERIFIED SAFE

**Grep Results:**
```bash
grep -rn "\.status\s*=\s*ArtifactStatus" --include="*.py" . | grep -v "==" | grep -v "!="
```

**Findings:**
1. `artifact_store.py:368` - `artifact.status = ArtifactStatus.REVISED` inside `update_artifact()`
2. `artifact_store.py:429` - `artifact.status = ArtifactStatus.APPROVED` inside `approve_artifact()`
3. `artifact_store.py:457` - `artifact.status = ArtifactStatus.FLAGGED_FOR_REVIEW` inside `flag_artifact_for_review()`

**Classification:** ✅ ALL OK
- All three status mutations are inside `ArtifactStore` methods (enforcement boundary)
- No UI-side direct manipulation found
- No bypasses in operator_v2.py or other modules

**Verdict:** Status enforcement is correctly centralized in ArtifactStore

---

### 0.2 FAILED Path Verification ✅ VERIFIED (with 1 issue found)

**Analysis:**
- Searched all `return {"status": "FAILED", ...}` patterns in operator_v2.py
- All FAILED returns occur BEFORE backend calls:
  - `run_strategy_step` line 1836: Returns FAILED when lineage_errors exist, BEFORE backend call
  - `run_creatives_step` line 1944: Returns FAILED when lineage_errors exist, BEFORE backend call
  - `run_execution_step` line 2062: Returns FAILED when lineage_errors exist, BEFORE backend call

**Caller Analysis (aicmo_tab_shell):**
- Line 1423: Calls `result = runner(inputs)`
- Line 1427-1448: When `result.get("status") == "SUCCESS"`, attempts artifact storage
- **Key finding:** Line 1438 calls `store_artifact_from_backend()` which is NOT ArtifactStore
- This is legacy pattern that writes artifacts outside the store enforcement

**Issues Found:**
1. ⚠️ **RISK:** `aicmo_tab_shell` uses old `store_artifact_from_backend()` helper (line 389-450)
   - This bypasses ArtifactStore validation
   - Creates artifacts as plain dicts without lineage
   - However, NEW runner functions (strategy/creatives/execution) NOW create artifacts themselves via `artifact_store.create_artifact()`
   - The old pattern in aicmo_tab_shell is now redundant/conflicting

**Verdict:** FAILED paths don't write artifacts, BUT there's conflicting artifact creation patterns (old vs new)

---

### 0.3 Execution Job Dependency Mechanism ✅ IDENTIFIED

**Location:** `aicmo/ui/generation_plan.py`

**Key Structures:**
- `Job` dataclass (line 35): Has `job_type`, `depends_on`, `context`
- `build_generation_plan_from_checkboxes()` (line 116): Builds job DAG from UI selections
- Execution jobs (line 201-216):
  ```python
  # Execution depends on strategy + creatives
  execution_deps = list(strategy_job_ids.values()) + list(creative_job_ids.values())
  ```

**Job Types:**
- `CREATIVE_JOB_TYPES` (line 267): carousel_templates, reel_cover_templates, image_pack_prompts, video_scripts, thumbnails_banners, brand_kit_suggestions
- `EXECUTION_JOB_TYPES` (line 276): content_calendar, ig_posts, fb_posts, linkedin_posts, reels_scripts, hashtag_sets, email_sequence

**Current State:**
- ⚠️ **PROBLEM:** Generation plan always assumes execution depends on ALL creatives
- ⚠️ **PROBLEM:** No per-job-type "requires_creatives" flag
- ⚠️ **PROBLEM:** `run_execution_step` only checks "if has_creatives" (line 2053), treats as optional
- ⚠️ **MISSING:** No deterministic mapping of which execution jobs REQUIRE creative assets

**Verdict:** Dependency mechanism exists but lacks granular job-type rules

---

## RISKS IDENTIFIED

### Risk #1: Execution Lineage Is "Optional When Present" ⚠️ CONFIRMED
**Location:** `operator_v2.py:2026-2143` (run_execution_step)
**Problem:**
```python
# Line 2050: Always requires strategy
required_types = [ArtifactType.STRATEGY]

# Line 2053: Checks if creatives exists (optional)
has_creatives = st.session_state.get("artifact_creatives")

# Lines 2055-2059: Builds lineage with ONLY strategy (not creatives)
lineage, lineage_errors = artifact_store.build_source_lineage(
    client_id, engagement_id, required_types  # <-- Missing CREATIVES
)
```

**Impact:** Execution can be generated/approved without creatives even when jobs require visual assets

**Fix Required:** Make creatives requirement deterministic based on selected job types

---

### Risk #2: Approval Only Checks Lineage "If Present" ⚠️ CONFIRMED
**Location:** `artifact_store.py:397-408` (approve_artifact)
**Problem:**
```python
# Line 406: Only validates if lineage already exists
if artifact.source_lineage:
    lineage_ok, lineage_errors = self.assert_lineage_fresh(...)
    if not lineage_ok:
        raise ArtifactValidationError(lineage_errors, [])
```

**Impact:**
- If artifact created WITHOUT lineage (e.g., via old pattern), approval succeeds
- No enforcement that Strategy MUST have intake lineage
- No enforcement that Creatives MUST have strategy lineage
- No enforcement that Execution MUST have strategy (+ conditional creatives) lineage

**Fix Required:** Add `validate_required_lineage()` that runs BEFORE freshness check

---

### Risk #3: Legacy Artifact Creation Pattern Bypasses Store ⚠️ CONFIRMED
**Location:** `operator_v2.py:389-450, 1438` (store_artifact_from_backend + aicmo_tab_shell)
**Problem:**
- Old pattern: aicmo_tab_shell calls `store_artifact_from_backend()` which returns plain dict
- New pattern: Runner functions call `artifact_store.create_artifact()` with lineage
- **Conflict:** Both patterns may execute, creating duplicate/inconsistent artifacts

**Impact:** 
- Artifacts created via old pattern have no lineage
- Old artifacts bypass validation
- Session state may have inconsistent artifact versions

**Fix Required:** Remove legacy `store_artifact_from_backend()` call from aicmo_tab_shell

---

## HARDENING PLAN

### Fix #1: Deterministic Execution Creatives Dependency
**Approach:**
1. Add `CREATIVE_DEPENDENT_EXECUTION_JOBS` set in generation_plan.py
2. Implement `required_upstreams_for(artifact_type, selected_job_ids)` helper
3. Update `run_execution_step` to compute required_types dynamically
4. Update `build_source_lineage` to accept required_types as arg (already done ✅)

---

### Fix #2: Explicit Required Lineage Validation
**Approach:**
1. Add `validate_required_lineage(artifact)` to artifact_store.py
2. Define rules:
   - Strategy MUST have intake lineage
   - Creatives MUST have strategy lineage
   - Execution MUST have strategy lineage (+ creatives if jobs require)
3. Call from `approve_artifact()` BEFORE freshness check

---

### Fix #3: Remove Legacy Artifact Creation
**Approach:**
1. Remove `store_artifact_from_backend()` call from aicmo_tab_shell line 1438
2. Ensure runner functions handle ALL artifact creation
3. Add tests proving no artifacts created on FAILED

---

## NEXT ACTIONS

✅ ALL FIXES IMPLEMENTED AND TESTED

**Final Status:**
- ✅ Fix #1: Deterministic execution creatives dependency (via required_upstreams_for)
- ✅ Fix #2: Explicit required lineage validation (via validate_required_lineage)
- ✅ Fix #3: Removed legacy artifact creation (removed store_artifact_from_backend call)

**Test Results:**
- 40/40 tests passing (16 new hardening tests + 24 existing lineage tests)
- 0 skipped tests
- All proof commands green

**Files Changed:**
1. `aicmo/ui/generation_plan.py` - Added CREATIVE_DEPENDENT_EXECUTION_JOBS, required_upstreams_for()
2. `aicmo/ui/persistence/artifact_store.py` - Added validate_required_lineage(), enforced in approve_artifact()
3. `operator_v2.py` - Updated run_execution_step to use deterministic deps, removed legacy artifact creation
4. `tests/test_lineage_hardening.py` - 16 new tests proving all fixes work

**Commit Ready:** "Harden lineage enforcement: required upstream rules + no bypass + execution deps"
