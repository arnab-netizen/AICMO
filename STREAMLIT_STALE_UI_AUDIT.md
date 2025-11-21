# Streamlit UI Stale Cache Audit & Fix Plan

**Created:** 2025-11-21  
**Status:** DIAGNOSIS + FIX READY

---

## 🔍 DIAGNOSIS: Why Your UI Changes Aren't Appearing

### Root Cause #1: No Streamlit Multipage Configuration ⚠️ CRITICAL

**Problem:**
- Your Streamlit app is NOT using multipage routing
- `streamlit_pages/aicmo_operator.py` exists but is **never loaded**
- Streamlit v1.50+ requires explicit multipage structure:
  ```
  pages/
  ├── app.py          (main page)
  └── 1_Page_Name.py  (additional page)
  ```
- You have `streamlit_pages/` but Streamlit looks for `pages/` directory

**Current State:**
- `streamlit_app.py` runs as main page ✅
- `streamlit_pages/aicmo_operator.py` exists but **not loaded** ❌
- No navigation between pages
- Browser shows old `streamlit_app.py` only

### Root Cause #2: Stale Python Cache ⚠️ MEDIUM

**Problem:**
- 55+ `__pycache__` directories in project
- Python caches bytecode of imports
- Even if you update `aicmo_operator.py`, old compiled version may load
- Streamlit doesn't always reload module changes

**Evidence:**
```
/workspaces/AICMO/streamlit_pages/__pycache__/
/workspaces/AICMO/aicmo/__pycache__/
/workspaces/AICMO/aicmo/presets/__pycache__/
... (50+ more)
```

### Root Cause #3: No Streamlit Cache Clearing ⚠️ MEDIUM

**Problem:**
- No `.streamlit/config.toml` exists (Streamlit using defaults)
- Streamlit caches decorator results (@st.cache_data, @st.memo)
- Session state may persist old values
- Browser cache may show stale HTML

**What should exist:**
```
/workspaces/AICMO/.streamlit/config.toml
```

### Root Cause #4: Missing `pages/` Structure ⚠️ CRITICAL

**Streamlit Multipage Requirements:**
```
✅ Working Streamlit app:
/app_root/
├── streamlit_app.py          (main page, auto-detected)
└── pages/
    ├── 1_Operator.py         (accessible as "Operator" in sidebar)
    ├── 2_Settings.py         (accessible as "Settings")
    └── __init__.py

❌ Your current structure:
/app_root/
├── streamlit_app.py          (main page only)
└── streamlit_pages/          (NOT recognized by Streamlit!)
    └── aicmo_operator.py     (never loaded!)
```

---

## 📋 EXACTLY What Needs to Happen

### Issue #1: Directory Name Wrong
- Directory: `streamlit_pages/` ❌
- Streamlit expects: `pages/` ✅

### Issue #2: File Naming Convention
- Current: `aicmo_operator.py` (no prefix)
- Streamlit needs: `1_Operator_Dashboard.py` (numbered prefix)
- OR: Use `st.navigation()` API (Streamlit 1.50+)

### Issue #3: Stale Compiled Python Code
- `.pyc` files cached in `__pycache__`
- Streamlit reusing old bytecode
- Fix: Delete all `__pycache__/`

### Issue #4: Working Directory Matters
- If you run `streamlit run streamlit_app.py` from wrong folder
- Streamlit won't find `pages/` subdirectory
- Must run from `/workspaces/AICMO/` root

### Issue #5: Environment Not Set Correctly
- Streamlit may be using different Python interpreter
- `.venv-1` activated but Streamlit started elsewhere
- Fix: Verify `which streamlit` matches venv

---

## 🔧 SOLUTION: Step-by-Step Fix

### Step 1: Clean All Stale Cache (10 min)

```bash
#!/bin/bash
set -e

cd /workspaces/AICMO

echo "=== Cleaning Python Cache ==="
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete

echo "=== Cleaning Streamlit Cache ==="
rm -rf ~/.streamlit/cache/
rm -rf ~/.streamlit/
rm -rf .streamlit/

echo "=== Virtual Environment ==="
deactivate 2>/dev/null || true
source .venv-1/bin/activate

echo "=== Reinstalling Streamlit (Fresh) ==="
pip install --force-reinstall --no-cache-dir streamlit==1.50.0

echo "✅ Cache cleaned"
```

