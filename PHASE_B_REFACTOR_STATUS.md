# Phase B Export Refactor - Status Report

## Summary

**Status**: 🟡 INCOMPLETE - Core refactor applied, but downloads still not rendering due to navigation issue

**What Was Accomplished**:
✅ Removed all rendering code from export button handler (Streamlit lifecycle fix)
✅ Removed prohibited `st.rerun()` call that was preventing downloads from appearing
✅ Fixed state storage to use serializable dict instead of live RuntimePaths object
✅ Fixed indentation errors in top-level downloads section
✅ Top-level downloads now correctly read from `st.session_state.e2e_export_paths`
✅ Updated negative test to use session-scoped violation checkbox
✅ Added comprehensive debug markers

**What Remains Broken**:
❌ Downloads not rendering in Playwright tests
❌ Root cause appears to be navigation issue - Export page may not be loading

---

## Architecture Changes Applied

### 1. State Mutation Only in Button Handler

**Before** (WRONG - violated Streamlit lifecycle):
```python
if st.button("Generate export file"):
    # Do export work
    paths = get_runtime_paths()
    st.session_state.e2e_export_state = "PASS"
    
    # ❌ WRONG: Rendering inside button handler
    st.markdown("### Downloads")
    st.download_button("Manifest", manifest_bytes)
    st.download_button("PDF", pdf_bytes)
```

**After** (CORRECT):
```python
if st.button("Generate export file"):
    # Do export work
    paths = get_runtime_paths()
    st.session_state.e2e_export_state = "PASS"
    
    # ✅ Store paths as serializable dict
    st.session_state.e2e_export_paths = {
        "manifest_path": str(paths.manifest_path),
        "validation_path": str(paths.validation_path),
        "section_map_path": str(paths.section_map_path),
        "downloads_dir": str(paths.downloads_dir)
    }
    # NO rendering here - top-level will handle it
```

### 2. Top-Level Downloads (Always Executes)

**Location**: `streamlit_app.py` lines 1728-1860

**Pattern**:
```python
# Outside button handler, at same indentation level as button
if e2e_mode:
    export_state = st.session_state.get("e2e_export_state", "IDLE")
    paths_dict = st.session_state.get("e2e_export_paths")
    
    if export_state == "PASS" and paths_dict:
        manifest_path = Path(paths_dict["manifest_path"])
        validation_path = Path(paths_dict["validation_path"])
        
        # Read files and create downloads
        st.download_button("Manifest", manifest_path.read_bytes())
        st.download_button("Validation", validation_path.read_bytes())
```

**Key Points**:
- Code executes on EVERY script run (not just on button click)
- Checks session state to determine what to render
- Uses paths stored in session state, NOT `get_runtime_paths()`

### 3. Removed st.rerun()

**Critical Fix**: Line ~1724 previously called `st.rerun()` after export, which prevented the rest of the script (including top-level downloads) from executing in the same run. This violated the user's "Non-Negotiable" rule: **"No st.rerun() for control flow"**.

---

## Current Blocking Issue

### Problem: Export Page Not Rendering

**Symptoms**:
- Test clicks "Export" navigation link
- Test sees export button and clicks it
- State stays "IDLE" forever (never changes to "PASS")
- No debug output appears in logs
- Button click is registered (trigger_value: true in logs)

**Root Cause Hypothesis**:
The Export section is conditional on `elif nav == "Export":` (line 1396). If the navigation isn't properly set to "Export", the entire Export section (including button handler) never renders.

**Evidence**:
1. Navigation is via `st.radio("Navigation", [...])` at line 734
2. Default index=0 means "Dashboard" is selected by default
3. Test uses `page.getByText('Export', { exact: true }).first().click()`
4. This should click the radio label, but may not register correctly

**Debug Markers Added**:
- `data-testid="e2e-current-nav"` - Shows which page is active
- Debug print statements at navigation and export sections
- Stub report creation markers

### Recommended Next Steps

1. **Verify Navigation**:
   ```typescript
   // In Playwright test
   await page.locator('input[type="radio"][value="Export"]').check();
   // OR
   await page.locator('label').filter({ hasText: /^Export$/ }).click();
   ```

2. **Check Session State**:
   Add to test after clicking Export link:
   ```typescript
   const navMarker = await page.locator('[data-testid="e2e-current-nav"]').textContent();
   console.log(`Navigation state: ${navMarker}`);
   expect(navMarker).toContain('NAV: Export');
   ```

3. **Verify Stub Report**:
   The stub report is created at line 1410 INSIDE `elif nav == "Export":`. If nav isn't "Export", the stub won't exist, and the button won't render (line 1561 checks `if not st.session_state.generated_report`).

