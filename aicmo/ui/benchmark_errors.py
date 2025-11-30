from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

import streamlit as st


_ERROR_RE = re.compile(
    r"Benchmark validation failed for pack '([^']+)'.*?Failing sections:\s*\[(.*?)\]",
    re.IGNORECASE | re.DOTALL,
)


def parse_benchmark_error(detail: str) -> Tuple[str | None, List[str]]:
    """
    Parse the BenchmarkEnforcementError detail string and extract:

    - pack_key
    - list of failing section_ids

    If parsing fails, returns (None, []).
    """
    match = _ERROR_RE.search(detail or "")
    if not match:
        return None, []

    pack_key = match.group(1).strip()
    raw_list = match.group(2).strip()

    # raw_list is like: "'overview', 'audience_segments'"
    if not raw_list:
        return pack_key, []

    sections: List[str] = []
    for chunk in raw_list.split(","):
        chunk = chunk.strip().strip("'").strip('"')
        if chunk:
            sections.append(chunk)

    return pack_key, sections


def render_benchmark_error_ui(
    *,
    error_detail: str,
    request_payload: Dict[str, Any] | None = None,
    retry_callback_key: str = "retry_generate",
) -> None:
    """
    Render a friendly error UI for benchmark failures.

    - Shows a clear error summary.
    - Lists failing section IDs, if available.
    - Provides:
        - "Try again" button (triggers a rerun)
        - "Download debug log" button with error + payload
    """
    pack_key, sections = parse_benchmark_error(error_detail)

    st.error("Report failed quality checks after 2 attempts.")

    with st.expander("Technical details", expanded=False):
        st.write("**Backend error detail:**")
        st.code(error_detail or "(no detail)", language="text")

        if pack_key:
            st.write(f"**Pack:** `{pack_key}`")

        if sections:
            st.write("**Failing sections:**")
            st.code("\n".join(sections), language="text")
        else:
            st.write("No specific sections were parsed from the error message.")

    col_retry, col_spacer, col_download = st.columns([1, 0.2, 1])

    # Try again button – simply triggers a rerun of the Streamlit script.
    # The caller is expected to re-call the backend when the app reruns.
    with col_retry:
        if st.button("🔁 Try again", key=f"{retry_callback_key}_button"):
            # Streamlit rerun pattern – let the outer logic re-execute.
            st.rerun()

    # Download debug log – pack error + payload into a small text file.
    with col_download:
        debug_text = _build_debug_log(error_detail, pack_key, sections, request_payload)
        st.download_button(
            label="📥 Download debug log",
            data=debug_text.encode("utf-8"),
            file_name=f"aicmo_debug_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
        )


def _build_debug_log(
    error_detail: str,
    pack_key: str | None,
    sections: List[str],
    request_payload: Dict[str, Any] | None,
) -> str:
    buf = io.StringIO()
    buf.write("AICMO Benchmark Failure Debug Log\n")
    buf.write("================================\n\n")
    buf.write(f"Timestamp (UTC): {datetime.utcnow().isoformat()}Z\n\n")

    buf.write("Error detail:\n")
    buf.write(error_detail or "(no detail)\n")
    buf.write("\n")

    if pack_key:
        buf.write(f"Pack key: {pack_key}\n")

    if sections:
        buf.write("Failing sections:\n")
        for sid in sections:
            buf.write(f"  - {sid}\n")
        buf.write("\n")

    if request_payload:
        buf.write("Original request payload (truncated):\n")
        # keep it simple; you can improve later if needed
        import json

        try:
            buf.write(json.dumps(request_payload, indent=2)[:8000])
            buf.write("\n")
        except Exception:
            buf.write("(Could not serialise payload as JSON)\n")

    return buf.getvalue()
