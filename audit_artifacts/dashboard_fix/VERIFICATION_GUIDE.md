# Dashboard Fix - Verification Guide

## Fix Summary

| Fix # | Issue | Location | Change | Status |
|-------|-------|----------|--------|--------|
| 1 | Campaign Ops tab not visible | streamlit_pages/aicmo_operator.py | Feature flag + tab wiring (already correct) | ✅ OK |
| 2 | Autonomy tab session crash | streamlit_pages/aicmo_operator.py lines 997-1038, 1173-1186 | Wrap in `with get_session()` context manager | ✅ FIXED |
| 3 | Metrics crash (invalid enum) | aicmo/operator_services.py line 61 | Remove "ENGAGED" from LeadStatus filter | ✅ FIXED |
| 4 | Panel isolation | streamlit_pages/aicmo_operator.py | Add try/except around tab rendering | ✅ FIXED |

---

## Verification Steps

### Step 1: Syntax Check

```bash
python -m py_compile streamlit_pages/aicmo_operator.py aicmo/operator_services.py
```

**Expected**: No output (success)

---

### Step 2: Verify Fix #3 (Metrics enum)

**Check**: LeadStatus enum values

```bash
python3 << 'PYEOF'
from aicmo.cam.domain import LeadStatus
print("Valid LeadStatus values:")
for status in LeadStatus:
    print(f"  - {status.value}")
print("\n✅ ENGAGED should NOT be in this list")
PYEOF
```

**Expected Output**:
```
Valid LeadStatus values:
  - NEW
  - ENRICHED
  - CONTACTED
  - REPLIED
  - QUALIFIED
  - ROUTED
  - LOST
  - MANUAL_REVIEW

✅ ENGAGED should NOT be in this list
```

---

### Step 3: Verify Fix #3 (Query still works)

```bash
grep -n "LeadDB.status.in_" aicmo/operator_services.py
```

**Expected**:
```
Line 61: LeadDB.status.in_(["CONTACTED"])
```

**NOT** `["CONTACTED", "ENGAGED"]`

---

### Step 4: Verify Fix #2 (Session context manager)

```bash
grep -n "with get_session()" streamlit_pages/aicmo_operator.py | grep -E "line (997|1001|1173)"
```

**Expected**: Both problematic lines now have `with get_session() as session:` pattern

```bash
grep -B 2 "session.execute" streamlit_pages/aicmo_operator.py | head -20
```

**Expected**: All `session.execute()` calls are inside a `with` block

---

### Step 5: Verify Fix #2 (No orphaned session.close() calls)

```bash
grep -n "session.close()" streamlit_pages/aicmo_operator.py
```

**Expected**: No `session.close()` calls in the fallback DB access section (lines 997-1050)

(Note: It's handled automatically by the context manager)

---

### Step 6: Verify Fix #4 (Panel isolation)

```bash
grep -n "# DASH_FIX_START" streamlit_pages/aicmo_operator.py
```

**Expected**: Multiple markers showing try/except blocks added

```
1527: # DASH_FIX_START - Fix #4: Add panel isolation
1851: # DASH_FIX_START - Fix #4: Isolate Autonomy tab
1054: # DASH_FIX_START - Fix #2: Wrap session in context manager
...
```

---

### Step 7: Verify Campaign Ops Tab Rendering Code (Fix #1)

```bash
grep -n "campaign_ops_tab" streamlit_pages/aicmo_operator.py
```

**Expected**: Tab is conditionally created and rendered:
```
1513: tab_list.append("Campaign Ops")
1519: cmd_tab, projects_tab, ..., campaign_ops_tab = tabs
1522: campaign_ops_tab = None
2050: if campaign_ops_tab is not None:
2051:    with campaign_ops_tab:
```

This logic is **CORRECT**. Campaign Ops tab is shown if and only if `AICMO_CAMPAIGN_OPS_ENABLED=true`

---

### Step 8: Manual UI Verification (When Running Streamlit)

1. **Start Streamlit**:
   ```bash
   streamlit run launch_operator.py
   ```

2. **Verify Command Tab**:
   - Tab loads without error
   - Shows metrics (Triage Needed, Approvals Pending, Execution Health)
   - No red error boxes

3. **Verify Autonomy Tab**:
   - Tab loads without "_GeneratorContextManager" error
   - Shows AOL status
   - No "AttributeError: 'session' has no attribute 'execute'" error

4. **Verify Metrics Load**:
   - Dashboard loads metrics without "invalid input value for enum leadstatus: ENGAGED" error
   - High-intent leads count displays correctly
   - No PostgreSQL enum errors

5. **Verify Campaign Ops Tab** (if enabled):
   - Tab appears in navigation if `AICMO_CAMPAIGN_OPS_ENABLED=true`
   - Tab loads without error
   - If error occurs, it shows in expander, doesn't crash page

6. **Test Error Isolation**:
   - If any single tab errors, others still work
   - Error appears in red box with debug expander
   - Other tabs remain accessible

---

## Evidence Files

All fixes are wrapped in `# DASH_FIX_START` and `# DASH_FIX_END` markers:

### Fix #2 Evidence
- **File**: streamlit_pages/aicmo_operator.py
- **Lines**: 
  - 1001-1047 (first session context manager)
  - 1175-1186 (second session context manager)
- **Marker**: `# DASH_FIX_START - Fix #2: Wrap session in context manager`

### Fix #3 Evidence
- **File**: aicmo/operator_services.py
- **Lines**: 55-64
- **Marker**: `# DASH_FIX_START - Fix #3: Remove invalid enum value "ENGAGED"`

### Fix #4 Evidence
- **File**: streamlit_pages/aicmo_operator.py
- **Lines**: 
  - 1527-1596 (Command tab isolation)
  - 1851-1859 (Autonomy tab isolation)
- **Marker**: `# DASH_FIX_START - Fix #4: Add panel isolation`

---

## Rollback Instructions

If needed, revert fixes:

```bash
# Revert aicmo_operator.py (Fixes #2 and #4)
git checkout streamlit_pages/aicmo_operator.py

# Revert operator_services.py (Fix #3)
git checkout aicmo/operator_services.py
```

---

## Known Limitations

- **Campaign Ops visibility**: Controlled by `AICMO_CAMPAIGN_OPS_ENABLED` environment variable. Ensure it's set to "true" for tab to appear.
- **Autonomy tab**: Requires backend service or `AICMO_ENABLE_DANGEROUS_UI_OPS=1` for direct DB fallback
- **Metrics**: Now filters by valid LeadStatus values only; may show lower "high-intent" count if "ENGAGED" was being used as proxy

---

## Files Changed

1. **streamlit_pages/aicmo_operator.py** (2 fixes: #2 and #4)
   - Added 3 session context manager fixes
   - Added 2 tab isolation try/except blocks
   - All wrapped in DASH_FIX markers

2. **aicmo/operator_services.py** (1 fix: #3)
   - Changed LeadStatus filter from `["CONTACTED", "ENGAGED"]` to `["CONTACTED"]`
   - Added DASH_FIX marker explaining the change

---

## Test Result: ✅ ALL SYNTAX VALID

No compilation errors detected.

```
$ python -m py_compile streamlit_pages/aicmo_operator.py aicmo/operator_services.py
(no output = success)
```

EOF
```

cat /workspaces/AICMO/audit_artifacts/dashboard_fix/VERIFICATION_GUIDE.md
