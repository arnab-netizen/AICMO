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

API_BASE = os.getenv("API_BASE_URL") or os.getenv("API_BASE") or "http://localhost:8000"
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
st.caption("Generate, review, and export marketing reports for your clients.")

# Sidebar: Settings & Industry
with st.sidebar:
    st.subheader("Settings")
    api_base_input = st.text_input("API Base", value=API_BASE, help="e.g., http://localhost:8000")
    timeout_input = st.number_input("Timeout (seconds)", value=TIMEOUT, min_value=5, max_value=120)

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
tab_brief, tab_plan, tab_export = st.tabs(["Brief & Generate", "Marketing Plan", "Export"])

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
    st.caption("(Implementation: would show report details from previous tab)")

with tab_export:
    st.header("Export")
    st.info("After generating a report, you can export it here as PDF or DOCX.")
    if st.button("Export as PDF (Demo)"):
        st.success("✅ Export feature coming soon")

print(f"✅ [DEBUG] Operator Dashboard loaded from: {__file__}")