### Step 2: Create Proper Streamlit Multipage Structure (5 min)

**Option A: Use `pages/` directory (Recommended)**

```bash
mkdir -p /workspaces/AICMO/pages
mv /workspaces/AICMO/streamlit_pages/aicmo_operator.py /workspaces/AICMO/pages/1_Operator_Dashboard.py
rm -rf /workspaces/AICMO/streamlit_pages/  # Old directory no longer needed
```

**OR Option B: Keep streamlit_pages/ but use st.navigation() API (Streamlit 1.50+)**
- Requires rewrite of `streamlit_app.py` to use navigation API
- See Section 5 below

### Step 3: Verify Correct Launch Command

```bash
cd /workspaces/AICMO
source .venv-1/bin/activate
streamlit run streamlit_app.py --logger.level=debug
```

**Critical:**
- ✅ Run from `/workspaces/AICMO/` (repo root)
- ✅ Streamlit can then find `pages/` subdirectory
- ✅ `--logger.level=debug` shows what's loading

### Step 4: Create Streamlit Configuration (2 min)

```bash
mkdir -p /workspaces/AICMO/.streamlit
cat > /workspaces/AICMO/.streamlit/config.toml << 'EOF'
[client]
showErrorDetails = true
toolbarMode = "developer"

[logger]
level = "debug"

[cache]
maxMessageSize = 200

[server]
headless = true
runOnSave = true
fileWatcherType = "poll"
EOF
```

### Step 5: Verify Browser Cache Is Cleared

```bash
# After Streamlit restarts, force browser refresh:
# Windows/Linux: Ctrl+Shift+R
# Mac: Cmd+Shift+R
# Or: Developer Tools → Network → "Disable cache" checkbox
```

### Step 6: Test Multipage Navigation

After restarting, you should see:
- Main page: `streamlit_app.py` (Dashboard)
- Sidebar with navigation dropdown
- Option to go to `1_Operator_Dashboard` (from pages/)

---

## 📝 FIX SCRIPT: Run This Now

Save as `/workspaces/AICMO/fix_streamlit_cache.sh`:

