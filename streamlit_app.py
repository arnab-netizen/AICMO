import io
import json
import os
import zipfile
from typing import Any, Dict, Optional

import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")  # change if needed
TIMEOUT = int(os.getenv("API_TIMEOUT", "20"))

st.set_page_config(page_title="AICMO Dashboard", page_icon="✨", layout="wide")


def _api_url(path: str, base: Optional[str] = None) -> str:
    base = (base or API_BASE).rstrip("/")
    path = f"/{path.lstrip('/')}"
    return f"{base}{path}"


def _pretty_json(payload: Any) -> str:
    try:
        return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(payload)


def _http_client(timeout: int) -> httpx.Client:
    return httpx.Client(timeout=timeout, headers={"Accept": "application/json"})


def get_json(
    path: str, params: Optional[Dict[str, Any]] = None, *, base: Optional[str] = None
) -> Dict[str, Any]:
    url = _api_url(path, base)
    with _http_client(TIMEOUT) as client:
        resp = client.get(url, params=params or {})
        resp.raise_for_status()
        data = resp.json()
    return {"url": url, "ok": True, "data": data}


def post_json(
    path: str,
    payload: Dict[str, Any],
    *,
    base: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    url = _api_url(path, base)
    with _http_client(timeout or TIMEOUT) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    return {"url": url, "ok": True, "data": data}


def upload_zip(
    files: list[st.runtime.uploaded_file_manager.UploadedFile],  # type: ignore[attr-defined]
    upload_path: str = "/api/upload",
    *,
    base: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """Bundle uploaded files into a single in-memory ZIP and POST as multipart."""
    if not files:
        return {"ok": False, "error": "No files selected."}

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            # Sanitize arcname to avoid directory traversal
            arcname = os.path.basename(getattr(f, "name", "file"))
            zf.writestr(arcname, f.read())

    mem.seek(0)
    url = _api_url(upload_path, base)
    with _http_client(timeout or TIMEOUT) as client:
        files_mp = {"file": ("bundle.zip", mem.getvalue(), "application/zip")}
        resp = client.post(url, files=files_mp)
        resp.raise_for_status()
        data = resp.json()
    return {"url": url, "ok": True, "data": data}


# ===== UI =====
st.title("AICMO • Control Panel")

with st.sidebar:
    st.subheader("Settings")
    api_base_input = st.text_input("API Base", value=API_BASE, help="e.g., http://localhost:8000")
    timeout_input = st.number_input(
        "Timeout (seconds)", value=TIMEOUT, min_value=5, max_value=120, step=5
    )
    st.caption("These settings apply immediately to new requests.")

tab1, tab2, tab3, tab4 = st.tabs(["Health", "Jobs", "Upload", "Raw API"])

with tab1:
    st.header("Health Checks")
    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Ping /health"):
            try:
                result = get_json("/health", base=api_base_input)
                st.code(_pretty_json(result["data"]), language="json")
            except httpx.RequestError as e:
                st.error(f"Request error: {e}")
            except httpx.HTTPStatusError as e:
                st.error(f"HTTP {e.response.status_code}: {e.response.text}")

    with col_b:
        if st.button("DB /health/db"):
            try:
                result = get_json("/health/db", base=api_base_input)
                st.code(_pretty_json(result["data"]), language="json")
            except httpx.RequestError as e:
                st.error(f"Request error: {e}")
            except httpx.HTTPStatusError as e:
                st.error(f"HTTP {e.response.status_code}: {e.response.text}")

with tab2:
    st.header("Run a Job")
    prompt = st.text_area("Prompt / Brief", height=160, placeholder="Describe the task to AICMO…")
    endpoint = st.text_input(
        "Endpoint", value="/api/jobs/create", help="POST endpoint that accepts JSON {'prompt': ...}"
    )
    run = st.button("Submit Job")

    if run:
        if not prompt.strip():
            st.warning("Please enter a prompt.")
        else:
            payload: Dict[str, Any] = {"prompt": prompt}
            try:
                result = post_json(
                    endpoint, payload, base=api_base_input, timeout=int(timeout_input)
                )
                st.success("Job submitted.")
                st.code(_pretty_json(result["data"]), language="json")
            except httpx.RequestError as e:
                st.error(f"Request error: {e}")
            except httpx.HTTPStatusError as e:
                st.error(f"HTTP {e.response.status_code}: {e.response.text}")

with tab3:
    st.header("Bulk Upload (ZIP on the fly)")
    st.caption(
        "Select multiple files; they’ll be bundled into a ZIP and uploaded as multipart/form-data."
    )
    up_endpoint = st.text_input(
        "Upload endpoint", value="/api/upload", help="POST expects a 'file' multipart field."
    )
    selected = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=["txt", "md", "json", "csv", "png", "jpg", "jpeg", "pdf"],
    )
    if st.button("Upload as ZIP"):
        try:
            result = upload_zip(
                selected or [],
                upload_path=up_endpoint,
                base=api_base_input,
                timeout=int(timeout_input),
            )
            if result.get("ok"):
                st.success("Upload successful.")
                st.code(_pretty_json(result["data"]), language="json")
            else:
                st.warning(result.get("error", "Upload failed."))
        except httpx.RequestError as e:
            st.error(f"Request error: {e}")
        except httpx.HTTPStatusError as e:
            st.error(f"HTTP {e.response.status_code}: {e.response.text}")

with tab4:
    st.header("Raw API Console")
    method = st.selectbox("Method", ["GET", "POST"], index=0)
    raw_path = st.text_input("Path", value="/health")
    body_str = st.text_area("JSON Body (POST only)", value="{}", height=140)
    if st.button("Send"):
        try:
            if method == "GET":
                res = get_json(raw_path, base=api_base_input)
            else:
                try:
                    body = json.loads(body_str or "{}")
                except json.JSONDecodeError as e:
                    st.error(f"JSON parse error: {e}")
                    st.stop()
                res = post_json(raw_path, body, base=api_base_input, timeout=int(timeout_input))
            st.code(_pretty_json(res["data"]), language="json")
        except httpx.RequestError as e:
            st.error(f"Request error: {e}")
        except httpx.HTTPStatusError as e:
            st.error(f"HTTP {e.response.status_code}: {e.response.text}")
