# Canonical Streamlit Entry Point - VERDICT

## Finding

**Canonical Entry File**: `streamlit_pages/aicmo_operator.py`

### Evidence

1. **Scripts confirm usage**:
   - `scripts/launch_operator_ui.sh`: `streamlit run streamlit_pages/aicmo_operator.py`
   - `scripts/start_e2e_streamlit.sh`: `streamlit run /workspaces/AICMO/streamlit_pages/aicmo_operator.py`
   - `scripts/QUICK_START.sh`: recommends `streamlit run streamlit_pages/aicmo_operator.py`

2. **File structure**:
   - Main UI entry: 2874 lines (substantial Streamlit app)
   - Location: `/workspaces/AICMO/streamlit_pages/aicmo_operator.py`
   - Imports: `streamlit`, operator_services, creative directions, humanization, presets

3. **Navigation structure** (lines 1508-1550):
   - Uses `st.tabs()` to create main sections
   - Tabs defined: `["Command", "Projects", "War Room", "Gallery", "PM Dashboard", "Analytics", "Autonomy", "Control Tower"]`
   - Each tab is a `with` block receiving user interactions

4. **Other dashboard files**:
   - `streamlit_pages/operator_qc.py` - QC specialist UI (separate)
   - NOT used as primary entry in scripts

## Integration Strategy

Add a new tab to the main tabs list in `aicmo_operator.py` at line 1508:

**Before**:
```python
cmd_tab, projects_tab, warroom_tab, gallery_tab, pm_tab, analytics_tab, autonomy_tab, control_tab = st.tabs(
    ["Command", "Projects", "War Room", "Gallery", "PM Dashboard", "Analytics", "Autonomy", "Control Tower"]
)
```

**After**:
```python
cmd_tab, projects_tab, warroom_tab, gallery_tab, pm_tab, analytics_tab, autonomy_tab, control_tab, campaign_ops_tab = st.tabs(
    ["Command", "Projects", "War Room", "Gallery", "PM Dashboard", "Analytics", "Autonomy", "Control Tower", "Campaign Ops"]
)
```

Then add implementation inside `with campaign_ops_tab:` block.

## No Breaking Changes

- ✅ Existing tabs unmodified
- ✅ New tab added to end (non-breaking)
- ✅ All existing functionality preserved
- ✅ Campaign Ops is isolated to new tab

## Conclusion

**Safe to proceed** with adding Campaign Ops as new tab in canonical entry.
