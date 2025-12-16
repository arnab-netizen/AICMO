# Dashboard Fixes - Implementation Plan

## Fix 1: Campaign Ops Tab Visibility

**Status**: Tab logic is already correct (lines 1508-1523)

**Actual Problem**: Unknown - may be environment variable issue

**Verification Needed**: Check if AICMO_CAMPAIGN_OPS_ENABLED is set to "true"

**Fix**: Add explicit error handling to show why tab is hidden if feature flag is off

---

## Fix 2: Autonomy Tab - Session Context Manager

**Location**: `streamlit_pages/aicmo_operator.py`, lines 997 and 1174

**Problem**: 
- Line 997: `session = get_session()` - NOT wrapped in `with` block
- Line 1174: `session = get_session()` - NOT wrapped in `with` block
- Lines 1004, 1008, 1012, 1178: `session.execute()` called on potentially invalid session

**Root Cause**: `get_session()` returns a context manager (generator), not a direct Session object

**Expected Error**: "_GeneratorContextManager object has no attribute execute"

**Fix**: Wrap session usage in `with get_session() as session:` block

**Affected Lines**:
- Lines 997-1180: Entire fallback DB access block needs context manager

---

## Fix 3: Metrics Crash - Invalid Enum "ENGAGED"

**Location**: `aicmo/operator_services.py`, line 61

**Problem**: Filter uses `["CONTACTED", "ENGAGED"]` but enum only has "CONTACTED"

**LeadStatus Enum Values** (aicmo/cam/domain.py):
- NEW
- ENRICHED
- CONTACTED ✓ (valid)
- REPLIED
- QUALIFIED
- ROUTED
- LOST
- MANUAL_REVIEW

**Error**: Database rejects "ENGAGED" as invalid enum value

**Fix**: Remove "ENGAGED" from filter - use only "CONTACTED"

**Rationale**: "ENGAGED" doesn't exist in the system; "CONTACTED" is the correct status for leads with contact activity

---

## Fix 4: Panel Isolation (Prevent whole dashboard crash)

**Location**: `streamlit_pages/aicmo_operator.py`, tab rendering sections

**Current State**: If one tab errors, it may crash the whole dashboard

**Fix**: Add try/except around each major tab section to show error without breaking other tabs

**Affected Sections**:
- Line 1525+: Command tab
- Line 1585+: Projects tab
- Line 1693+: War Room tab
- Lines 1842, 1846, 1936: Autonomy, Control Tower, PM Dashboard tabs

---

## Implementation Order

1. **Fix #3 First** (Metrics enum) - Simplest, affects data layer only
2. **Fix #2 Next** (Autonomy session) - Fixes runtime crash
3. **Fix #4** (Panel isolation) - Prevents future similar crashes
4. **Fix #1 Last** (Campaign Ops visibility) - Already working, just needs verification