---

## Files Modified

### streamlit_app.py
- **Lines 1407-1420**: Stub report creation (now with debug output)
- **Lines 1561-1564**: Added debug output for report existence check
- **Lines 1571-1578**: Button handler with debug markers  
- **Lines 1655-1665**: Removed all rendering code from PASS handler
- **Lines 1669-1673**: Removed rendering from FAIL handler
- **Lines 1675-1677**: Removed rendering from ERROR handler
- **Lines 1724**: Removed `st.rerun()` call
- **Lines 1728-1860**: Fixed top-level downloads to use session state
- **Lines 1744-1831**: Fixed indentation and removed `get_runtime_paths()` calls

### tests/playwright/e2e_strict/phase_b_negative.spec.ts
- **Lines 35-51**: Updated to use session-scoped violation checkbox instead of env var

---

## Test Status

### Positive Test (phase_b_positive.spec.ts)
**Status**: ❌ FAILING
**Failure Point**: State never changes from IDLE to PASS
**Likely Cause**: Export page not loading due to navigation issue

### Negative Test (phase_b_negative.spec.ts)  
**Status**: ⏸️ NOT RUN
**Expected**: Should work once navigation is fixed

---

## Proof Commands (Step 5 - Not Yet Executed)

```bash
# 1. Restart Streamlit
pkill -9 -f "streamlit" || true
cd /workspaces/AICMO && env \
  AICMO_E2E_MODE=1 \
  AICMO_E2E_DIAGNOSTICS=1 \
  AICMO_PROOF_RUN=1 \
  AICMO_PERSISTENCE_MODE=db \
  AICMO_TEST_SEED=12345 \
  AICMO_E2E_ARTIFACT_DIR=/workspaces/AICMO/.artifacts/e2e \
  streamlit run streamlit_app.py \
  --server.port 8501 \
  --server.headless true > /tmp/streamlit.log 2>&1 &

# 2. Wait for health
sleep 15 && curl http://localhost:8501/_stcore/health

# 3. Run positive test
npx playwright test tests/playwright/e2e_strict/phase_b_positive.spec.ts \
  --reporter=line --timeout=75000

# 4. Run negative test (without restart)
npx playwright test tests/playwright/e2e_strict/phase_b_negative.spec.ts \
  --reporter=line --timeout=75000

# 5. Check artifacts
find .artifacts/e2e -maxdepth 6 -type f | sort

# 6. Verify parity
./.venv/bin/python scripts/check_manifest_parity.py
```

---

## Next Session Action Items

1. **Fix Navigation Issue** (CRITICAL):
   - Debug why Export page isn't loading in tests
   - Consider using more explicit Playwright selectors for radio buttons
   - Add visible nav indicator in E2E mode for debugging

2. **Verify Refactor**:
   - Once navigation works, confirm button handler executes
   - Verify state changes from IDLE → PASS
   - Confirm downloads appear

3. **Run Proof Execution**:
   - Execute Step 5 commands
   - Capture green test output
   - Document artifacts and parity results

4. **Complete Step 6**:
   - Create final status document with evidence
   - Include screenshots of green tests
   - Document manifest parity results

---

## Architecture Reference

### Correct Streamlit State Machine Pattern

```python
# STEP 1: Initialize state (always, top-level)
st.session_state.setdefault("export_state", "IDLE")
st.session_state.setdefault("export_paths", None)

# STEP 2: Button handler (state mutation ONLY)
if st.button("Export"):
    # Do work
    st.session_state.export_state = "PASS"
    st.session_state.export_paths = {"manifest": str(path)}
    # NO st.download_button() here!

# STEP 3: Top-level downloads (always executes, conditional rendering)
if st.session_state.export_state == "PASS" and st.session_state.export_paths:
    paths_dict = st.session_state.export_paths
    manifest_bytes = Path(paths_dict["manifest"]).read_bytes()
    st.download_button("Download", manifest_bytes, key="stable-key")
```

### Why This Works

1. **Streamlit Lifecycle**: Script reruns completely on every interaction
2. **Session State Persists**: Values survive across reruns
3. **Widgets Must Be Top-Level**: Downloads must exist in code that executes EVERY time state matches
4. **No st.rerun() Needed**: State machine drives rendering naturally through script flow

---

## Session Notes

- **Token Budget**: Exhausted during deep debugging of navigation issue
- **Root Problem**: Export page conditional on nav state, but nav change not registering in tests
- **Architecture**: Successfully refactored to correct Streamlit pattern
- **Testing**: Blocked on navigation - once fixed, rest should work

**Recommendation**: Start next session by fixing navigation selector in test or adding explicit nav debugging to app.