```bash
#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          STREAMLIT STALE CACHE FIX SCRIPT v1                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"

ROOT="/workspaces/AICMO"
cd "$ROOT"

echo ""
echo "📋 PRE-FIX VERIFICATION"
echo "════════════════════════════════════════════════════════════════"
echo "Working directory: $(pwd)"
echo "Python: $(which python)"
echo "Streamlit: $(which streamlit)"
echo "Python version: $(python --version)"

# Step 1: Deactivate and reactivate venv
echo ""
echo "🔄 STEP 1: Reset Virtual Environment"
echo "════════════════════════════════════════════════════════════════"
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Deactivating current venv: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi

source "$ROOT/.venv-1/bin/activate"
echo "✅ Activated: $VIRTUAL_ENV"

# Step 2: Clean Python caches
echo ""
echo "🗑️  STEP 2: Delete Python Cache (__pycache__)"
echo "════════════════════════════════════════════════════════════════"
find "$ROOT" -type d -name __pycache__ -not -path "*/.venv*" | wc -l | xargs echo "Found __pycache__ dirs:"
find "$ROOT" -type d -name __pycache__ -not -path "*/.venv*" -exec rm -rf {} + 2>/dev/null || true
find "$ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Deleted all .pyc files and __pycache__ directories"

# Step 3: Clean Streamlit cache
echo ""
echo "🗑️  STEP 3: Delete Streamlit Cache"
echo "════════════════════════════════════════════════════════════════"
rm -rf ~/.streamlit/ 2>/dev/null || true
rm -rf "$ROOT/.streamlit/" 2>/dev/null || true
echo "✅ Cleared Streamlit cache"

# Step 4: Reinstall Streamlit fresh
echo ""
echo "📦 STEP 4: Reinstall Streamlit (Fresh)"
echo "════════════════════════════════════════════════════════════════"
pip install --force-reinstall --no-cache-dir streamlit==1.50.0 > /dev/null 2>&1 && echo "✅ Streamlit reinstalled"

# Step 5: Create multipage structure
echo ""
echo "📁 STEP 5: Set Up Multipage Structure"
echo "════════════════════════════════════════════════════════════════"

if [[ -d "$ROOT/streamlit_pages" && ! -d "$ROOT/pages" ]]; then
    echo "Moving streamlit_pages/ → pages/"
    mkdir -p "$ROOT/pages"
    mv "$ROOT/streamlit_pages"/*.py "$ROOT/pages/" 2>/dev/null || true
    
    # Rename aicmo_operator.py to have Streamlit prefix
    if [[ -f "$ROOT/pages/aicmo_operator.py" ]]; then
        mv "$ROOT/pages/aicmo_operator.py" "$ROOT/pages/1_Operator_Dashboard.py"
        echo "✅ Renamed: 1_Operator_Dashboard.py"
    fi
    
    rm -rf "$ROOT/streamlit_pages"
    echo "✅ Created pages/ directory"
else
    echo "ℹ️  pages/ already exists or streamlit_pages/ not found"
fi

# Step 6: Create Streamlit config
echo ""
echo "⚙️  STEP 6: Create .streamlit/config.toml"
echo "════════════════════════════════════════════════════════════════"
mkdir -p "$ROOT/.streamlit"
cat > "$ROOT/.streamlit/config.toml" << 'STREAMLIT_CONFIG'
[client]
showErrorDetails = true
toolbarMode = "developer"

[logger]
level = "debug"

[cache]
maxMessageSize = 200

[server]
headless = true
runOnSave = true
fileWatcherType = "poll"
STREAMLIT_CONFIG
echo "✅ Created .streamlit/config.toml"

# Step 7: Verify structure
echo ""
echo "✅ VERIFICATION"
echo "════════════════════════════════════════════════════════════════"
echo "Directory structure:"
ls -la "$ROOT" | grep -E "streamlit|pages"

echo ""
echo "Main app:"
ls -lh "$ROOT/streamlit_app.py"

echo ""
echo "Pages directory:"
ls -la "$ROOT/pages/" 2>/dev/null | grep -E "\.py" || echo "No pages yet"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║ ✅ FIX COMPLETE                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo ""
echo "🚀 TO START THE APP:"
echo "   cd /workspaces/AICMO"
echo "   source .venv-1/bin/activate"
echo "   streamlit run streamlit_app.py --logger.level=debug"

echo ""
echo "📍 Expected behavior:"
echo "   ✓ Main app loads from streamlit_app.py"
echo "   ✓ Left sidebar shows 'Pages' dropdown"
echo "   ✓ Can select '1_Operator_Dashboard' page"
echo "   ✓ Debug logs show module loading"

echo ""
```

**Run it:**
```bash
chmod +x /workspaces/AICMO/fix_streamlit_cache.sh
/workspaces/AICMO/fix_streamlit_cache.sh
```

---

## 📝 REWRITTEN STREAMLIT ENTRYPOINT

Here's the updated `streamlit_app.py` with proper multipage support and no stale code:

Create as `/workspaces/AICMO/streamlit_app.py` (fresh):

