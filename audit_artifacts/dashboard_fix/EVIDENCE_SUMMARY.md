# Dashboard Fix - Evidence Summary

## Issue 1: Campaign Ops Tab Not Visible

**Evidence Found:**
- Lines 1508-1523: Campaign Ops IS wired into nav
  - `AICMO_CAMPAIGN_OPS_WIRING_START/END` markers present
  - Code adds "Campaign Ops" to tab_list at line 1513
  - Creates `campaign_ops_tab` variable
  - BUT line 1522 shows `campaign_ops_tab = None` ALWAYS

**Problem:** After adding tab to list, code immediately sets `campaign_ops_tab = None` regardless of the condition

**Fix Required:** Properly assign tab from tabs tuple

---

## Issue 2: Autonomy Tab - _GeneratorContextManager Session Crash

**Evidence Found:**
- Line 948: Function `_render_autonomy_tab()` defined
- Lines 1003-1178: Multiple calls to `session.execute()`
  - Line 1004: `lease = session.execute(lease_stmt).scalar_one_or_none()`
  - Line 1008: `flags_row = session.execute(flags_stmt).scalar_one_or_none()`
  - Line 1012: `last_tick = session.execute(last_tick_stmt).scalar_one_or_none()`
  - Line 1178: `logs = session.execute(log_stmt).scalars().all()`

**Problem:** Session is obtained but NOT in context manager; likely returns _GeneratorContextManager

**Fix Required:** Wrap session usage in `with` block

---

## Issue 3: Metrics Crash - Invalid Enum Value "ENGAGED" for leadstatus

**Evidence Found:**
- Line 61 in `aicmo/operator_services.py`: 
  ```python
  LeadDB.status.in_(["CONTACTED", "ENGAGED"])
  ```

- LeadStatus enum in `aicmo/cam/domain.py` lines 23-32:
  ```python
  class LeadStatus(str, Enum):
      NEW = "NEW"
      ENRICHED = "ENRICHED"
      CONTACTED = "CONTACTED"
      REPLIED = "REPLIED"
      QUALIFIED = "QUALIFIED"
      ROUTED = "ROUTED"
      LOST = "LOST"
      MANUAL_REVIEW = "MANUAL_REVIEW"
  ```

**Problem:** "ENGAGED" does NOT exist in LeadStatus enum, only "CONTACTED" exists

**Solution:** Remove "ENGAGED" from the filter - it's not a valid enum value

---

## Tab Navigation Structure

Lines 1508-1523 show the tab architecture:
```python
tab_list = ["COMMAND", "PROJECTS", "WAR ROOM", ...]
if AICMO_CAMPAIGN_OPS_ENABLED:
    tab_list.append("Campaign Ops")
    
tabs = st.tabs(tab_list)

if AICMO_CAMPAIGN_OPS_ENABLED:
    cmd_tab, projects_tab, warroom_tab, gallery_tab, pm_tab, analytics_tab, autonomy_tab, control_tab, campaign_ops_tab = tabs
else:
    campaign_ops_tab = None
```

Issue: campaign_ops_tab is ALWAYS set to None at line 1522 when unpacking, regardless of the condition!

