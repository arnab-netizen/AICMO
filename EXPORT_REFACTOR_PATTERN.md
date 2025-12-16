# Export Section Refactor Pattern

## Problem
Streamlit widgets must be rendered at top-level on every run. You CANNOT create widgets inside conditionals that only execute sometimes.

## Solution Pattern

```python
# ========== TOP OF EXPORT SECTION ==========

# 1. Initialize state (always, idempotent)
st.session_state.setdefault("export_state", "IDLE")
st.session_state.setdefault("export_paths", None)

# 2. Button handler (only mutates state, never renders widgets)
if st.button("Export"):
    # Do work
    st.session_state.export_state = "PASS"  # or "FAIL"
    st.session_state.export_paths = {...}  # store serializable dict
    # NO st.download_button() HERE!

# 3. Top-level downloads (always executes on every run)
if st.session_state.export_state == "PASS" and st.session_state.export_paths:
    paths_dict = st.session_state.export_paths
    
    # Read file BEFORE passing to button
    with open(paths_dict["manifest_path"], "rb") as f:
        manifest_bytes = f.read()
    
    # NOW create button (this code runs on EVERY page load when state==PASS)
    st.download_button("Download Manifest", manifest_bytes, key="dl-manifest")
    
elif st.session_state.export_state == "FAIL":
    st.warning("Downloads blocked")
```

## Key Rules
1. State initialization: TOP of section, before any conditionals
2. Button handler: State mutation ONLY, zero rendering
3. Download rendering: TOP-LEVEL conditional that checks state
4. File I/O: Read bytes BEFORE st.download_button()
5. Keys: Stable, not f-strings with changing variables

## Why This Works
- Streamlit re-runs entire script on every interaction
- Session state persists across runs
- Download buttons exist in code that executes EVERY time (when state matches)
- Not hidden inside a `if st.button()` block that only runs once

## Application to AICMO
Replace lines 1555-1850 in streamlit_app.py with this pattern.