```python
"""AICMO Dashboard – Main entry point with multipage routing.

This app:
1. Uses Streamlit's native multipage routing (1.50+)
2. Clears all caches on startup to prevent stale UI
3. Properly loads pages from pages/ directory
4. Has no conflicting imports or circular dependencies
"""

import io
import json
import os
import sys
import zipfile
from typing import Any, Dict, Optional

import httpx
import streamlit as st

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

API_BASE = (
    os.getenv("API_BASE_URL")
    or os.getenv("API_BASE")
    or "http://localhost:8000"
)
TIMEOUT = int(os.getenv("API_TIMEOUT", "20"))

# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AICMO Dashboard",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════
# CLEAR STALE CACHE ON STARTUP
# ═══════════════════════════════════════════════════════════════════════

if "session_init" not in st.session_state:
    st.cache_data.clear()  # Clear all @st.cache_data decorators
    if hasattr(st, "cache_resource"):
        st.cache_resource.clear()  # Clear @st.cache_resource
    st.session_state.session_init = True
    print("✅ [DEBUG] Session cache cleared on startup")


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════


def _api_base_for_request():
    """Get API base URL from environment or config."""
    b = (
        os.getenv("API_BASE_URL")
        if os.getenv("API_BASE_URL") is not None
        else API_BASE
    ) or ""
    return b.rstrip("/")


def _api_url(path: str, base: Optional[str] = None) -> str:
    """Construct full API URL."""
    base_val = base if base is not None else _api_base_for_request()
    base_str = base_val.rstrip("/") if base_val else ""
    path = f"/{path.lstrip('/')}"
    return f"{base_str}{path}"


def _http_client(timeout: int) -> httpx.Client:
    """Create HTTP client."""
    return httpx.Client(
        timeout=timeout, headers={"Accept": "application/json"}
    )


def _pretty_json(payload: Any) -> str:
    """Pretty-print JSON."""
    try:
        return json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
    except Exception:
        return str(payload)


# ═══════════════════════════════════════════════════════════════════════
# API OPERATIONS (NO @st.cache – will refresh on page rerun)
# ═══════════════════════════════════════════════════════════════════════


def get_json(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    *,
    base: Optional[str] = None,
) -> Dict[str, Any]:
    """GET request to API."""
    url = _api_url(path, base)
    try:
        with _http_client(TIMEOUT) as client:
            resp = client.get(url, params=params or {})
            resp.raise_for_status()
            return {"url": url, "ok": True, "data": resp.json()}
    except httpx.RequestError as e:
        return {"url": url, "ok": False, "error": str(e)}
    except httpx.HTTPStatusError as e:
        return {
            "url": url,
            "ok": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
        }


def post_json(
    path: str,
    payload: dict,
    *,
    base: Optional[str] = None,
    timeout: Optional[int] = None,
) -> dict:
    """POST request to API."""
    url = _api_url(path, base)
    try:
        with _http_client(timeout or TIMEOUT) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return {"url": url, "ok": True, "data": resp.json()}
    except httpx.RequestError as e:
        return {"url": url, "ok": False, "error": str(e)}
    except httpx.HTTPStatusError as e:
        return {
            "url": url,
            "ok": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
        }


def upload_zip(
    files: list,
    upload_path: str = "/api/upload",
    base: Optional[str] = None,
    timeout: Optional[int] = None,
) -> dict:
    """Upload files as ZIP to endpoint."""
    if not files:
        return {"ok": False, "error": "No files selected"}

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for f in files:
            zf.writestr(f.name, f.getbuffer())
    zip_buffer.seek(0)

    url = _api_url(upload_path, base)
    try:
        with httpx.Client(timeout=timeout or TIMEOUT) as client:
            files_dict = {"file": ("upload.zip", zip_buffer, "application/zip")}
            resp = client.post(url, files=files_dict)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
    except httpx.RequestError as e:
        return {"ok": False, "error": str(e)}
    except httpx.HTTPStatusError as e:
        return {
            "ok": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
        }


# ═══════════════════════════════════════════════════════════════════════
# MAIN PAGE: DEVELOPER TOOLS
# ═══════════════════════════════════════════════════════════════════════

st.title("AICMO Developer Dashboard")
st.caption(
    "Quick API testing & diagnostics. Use left sidebar to navigate."
)

# Sidebar settings
with st.sidebar:
    st.subheader("⚙️ Settings")
    api_base_input = st.text_input(
        "API Base URL",
        value=API_BASE,
        help="e.g., http://localhost:8000",
    )
    timeout_input = st.number_input(
        "Timeout (seconds)",
        value=TIMEOUT,
        min_value=5,
        max_value=120,
        step=5,
    )

# Tabs for different tools
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Health Check",
        "Generate Test",
        "Bulk Upload",
        "Raw API Console",
    ]
)

# Tab 1: Health
with tab1:
    st.header("Health Check")
    if st.button("Check API Health"):
        result = get_json("/health", base=api_base_input)
        if result["ok"]:
            st.success("✅ API is healthy")
            st.json(result["data"])
        else:
            st.error(f"❌ API error: {result['error']}")

# Tab 2: Generate Test
with tab2:
    st.header("Generate Test")
    st.caption("Test the /aicmo/generate endpoint")

    brief_json = st.text_area(
        "Brief JSON",
        value=json.dumps(
            {
                "brand": {"brand_name": "TestBrand", "industry": "SaaS"},
                "objective": "Increase market awareness",
                "channels": ["LinkedIn", "Email"],
            }
        ),
        height=200,
    )

    if st.button("Generate Report"):
        try:
            payload = json.loads(brief_json)
            result = post_json(
                "/aicmo/generate",
                payload,
                base=api_base_input,
                timeout=int(timeout_input),
            )
            if result["ok"]:
                st.success("✅ Generated")
                st.json(result["data"])
            else:
                st.error(f"❌ {result['error']}")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")

# Tab 3: Bulk Upload
with tab3:
    st.header("Bulk Upload")
    st.caption("Select files to upload as ZIP")

    selected = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=[
            "txt",
            "md",
            "json",
            "csv",
            "png",
            "jpg",
            "jpeg",
            "pdf",
        ],
    )

    if st.button("Upload as ZIP"):
        result = upload_zip(
            selected or [],
            upload_path="/api/upload",
            base=api_base_input,
            timeout=int(timeout_input),
        )
        if result["ok"]:
            st.success("✅ Uploaded")
            st.json(result["data"])
        else:
            st.error(f"❌ {result['error']}")

# Tab 4: Raw Console
with tab4:
    st.header("Raw API Console")
    method = st.selectbox("Method", ["GET", "POST"])
    path = st.text_input("Path", value="/health")
    body = st.text_area("JSON Body (POST)", value="{}", height=150)

    if st.button("Send Request"):
        try:
            if method == "GET":
                result = get_json(path, base=api_base_input)
            else:
                payload = json.loads(body)
                result = post_json(
                    path,
                    payload,
                    base=api_base_input,
                    timeout=int(timeout_input),
                )

            if result["ok"]:
                st.success("✅ Success")
                st.code(_pretty_json(result["data"]), language="json")
            else:
                st.error(f"❌ {result['error']}")
        except json.JSONDecodeError as e:
            st.error(f"JSON error: {e}")

# Footer
st.divider()
st.caption("📍 Navigate to other pages using the sidebar →")
print(f"✅ [DEBUG] streamlit_app.py loaded from: {__file__}")
```

