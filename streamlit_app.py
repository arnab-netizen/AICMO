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
import zipfile
from typing import Any, Dict, Optional

import httpx
import streamlit as st

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

API_BASE = os.getenv("API_BASE_URL") or os.getenv("API_BASE") or "http://localhost:8000"
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
    b = (os.getenv("API_BASE_URL") if os.getenv("API_BASE_URL") is not None else API_BASE) or ""
    return b.rstrip("/")


def _api_url(path: str, base: Optional[str] = None) -> str:
    """Construct full API URL."""
    base_val = base if base is not None else _api_base_for_request()
    base_str = base_val.rstrip("/") if base_val else ""
    path = f"/{path.lstrip('/')}"
    return f"{base_str}{path}"


def _http_client(timeout: int) -> httpx.Client:
    """Create HTTP client."""
    return httpx.Client(timeout=timeout, headers={"Accept": "application/json"})


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
st.caption("Quick API testing & diagnostics. Use left sidebar to navigate.")

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