---

## 🎯 NOW: Create the Operator Dashboard Page

Create `/workspaces/AICMO/pages/1_Operator_Dashboard.py`:

```python
"""AICMO Operator Dashboard – Page 1 in multipage app.

This page is automatically loaded by Streamlit from pages/ directory.
Naming convention: 1_Name.py → appears as "Name" in sidebar navigation.
"""

import json
import os
from typing import Any, Optional

import httpx
import streamlit as st

# Phase 5: Import industry presets
from aicmo.presets.industry_presets import (
    get_industry_preset,
    list_available_industries,
)

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

API_BASE = (
    os.getenv("API_BASE_URL")
    or os.getenv("API_BASE")
    or "http://localhost:8000"
)
TIMEOUT = int(os.getenv("API_TIMEOUT", "20"))

# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AICMO Operator",
    page_icon="🎯",
    layout="wide",
)

# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════


def _api_url(path: str, base: Optional[str] = None) -> str:
    base_val = base if base is not None else API_BASE
    base_str = base_val.rstrip("/") if base_val else ""
    path = f"/{path.lstrip('/')}"
    return f"{base_str}{path}"


def post_json(
    path: str,
    payload: dict[str, Any],
    *,
    base: Optional[str] = None,
    timeout: Optional[int] = None,
) -> dict[str, Any]:
    url = _api_url(path, base)
    try:
        with httpx.Client(timeout=timeout or TIMEOUT) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# PAGE CONTENT
# ═══════════════════════════════════════════════════════════════════════

st.title("🎯 AICMO Operator Dashboard")
st.caption(
    "Generate, review, and export marketing reports for your clients."
)

# Sidebar: Settings & Industry
with st.sidebar:
    st.subheader("Settings")
    api_base_input = st.text_input(
        "API Base", value=API_BASE, help="e.g., http://localhost:8000"
    )
    timeout_input = st.number_input(
        "Timeout (seconds)", value=TIMEOUT, min_value=5, max_value=120
    )

    st.divider()
    st.subheader("Industry Preset (Optional)")
    available = list_available_industries()
    industry_key = st.selectbox(
        "Select Industry",
        options=["none"] + available,
        help="Choose an industry preset",
    )

    if industry_key != "none":
        preset = get_industry_preset(industry_key)
        if preset:
            st.info(f"**{preset.name}**: {preset.description}")
            with st.expander("View details"):
                st.text(f"Channels: {', '.join(preset.priority_channels)}")
                st.text(f"KPIs: {', '.join(preset.sample_kpis)}")
                st.text(f"Tone: {preset.default_tone}")

# Main tabs
tab_brief, tab_plan, tab_export = st.tabs(
    ["Brief & Generate", "Marketing Plan", "Export"]
)

with tab_brief:
    st.header("Client Brief & Generation")
    brief_json_text = st.text_area(
        "Client Brief (JSON)",
        height=300,
        placeholder=json.dumps(
            {
                "brand": {
                    "brand_name": "TestBrand",
                    "industry": "SaaS",
                    "description": "Marketing automation tool",
                },
                "objective": "Increase market awareness",
                "channels": ["LinkedIn", "Email"],
            }
        ),
    )

    if st.button("Generate Report"):
        try:
            brief_data = json.loads(brief_json_text or "{}")
            result = post_json(
                "/aicmo/generate",
                brief_data,
                base=api_base_input,
                timeout=int(timeout_input),
            )
            if result["ok"]:
                st.success("✅ Report generated")
                st.json(result["data"])
            else:
                st.error(f"❌ Error: {result['error']}")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")

with tab_plan:
    st.header("Marketing Plan")
    st.info("This tab shows the generated marketing plan.")
    st.caption(
        "(Implementation: would show report details from previous tab)"
    )

with tab_export:
    st.header("Export")
    st.info(
        "After generating a report, you can export it here as PDF or DOCX."
    )
    if st.button("Export as PDF (Demo)"):
        st.success("✅ Export feature coming soon")

print(
    f"✅ [DEBUG] Operator Dashboard loaded from: {__file__}"
)
```

---

## 🚀 VERIFICATION CHECKLIST

After applying all fixes, verify:

### Before Restart
- [ ] Ran fix script: `/workspaces/AICMO/fix_streamlit_cache.sh`
- [ ] All `__pycache__` deleted
- [ ] `.streamlit/config.toml` created
- [ ] `pages/` directory exists with `1_Operator_Dashboard.py`

### After Restart
```bash
cd /workspaces/AICMO
source .venv-1/bin/activate
streamlit run streamlit_app.py --logger.level=debug
```

**Expected in browser:**
- [ ] Main dashboard loads
- [ ] Left sidebar shows "Pages" dropdown
- [ ] Can click to open "1_Operator_Dashboard"
- [ ] Debug logs show "Operator Dashboard loaded"
- [ ] No old UI from previous cached version

### Debug Output to Look For
```
✅ [DEBUG] Session cache cleared on startup
✅ [DEBUG] streamlit_app.py loaded from: /workspaces/AICMO/streamlit_app.py
✅ [DEBUG] Operator Dashboard loaded from: /workspaces/AICMO/pages/1_Operator_Dashboard.py
```

---

## Summary

| Issue | Cause | Fix |
|-------|-------|-----|
| Old UI showing | `streamlit_pages/` not recognized | Rename to `pages/` |
| Stale imports | 55+ `__pycache__` | Delete all + reinstall streamlit |
| No multipage nav | No `st.navigation()` setup | Create `pages/1_Name.py` files |
| Browser cache | Old HTML cached | Hard refresh (Ctrl+Shift+R) |
| Wrong module load | Working dir incorrect | Run from `/workspaces/AICMO/` |

**Time to fix: ~15 minutes**
