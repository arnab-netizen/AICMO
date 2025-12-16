"""AICMO Operator Dashboard – Complete Streamlit Application.

⚠️  DEPRECATED FOR NEW USE:
For production workflows, use: streamlit_pages/aicmo_operator.py
This file is retained for backward compatibility with E2E report generation tests.

Run canonical UI:
  python -m streamlit run streamlit_pages/aicmo_operator.py --server.port 8501

This is a professional workspace for generating, refining, and exporting
client marketing reports. Integrates with backend endpoints:
- /aicmo/generate
- /aicmo/revise
- /aicmo/learn
- /aicmo/export
- /health (diagnostics)
"""

import json
import os
import re
import subprocess
import sys
import time
import hashlib
from typing import Any, Dict, Optional

# PHASE 2: DEPRECATED UI GUARD
# This file is legacy and should not be run directly via Streamlit
import streamlit as st
if os.getenv('AICMO_ALLOW_DEPRECATED_UI', '').lower() != '1':
    st.error("❌ DEPRECATED: streamlit_app.py is legacy code")
    st.markdown("""
Use the canonical dashboard instead:
```bash
python -m streamlit run streamlit_pages/aicmo_operator.py
```

To override (dev only): `export AICMO_ALLOW_DEPRECATED_UI=1`
    """)
    st.stop()

# Continue with legacy imports only if override is set
requests = __import__('requests')


# Import AICMO API client
from backend.client.aicmo_api_client import call_generate_report
from backend.utils.config import is_production_llm_ready, allow_stubs_in_current_env


def parse_markdown_to_sections(markdown: str) -> dict:
    """
    Parse markdown content into structured sections dict.

    Splits by ## headers (H2) and creates a dict like:
    {"section_name": "content", ...}

    If no headers found, returns single section with full content.
    """
    if not markdown or not markdown.strip():
        return {}

    # Split by ## headers (H2 level)
    # Pattern: ## Header Name
    sections = {}

    # Find all H2 headers and their positions
    pattern = r"^## (.+?)$"
    matches = list(re.finditer(pattern, markdown, re.MULTILINE))

    if not matches:
        # No sections found, return entire content as single section
        return {"full_report": markdown}

    # Extract sections between headers
    for i, match in enumerate(matches):
        section_title = match.group(1).strip()
        start_pos = match.end()

        # Find end position (start of next section or end of document)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(markdown)

        # Extract content between this header and next
        content = markdown[start_pos:end_pos].strip()

        # Use section title as key (sanitize for dict key)
        section_key = section_title.lower().replace(" ", "_").replace("-", "_")
        section_key = re.sub(r"[^a-z0-9_]", "", section_key)

        if content:  # Only add non-empty sections
            sections[section_key] = content

    # If we have sections but none had content, fallback to full report
    if not sections:
        sections = {"full_report": markdown}

    return sections


def compute_sha256(data: bytes) -> str:
    """Compute SHA256 hash of bytes data."""
    return hashlib.sha256(data).hexdigest()


def populate_download_cache(paths_dict: dict, manifest_json: dict, e2e_mode: bool = False) -> dict:
    """Populate e2e_download_cache with manifest/validation/section_map and artifacts.
    
    Returns cache dict with structure:
    {"manifest_json": bytes, "validation_json": bytes, "section_map_json": bytes, 
     "artifacts": {artifact_id: {"filename": str, "bytes": bytes, "sha256": str, "size": int}}}
    
    If any read fails, returns {"error": error_message}
    """
    try:
        from pathlib import Path
        import json
        
        cache = {
            "manifest_json": None,
            "validation_json": None,
            "section_map_json": None,
            "artifacts": {}
        }
        
        manifest_path = Path(paths_dict.get("manifest_path", ""))
        validation_path = Path(paths_dict.get("validation_path", ""))
        section_map_path = Path(paths_dict.get("section_map_path", ""))
        downloads_dir = Path(paths_dict.get("downloads_dir", ""))
        
        # Read manifest
        if manifest_path.exists():
            with open(manifest_path, 'rb') as f:
                manifest_bytes = f.read()
                cache["manifest_json"] = manifest_bytes
        else:
            return {"error": f"Manifest path not found: {manifest_path}"}
        
        # Read validation JSON
        if validation_path.exists():
            with open(validation_path, 'rb') as f:
                cache["validation_json"] = f.read()
        
        # Read section map JSON
        if section_map_path.exists():
            with open(section_map_path, 'rb') as f:
                cache["section_map_json"] = f.read()
        
        # Process artifacts from manifest
        if manifest_json and "artifacts" in manifest_json:
            for artifact in manifest_json["artifacts"]:
                artifact_id = artifact.get("artifact_id")
                filename = artifact.get("filename")
                
                if not artifact_id or not filename:
                    continue
                
                filepath = downloads_dir / filename
                if filepath.exists():
                    with open(filepath, 'rb') as f:
                        artifact_bytes = f.read()
                        cache["artifacts"][artifact_id] = {
                            "filename": filename,
                            "bytes": artifact_bytes,
                            "sha256": compute_sha256(artifact_bytes),
                            "size": len(artifact_bytes)
                        }
                else:
                    if e2e_mode:
                        sys.stderr.write(f"[E2E DEBUG] Artifact file missing: {filepath}\n")
                        sys.stderr.flush()
        
        return cache
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# SECRETS BRIDGE → os.environ
# ═══════════════════════════════════════════════════════════════════════
# Streamlit secrets don't automatically populate os.environ.
# The backend and memory engine look at os.getenv() directly.
# This bridge ensures secrets are available to all components.

if "AICMO_MEMORY_DB" in st.secrets:
    os.environ["AICMO_MEMORY_DB"] = st.secrets["AICMO_MEMORY_DB"]

if "AICMO_USE_LLM" in st.secrets:
    os.environ["AICMO_USE_LLM"] = st.secrets["AICMO_USE_LLM"]

if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG & GLOBAL STYLE
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AICMO Operator Dashboard",
    page_icon="🎯",
    layout="wide",
)

# Modern dark "terminal" styling
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #111827 0, #020617 45%, #000 100%);
        color: #E5E7EB;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    }

    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 1.25rem;
        max-width: 1400px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #020617, #020617 40%, #020617 70%, #020617);
        border-right: 1px solid rgba(148,163,184,0.16);
    }

    .sidebar-title {
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        font-size: 0.8rem;
        color: #9CA3AF;
    }

    .sidebar-logo {
        font-weight: 800;
        font-size: 1.1rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #F9FAFB;
    }

    .cc-card {
        background: radial-gradient(circle at top left, #111827 0, #020617 65%);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        border: 1px solid rgba(148,163,184,0.3);
        box-shadow: 0 0 0 1px rgba(15,23,42,0.8), 0 18px 45px rgba(15,23,42,0.85);
    }

    .cc-card h3 {
        font-size: 0.8rem;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: #9CA3AF;
        margin-bottom: 0.3rem;
    }

    .cc-metric {
        font-size: 1.8rem;
        font-weight: 650;
        color: #F9FAFB;
        margin-bottom: 0.15rem;
    }

    .cc-subtext {
        font-size: 0.75rem;
        color: #9CA3AF;
    }

    .cc-alert {
        font-size: 0.75rem;
        color: #FBBF24;
        margin-top: 0.15rem;
    }

    .cc-feed {
        max-height: 280px;
        overflow-y: auto;
        padding-right: 0.35rem;
    }

    .cc-feed-item {
        font-size: 0.8rem;
        border-bottom: 1px solid rgba(30,64,175,0.55);
        padding: 0.35rem 0;
    }

    .cc-feed-item time {
        color: #6B7280;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        margin-right: 0.4rem;
    }

    .cc-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 999px;
        margin-right: 0.25rem;
        box-shadow: 0 0 10px currentColor;
    }
    .cc-dot-ok { color: #22C55E; background: #22C55E; }
    .cc-dot-bad { color: #F97373; background: #F97373; }
    .cc-dot-warn { color: #FACC15; background: #FACC15; }

    .cc-gateway-label {
        font-size: 0.78rem;
        color: #D1D5DB;
        margin-right: 0.75rem;
        white-space: nowrap;
    }

    .cc-column-title {
        font-size: 0.75rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #9CA3AF;
        margin-bottom: 0.35rem;
    }

    .cc-project-card {
        background: rgba(15,23,42,0.95);
        border-radius: 10px;
        padding: 0.45rem 0.65rem;
        border: 1px solid rgba(30,64,175,0.6);
        margin-bottom: 0.4rem;
        font-size: 0.8rem;
    }

    .cc-project-name {
        font-weight: 600;
        color: #E5E7EB;
    }

    .cc-pill-danger {
        display: inline-flex;
        align-items: center;
        padding: 0.05rem 0.4rem;
        border-radius: 999px;
        background: rgba(248,113,113,0.15);
        color: #FCA5A5;
        font-size: 0.68rem;
        margin-top: 0.15rem;
    }

    .cc-pill-warn {
        display: inline-flex;
        align-items: center;
        padding: 0.05rem 0.4rem;
        border-radius: 999px;
        background: rgba(250,204,21,0.08);
        color: #FACC15;
        font-size: 0.68rem;
        margin-top: 0.15rem;
    }

    .cc-pill-ok {
        display: inline-flex;
        align-items: center;
        padding: 0.05rem 0.4rem;
        border-radius: 999px;
        background: rgba(34,197,94,0.12);
        color: #4ADE80;
        font-size: 0.68rem;
        margin-top: 0.15rem;
    }

    button[role="tab"] {
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-size: 0.7rem !important;
    }

    .cc-pause-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #F97373;
    }

    /* Preserve compatibility with existing cards */
    .aicmo-card {
        background: radial-gradient(circle at top left, #111827 0, #020617 65%);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        border: 1px solid rgba(148,163,184,0.3);
        box-shadow: 0 0 0 1px rgba(15,23,42,0.8), 0 18px 45px rgba(15,23,42,0.85);
    }

    .aicmo-tagline {
        color: #9ca3af;
        font-size: 0.9rem;
    }

    .aicmo-section-title {
        margin-top: 1.25rem;
        margin-bottom: 0.5rem;
    }

    button[kind="primary"] {
        border-radius: 9999px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════
# CONFIG & SESSION STATE
# ═══════════════════════════════════════════════════════════════════════

DEFAULT_API_BASE = "http://localhost:8000"

# -------------------------------------------------
# Package presets (Fiverr/Upwork-style)
# -------------------------------------------------

PACKAGE_PRESETS = {
    # GENERAL PACKAGES
    "Quick Social Pack (Basic)": {
        "marketing_plan": False,
        "campaign_blueprint": False,
        "social_calendar": True,
        "performance_review": False,
        "creatives": True,
        "include_agency_grade": False,
    },
    "Strategy + Campaign Pack (Standard)": {
        "marketing_plan": True,
        "campaign_blueprint": True,
        "social_calendar": True,
        "performance_review": False,
        "creatives": True,
        "include_agency_grade": False,
    },
    "Full CMO / Go-To-Market (Premium)": {
        "marketing_plan": True,
        "campaign_blueprint": True,
        "social_calendar": True,
        "performance_review": True,
        "creatives": True,
        "include_agency_grade": True,
    },
    # SPECIALISED PACKAGES
    "Ads Launch Pack (Meta/Google/LinkedIn)": {
        "marketing_plan": False,
        "campaign_blueprint": True,
        "social_calendar": True,
        "performance_review": False,
        "creatives": True,
        "include_agency_grade": False,
    },
    "Email Funnel Pack": {
        "marketing_plan": False,
        "campaign_blueprint": True,
        "social_calendar": False,
        "performance_review": False,
        "creatives": True,
        "include_agency_grade": False,
    },
    "Launch Campaign Pack": {
        "marketing_plan": True,
        "campaign_blueprint": True,
        "social_calendar": True,
        "performance_review": False,
        "creatives": True,
        "include_agency_grade": True,
    },
    "Performance Review & Growth Audit": {
        "marketing_plan": False,
        "campaign_blueprint": False,
        "social_calendar": False,
        "performance_review": True,
        "creatives": False,
        "include_agency_grade": True,
    },
    "Organic Authority Pack (LinkedIn-first)": {
        "marketing_plan": True,
        "campaign_blueprint": False,
        "social_calendar": True,
        "performance_review": False,
        "creatives": True,
        "include_agency_grade": False,
    },
    "Local Business Growth Pack": {
        "marketing_plan": True,
        "campaign_blueprint": True,
        "social_calendar": True,
        "performance_review": False,
        "creatives": True,
        "include_agency_grade": False,
    },
}

if "current_project_id" not in st.session_state:
    st.session_state.current_project_id = None

if "current_brief" not in st.session_state:
    st.session_state.current_brief = None  # dict

if "generated_report" not in st.session_state:
    st.session_state.generated_report = None  # dict

# E2E Mode: Initialize with stub report for testing
if os.getenv('AICMO_E2E_MODE') == '1' and st.session_state.generated_report is None:
    st.session_state.current_brief = {
        "brand": {
            "brand_name": "E2E Test Brand",
            "industry": "Technology",
            "description": "Test company for E2E validation"
        },
        "objective": "Test objective",
        "audience": "Test audience"
    }
    st.session_state.generated_report = {
        "agency_baseline": {"enabled": True},
        "sections": {
            "Executive Summary": "This is a test executive summary for E2E validation testing.",
            "Market Analysis": "This is test market analysis content for validation purposes.",
            "Strategy Overview": "This is test strategy content to ensure export gate works properly."
        },
        "markdown": "# E2E Test Report\n\n## Executive Summary\n\nTest content.\n\n## Market Analysis\n\nTest market data."
    }

if "selected_outputs" not in st.session_state:
    st.session_state.selected_outputs = []

if "usage_counter" not in st.session_state:
    st.session_state.usage_counter = {"reports": 0, "words": 0}

if "recent_projects" not in st.session_state:
    st.session_state.recent_projects = []  # list[dict]

# NEW: Package preset and agency-grade flag
if "package_preset" not in st.session_state:
    st.session_state.package_preset = "Strategy + Campaign Pack (Standard)"

if "include_agency_grade" not in st.session_state:
    st.session_state.include_agency_grade = False

# ─────────────────────────────────────────────────────────────────────
# COMMAND CENTER STATE (for cockpit dashboard)
# ─────────────────────────────────────────────────────────────────────
if "activity_log" not in st.session_state:
    st.session_state.activity_log = [
        {"timestamp": "2025-01-22T14:30:00", "message": "System initialized"},
        {"timestamp": "2025-01-22T14:35:00", "message": "Strategy service online"},
    ]

if "mock_projects" not in st.session_state:
    st.session_state.mock_projects = {
        "to_do": [
            {"id": 101, "name": "Client A Campaign", "status": "Needs brief", "deadline": "2025-01-27"}
        ],
        "in_progress": [
            {"id": 102, "name": "Q1 Social Strategy", "status": "Creative review", "deadline": "2025-01-25"},
            {"id": 103, "name": "Product Launch", "status": "Copy edits", "deadline": "2025-01-24"}
        ],
        "done": [
            {"id": 104, "name": "Dec Newsletter", "status": "Delivered", "deadline": None}
        ]
    }

if "gateway_status" not in st.session_state:
    st.session_state.gateway_status = {
        "Instagram": "ok",
        "LinkedIn": "ok",
        "Twitter": "warn",
        "Email": "ok",
        "CRM": "bad"
    }

if "system_paused" not in st.session_state:
    st.session_state.system_paused = False


# ═══════════════════════════════════════════════════════════════════════
# BACKEND HELPERS
# ═══════════════════════════════════════════════════════════════════════

DEFAULT_API_BASE = "http://127.0.0.1:8000"


def call_backend(
    method: str,
    base: str,
    path: str,
    *,
    json_body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> requests.Response:
    """Make HTTP request to backend."""
    url = base.rstrip("/") + path
    resp = requests.request(method, url, json=json_body, params=params, timeout=timeout)
    return resp


def aicmo_generate(
    api_base: str,
    brief: Dict[str, Any],
    industry: Optional[str],
    outputs: list[str],
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Temporary: use CopyHook as the 'report generator' until /aicmo/generate exists.

    We build a payload similar to backend/tests/test_copyhook_api.py:
      - project_id
      - goal
      - constraints (brand, tone, audience, benefits, CTA)
      - sources
      - policy_id
      - budget_tokens
    """
    brand = brief.get("brand", {})
    brand_name = brand.get("brand_name") or brand.get("name") or "ClientBrand"
    objective = brief.get("objective", "Landing page hero variants")
    audience = brief.get("audience", "Target decision makers")
    channels = brief.get("channels", [])
    benefits = brief.get("benefits") or brief.get("pain_points") or []

    goal = f"3 landing page hero variants for {brand_name}"
    if objective:
        goal = f"3 landing page hero variants for {brand_name} – {objective}"

    payload = {
        "project_id": "streamlit-manual-test-001",
        "goal": goal,
        "constraints": {
            "brand": brand_name,
            "tone": brief.get("tone", "confident, clear"),
            "must_avoid": [],
            "main_cta": "Book a demo",
            "audience": audience,
            "benefits": benefits or ["Ship faster", "Reduce ops cost", "Centralize workflows"],
            "channels": channels,
            "industry": industry,
        },
        "sources": [],
        "policy_id": "policy/default",
        "budget_tokens": 15000,
    }

    # Use skip_gates=true in dev mode to bypass readability/dedup/platform checks
    # (compliance check for banned terms is always enforced)
    resp = call_backend(
        "POST",
        api_base,
        "/api/copyhook/run",
        json_body=payload,
        params={"skip_gates": True},  # Dev mode: skip quality gates for testing
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def aicmo_revise(
    api_base: str,
    project_id: str,
    section_id: str,
    instructions: str,
    timeout: int,
) -> Dict[str, Any]:
    """Call /aicmo/revise endpoint."""
    payload = {
        "project_id": project_id,
        "section_id": section_id,
        "instructions": instructions,
    }
    resp = call_backend("POST", api_base, "/aicmo/revise", json_body=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def aicmo_learn(
    api_base: str,
    project_id: str,
    brief: Dict[str, Any],
    final_report: Dict[str, Any],
    tags: Dict[str, str],
    timeout: int,
) -> Dict[str, Any]:
    """Call /api/learn/from-report endpoint (Phase L memory engine)."""
    # Convert tags dict to list of formatted strings
    tag_list = [f"{k}:{v}" for k, v in tags.items()] if tags else []

    payload = {
        "project_id": project_id,
        "report": final_report,
        "tags": tag_list,
    }
    resp = call_backend(
        "POST", api_base, "/api/learn/from-report", json_body=payload, timeout=timeout
    )
    resp.raise_for_status()
    return resp.json()


def aicmo_export(
    api_base: str,
    brief: Dict[str, Any],
    output: Dict[str, Any],
    format_: str,
    timeout: int,
) -> bytes:
    """Call /aicmo/export/{pdf,pptx,zip} endpoint."""
    if format_ == "json":
        # Return JSON as downloadable
        return json.dumps(output, indent=2).encode("utf-8")

    payload = {"brief": brief, "output": output}

    if format_ == "pdf":
        resp = call_backend(
            "POST", api_base, "/aicmo/export/pdf", json_body=payload, timeout=timeout
        )
    elif format_ == "pptx":
        resp = call_backend(
            "POST", api_base, "/aicmo/export/pptx", json_body=payload, timeout=timeout
        )
    elif format_ == "zip":
        resp = call_backend(
            "POST", api_base, "/aicmo/export/zip", json_body=payload, timeout=timeout
        )
    else:
        raise ValueError(f"Unsupported format: {format_}")

    resp.raise_for_status()
    return resp.content


# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR – NAV + SETTINGS
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 🎯 AICMO")
    st.markdown("Operator Workspace")

    st.markdown("---")
    api_base = st.text_input("API Base", value=DEFAULT_API_BASE)
    timeout = st.number_input("Timeout (seconds)", min_value=5, max_value=120, value=20)

    st.markdown("#### Industry Preset")

    # Try to load industries from backend
    industries_list = ["none"]
    try:
        resp = call_backend("GET", api_base, "/aicmo/industries", timeout=int(timeout))
        if resp.status_code == 200:
            data = resp.json()
            if "industries" in data:
                industries_list.extend(data["industries"])
    except Exception:
        # Fallback to hardcoded list
        industries_list = [
            "none",
            "SaaS",
            "E-commerce",
            "D2C",
            "Healthcare",
            "FinTech",
            "Real Estate",
        ]

    industry = st.selectbox(
        "Select Industry",
        industries_list,
        index=0,
        help="Choose if the client clearly fits one of these categories.",
    )

    st.markdown("---")

    # STEP 3: Environment indicator
    st.markdown("#### 🔧 Environment Status")
    prod_llm_ready = is_production_llm_ready()
    stubs_allowed = allow_stubs_in_current_env()

    if prod_llm_ready:
        st.success("**LLM Mode:** PRODUCTION")
        st.caption("✅ Real LLM keys configured (no stubs)")

        # STEP 3: Add LLM health check button (only in production)
        if st.button("🏥 Check LLM Health", key="sidebar_health_check"):
            with st.spinner("Checking LLM health..."):
                try:
                    # Call the /health/llm endpoint
                    health_response = call_backend("GET", api_base, "/health/llm", timeout=30)

                    if health_response.status_code == 200:
                        health_data = health_response.json()

                        # Display results
                        st.markdown("**Health Check Results:**")

                        # Overall status
                        if health_data.get("ok"):
                            st.success("✅ Overall: HEALTHY")
                        else:
                            st.error("❌ Overall: UNHEALTHY")

                        # Details
                        st.markdown(f"- **LLM Ready:** {health_data.get('llm_ready')}")
                        st.markdown(f"- **Used Stub:** {health_data.get('used_stub')}")
                        st.markdown(f"- **Quality Passed:** {health_data.get('quality_passed')}")

                        # Error details if present
                        if health_data.get("error_type"):
                            st.warning(f"⚠️ **Error:** {health_data.get('error_type')}")
                            st.caption(health_data.get("debug_hint", "No details"))

                    else:
                        st.error(f"Health check failed: HTTP {health_response.status_code}")

                except Exception as exc:
                    st.error(f"Health check error: {exc}")
    else:
        st.info("**LLM Mode:** DEV/LOCAL")
        if stubs_allowed:
            st.caption("⚠️ Stub content allowed (no LLM keys)")
        else:
            st.warning("⚠️ Stubs disabled but no LLM keys")

    st.markdown("---")
    
    # E2E: App loaded sentinel (always visible)
    st.markdown('<div data-testid="e2e-app-loaded">YES</div>', unsafe_allow_html=True)

    # Navigation radio with sentinel container
    st.markdown('<div data-testid="e2e-nav-radio">', unsafe_allow_html=True)
    nav = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Brief & Generate",
            "Workshop",
            "Learn & Improve",
            "Export",
            "🛡️ Operator QC",
            "Settings",
        ],
        index=0,
        key="nav_radio",
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # E2E: Current nav value (always visible, unambiguous proof)
    st.markdown(f'<div data-testid="e2e-nav-current">{nav}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════

header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("Operator Dashboard")
    st.markdown(
        '<p class="aicmo-tagline">'
        "Command center for generating, refining, and exporting client marketing reports."
        "</p>",
        unsafe_allow_html=True,
    )
with header_col2:
    st.write("")
    new_clicked = st.button("New Client Report", use_container_width=True)
    if new_clicked:
        st.session_state.current_project_id = None
        st.session_state.current_brief = None
        st.session_state.generated_report = None


def _safe_get_current_project_name() -> str:
    """Get current project name safely."""
    if st.session_state.current_brief and "brand" in st.session_state.current_brief:
        brand = st.session_state.current_brief["brand"]
        name = brand.get("brand_name") or brand.get("name") or "Unnamed"
        return str(name)
    return "No active project"


def _get_gateway_dot(status: str) -> str:
    """Return HTML for colored status dot."""
    if status == "ok":
        return '<span class="cc-dot cc-dot-ok"></span>'
    elif status == "warn":
        return '<span class="cc-dot cc-dot-warn"></span>'
    else:
        return '<span class="cc-dot cc-dot-bad"></span>'


# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD (COMMAND CENTER)
# ═══════════════════════════════════════════════════════════════════════

if nav == "Dashboard":
    st.markdown("## Command Center")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚡ Command",
        "📋 Projects",
        "🎯 War Room",
        "🖼️ Gallery",
        "🛰️ Control Tower"
    ])

    # ─── TAB 1: COMMAND (Core Metrics) ─────────────────────────────────
    with tab1:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown('<div class="cc-card">', unsafe_allow_html=True)
            st.markdown("<h3>Reports Generated</h3>", unsafe_allow_html=True)
            reports = st.session_state.usage_counter["reports"]
            st.markdown(f'<div class="cc-metric">{reports}</div>', unsafe_allow_html=True)
            st.markdown('<div class="cc-subtext">Lifetime usage</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="cc-card">', unsafe_allow_html=True)
            st.markdown("<h3>Words Generated</h3>", unsafe_allow_html=True)
            words = st.session_state.usage_counter["words"]
            st.markdown(f'<div class="cc-metric">{words:,}</div>', unsafe_allow_html=True)
            st.markdown('<div class="cc-subtext">Total content output</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="cc-card">', unsafe_allow_html=True)
            st.markdown("<h3>Active Projects</h3>", unsafe_allow_html=True)
            active_count = len(st.session_state.mock_projects["in_progress"])
            st.markdown(f'<div class="cc-metric">{active_count}</div>', unsafe_allow_html=True)
            st.markdown('<div class="cc-subtext">Currently in progress</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        col_feed, col_proj = st.columns([1, 1])

        with col_feed:
            st.markdown('<div class="cc-card">', unsafe_allow_html=True)
            st.markdown("<h3>Activity Feed</h3>", unsafe_allow_html=True)
            st.markdown('<div class="cc-feed">', unsafe_allow_html=True)
            for item in st.session_state.activity_log[-10:]:
                ts = item["timestamp"]
                msg = item["message"]
                st.markdown(
                    f'<div class="cc-feed-item"><time>{ts}</time> {msg}</div>',
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_proj:
            st.markdown('<div class="cc-card">', unsafe_allow_html=True)
            st.markdown("<h3>Current Project</h3>", unsafe_allow_html=True)
            project_name = _safe_get_current_project_name()
            st.markdown(f"**{project_name}**")
            if st.session_state.current_project_id:
                st.caption(f"Project ID: {st.session_state.current_project_id}")
            else:
                st.caption("No project generated yet in this session.")
            st.markdown("</div>", unsafe_allow_html=True)

    # ─── TAB 2: PROJECTS (Kanban) ──────────────────────────────────────
    with tab2:
        col_todo, col_prog, col_done = st.columns(3)

        with col_todo:
            st.markdown('<div class="cc-column-title">To Do</div>', unsafe_allow_html=True)
            for p in st.session_state.mock_projects["to_do"]:
                st.markdown('<div class="cc-project-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="cc-project-name">{p["name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="cc-subtext">{p["status"]}</div>', unsafe_allow_html=True)
                if p.get("deadline"):
                    st.markdown(
                        f'<div class="cc-pill-warn">⏰ {p["deadline"]}</div>',
                        unsafe_allow_html=True
                    )
                st.markdown("</div>", unsafe_allow_html=True)

        with col_prog:
            st.markdown('<div class="cc-column-title">In Progress</div>', unsafe_allow_html=True)
            for p in st.session_state.mock_projects["in_progress"]:
                st.markdown('<div class="cc-project-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="cc-project-name">{p["name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="cc-subtext">{p["status"]}</div>', unsafe_allow_html=True)
                if p.get("deadline"):
                    st.markdown(
                        f'<div class="cc-pill-danger">🚨 {p["deadline"]}</div>',
                        unsafe_allow_html=True
                    )
                st.markdown("</div>", unsafe_allow_html=True)

        with col_done:
            st.markdown('<div class="cc-column-title">Done</div>', unsafe_allow_html=True)
            for p in st.session_state.mock_projects["done"]:
                st.markdown('<div class="cc-project-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="cc-project-name">{p["name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="cc-subtext">{p["status"]}</div>', unsafe_allow_html=True)
                st.markdown('<div class="cc-pill-ok">✅ Complete</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # ─── TAB 3: WAR ROOM (Strategy Review) ─────────────────────────────
    with tab3:
        st.info("**War Room**: Strategy review and planning area (placeholder)")
        st.markdown("- Campaign strategy snapshots")
        st.markdown("- Competitive analysis")
        st.markdown("- Target audience insights")

    # ─── TAB 4: GALLERY (Creative Approval) ────────────────────────────
    with tab4:
        st.info("**Gallery**: Creative asset review and approval (placeholder)")
        st.markdown("- Preview generated images")
        st.markdown("- Approve/reject creatives")
        st.markdown("- Export assets")

    # ─── TAB 5: CONTROL TOWER (Scheduling + Gateways) ──────────────────
    with tab5:
        st.markdown("### Gateway Status")
        for gw, status in st.session_state.gateway_status.items():
            dot = _get_gateway_dot(status)
            st.markdown(
                f'<div style="margin-bottom:0.45rem;">'
                f'{dot} <span class="cc-gateway-label">{gw}</span> '
                f'<span class="cc-subtext">({status.upper()})</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown("### System Controls")
        paused = st.checkbox("⏸️ Pause All Execution", value=st.session_state.system_paused)
        st.session_state.system_paused = paused
        if paused:
            st.markdown('<div class="cc-pause-label">System Paused</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# BRIEF & GENERATE
# ═══════════════════════════════════════════════════════════════════════

elif nav == "Brief & Generate":
    st.subheader("Step 1 – Client Brief & Generation")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("#### Client Brief")
        uploaded = st.file_uploader("Upload PDF/DOCX/TXT (optional)", type=["pdf", "docx", "txt"])
        st.caption("Or paste JSON brief directly below:")

        default_brief = {
            "brand": {
                "brand_name": "TestBrand",
                "industry": "SaaS",
                "description": "Marketing automation tool",
            },
            "objective": "Increase market awareness",
            "audience": "B2B marketing leaders",
            "channels": ["LinkedIn", "Email"],
        }
        brief_str = st.text_area(
            "Client Brief (JSON)",
            value=json.dumps(default_brief, indent=2),
            height=260,
        )

    with col_right:
        st.markdown("#### What should AICMO generate?")
        gen_marketing_plan = st.checkbox("Marketing Plan", value=True)
        gen_campaign_blueprint = st.checkbox("Campaign Blueprint", value=True)
        gen_social_calendar = st.checkbox("Social Calendar", value=True)
        gen_performance_review = st.checkbox("Performance Review", value=False)
        gen_creatives = st.checkbox("Creatives (Hooks, CTAs)", value=True)

        st.markdown("---")
        st.caption("Industry preset will adjust tone, channels, and benchmarks.")
        selected_industry = None if industry == "none" else industry

        generate_btn = st.button("Generate Draft Report", type="primary", use_container_width=True)

    if generate_btn:
        try:
            brief = json.loads(brief_str)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON in brief: {e}")
        else:
            # Build outputs list from checkboxes
            selected_outputs = []
            if gen_marketing_plan:
                selected_outputs.append("marketing_plan")
            if gen_campaign_blueprint:
                selected_outputs.append("campaign_blueprint")
            if gen_social_calendar:
                selected_outputs.append("social_calendar")
            if gen_performance_review:
                selected_outputs.append("performance_review")
            if gen_creatives:
                selected_outputs.append("creatives")

            if not selected_outputs:
                st.error("Select at least one output for AICMO to generate.")
            else:
                with st.status(
                    "Generating AICMO report with production-ready pipeline…", expanded=True
                ) as status:
                    try:
                        # Build payload for AICMO API
                        payload = {
                            "pack_key": "quick_social_basic",  # Default pack
                            "client_brief": brief,
                            "stage": "draft",
                            "services": {
                                "marketing_plan": gen_marketing_plan,
                                "campaign_blueprint": gen_campaign_blueprint,
                                "social_calendar": gen_social_calendar,
                                "performance_review": gen_performance_review,
                                "creatives": gen_creatives,
                            },
                        }

                        # Add industry if selected
                        if selected_industry:
                            payload["industry_key"] = selected_industry

                        # Call the hardened API
                        result = call_generate_report(payload)

                        # Parse markdown into sections for Workshop tab
                        if result.get("success"):
                            markdown = result.get("markdown", "")
                            if markdown:
                                sections = parse_markdown_to_sections(markdown)
                                result["sections"] = sections

                        # Store results
                        st.session_state.current_brief = brief
                        st.session_state.generated_report = result

                        # Check response
                        if result.get("success"):
                            status.update(
                                label="✅ Report generated successfully", state="complete"
                            )
                            st.success("AICMO report generated successfully!")

                            # Show LLM status badge
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown("### Generated Report")
                            with col2:
                                stub_used = result.get("stub_used", False)
                                quality_passed = result.get("quality_passed", True)

                                if stub_used:
                                    st.warning("⚠️ Stub content (dev only)")
                                else:
                                    st.success("✅ LLM: Real")

                                if not quality_passed:
                                    st.warning("⚠️ Quality checks")

                            # Display the markdown report
                            markdown = result.get("markdown", "")
                            if markdown:
                                st.markdown(markdown)
                            else:
                                st.warning("No markdown content in response")

                            # Show debug section
                            with st.expander("Debug (AICMO raw response)"):
                                st.json(result)

                        else:
                            # Handle error response
                            status.update(label="❌ Generation failed", state="error")
                            error_type = result.get("error_type", "unknown")
                            error_message = result.get("error_message", "No error message provided")

                            st.error(f"**Error:** {error_type}")
                            st.error(error_message)

                            # Show specific guidance for error types
                            if error_type == "runtime_quality_failed":
                                debug_hint = result.get("debug_hint", "")
                                st.warning(f"💡 **Hint:** {debug_hint}")

                                extra = result.get("extra", {})
                                if extra:
                                    with st.expander("Quality Check Details"):
                                        if "missing_terms" in extra and extra["missing_terms"]:
                                            st.write("**Missing required terms:**")
                                            st.write(", ".join(extra["missing_terms"]))
                                        if "forbidden_terms" in extra and extra["forbidden_terms"]:
                                            st.write("**Forbidden terms found:**")
                                            st.write(", ".join(extra["forbidden_terms"]))
                                        if "brand_mentions" in extra:
                                            st.write(
                                                f"**Brand mentions:** {extra['brand_mentions']}"
                                            )

                            elif error_type in ["llm_chain_failed", "llm_failure"]:
                                st.info(
                                    "💡 Check OpenAI and Perplexity API status. All LLM providers may be unavailable."
                                )

                            elif error_type == "stub_in_production_forbidden":
                                st.error(
                                    "🔴 **CRITICAL:** Stub content was generated in production mode. This should never happen!"
                                )
                                st.info("Check application logs for AICMO_RUNTIME errors.")

                            # Show debug section
                            with st.expander("Debug (AICMO error response)"):
                                st.json(result)

                    except Exception as exc:
                        status.update(label="Generation failed.", state="error")
                        st.error(f"Unexpected error: {exc}")
                        import traceback

                        with st.expander("Stack trace"):
                            st.code(traceback.format_exc())

# ═══════════════════════════════════════════════════════════════════════
# WORKSHOP (MARKETING PLAN)
# ═══════════════════════════════════════════════════════════════════════

elif nav == "Workshop":
    st.subheader("Step 2 – Workshop & Refine")

    if not st.session_state.generated_report:
        st.info("No draft report yet. Generate one from **Brief & Generate** first.")
    else:
        report = st.session_state.generated_report

        # DEBUG: Show what keys are in the report
        st.write("🔍 DEBUG - Report keys:", list(report.keys()))

        st.caption("Review sections below. You can send revision instructions for each section.")
        sections = report.get("sections") or report.get("content") or {}
        if isinstance(sections, dict):
            items = list(sections.items())
        elif isinstance(sections, list):
            # fallback if backend returns [{id,title,body}, ...]
            items = [
                (s.get("id") or s.get("title") or f"section_{i}", s) for i, s in enumerate(sections)
            ]
        else:
            items = []

        if not items:
            st.warning("⚠️ No structured sections found in the report.")
            st.info(
                "The report was generated but couldn't be parsed into sections. You can still view it in the **Brief & Generate** tab or export it."
            )

            # Show raw markdown as fallback
            markdown = report.get("markdown", "")
            if markdown:
                with st.expander("📄 View full report (raw)", expanded=False):
                    st.markdown(markdown)
        else:
            st.success(f"✅ Found {len(items)} sections in report")

        for section_id, section_content in items:
            with st.expander(f"Section: {section_id}", expanded=False):
                st.markdown("##### Current content")
                st.write(section_content)

                instructions = st.text_area(
                    f"Revision instructions for `{section_id}`",
                    key=f"instr_{section_id}",
                    placeholder="E.g., make tone more casual, focus on ROI, shorten this section…",
                )
                col_a, col_b = st.columns([1, 4])
                with col_a:
                    if st.button(
                        "Revise section", key=f"btn_{section_id}", use_container_width=True
                    ):
                        try:
                            project_id = st.session_state.current_project_id or "temp-project"
                            revised = aicmo_revise(
                                api_base=api_base,
                                project_id=project_id,
                                section_id=str(section_id),
                                instructions=instructions,
                                timeout=int(timeout),
                            )
                            # Update section with revised content
                            updated_section = revised.get("section") or revised
                            if isinstance(sections, dict):
                                sections[section_id] = updated_section
                            elif isinstance(sections, list):
                                for s in sections:
                                    if s.get("id") == section_id:
                                        s.update(updated_section)
                            st.session_state.generated_report["sections"] = sections
                            st.success("Section updated from backend.")
                        except Exception as exc:
                            st.error(f"Revision failed: {exc}")
                with col_b:
                    st.caption("AICMO will use your instructions to re-write this section only.")

        st.markdown("---")
        st.markdown("#### Global revision")
        global_instr = st.text_area(
            "High-level revision instructions for the whole report",
            placeholder="E.g., adjust for EU market, emphasize retention instead of acquisition…",
        )
        if st.button(
            "(Optional) Re-run full report with new instructions", use_container_width=True
        ):
            st.warning(
                "Wire this button to a dedicated 'revise_whole_report' endpoint if available."
            )

# ═══════════════════════════════════════════════════════════════════════
# LEARN & IMPROVE
# ═══════════════════════════════════════════════════════════════════════

elif nav == "Learn & Improve":
    st.subheader("Step 3 – Teach AICMO & Add Library Assets")

    if not st.session_state.generated_report or not st.session_state.current_brief:
        st.info(
            "You need a finalized report and brief to teach AICMO. Complete Steps 1 and 2 first."
        )
    else:
        brief = st.session_state.current_brief
        report = st.session_state.generated_report
        project_id = st.session_state.current_project_id or "temp-project"

        st.markdown("#### Teach AICMO from this project")
        st.caption(
            "This will store the client brief + final report so future generations "
            "for similar brands and industries get better."
        )

        col_tags1, col_tags2 = st.columns(2)
        with col_tags1:
            t_industry = st.text_input(
                "Industry tag", value=brief.get("brand", {}).get("industry", "")
            )
            t_geo = st.text_input("Region tag", value="India")
        with col_tags2:
            t_stage = st.text_input("Stage tag (e.g., launch, growth, retention)", value="launch")
            t_notes = st.text_input("Internal notes tag", value="benchmark-good")

        if st.button("Teach AICMO from this project", type="primary"):
            try:
                result = aicmo_learn(
                    api_base=api_base,
                    project_id=project_id,
                    brief=brief,
                    final_report=report,
                    tags={
                        "industry": t_industry,
                        "region": t_geo,
                        "stage": t_stage,
                        "notes": t_notes,
                    },
                    timeout=int(timeout),
                )
                st.success(
                    f"✅ AICMO learned from this project! ({result.get('stored_blocks', '?')} blocks stored)"
                )
                st.json(result)
            except Exception as exc:
                error_msg = str(exc)
                st.error(
                    f"❌ Teaching failed: {error_msg}\n\nMake sure the backend is running and the endpoint /api/learn/from-report is available."
                )

        st.markdown("---")
        st.markdown("#### Bulk Training – Upload ZIP Archive")
        st.caption(
            "Upload your full AICMO_Training.zip (with 00–10 folders) to bulk-teach AICMO using "
            "frameworks, examples, and report libraries."
        )

        training_zip = st.file_uploader(
            "Select AICMO training ZIP",
            type=["zip"],
            key="training_zip",
        )

        if training_zip is not None and st.button("Train from ZIP", key="train_from_zip"):
            with st.spinner("Uploading and training from ZIP…"):
                try:
                    # Build multipart upload for backend
                    files = {
                        "file": (
                            training_zip.name,
                            training_zip.getvalue(),
                            "application/zip",
                        )
                    }
                    effective_project_id = project_id or "bulk-training"

                    resp = requests.post(
                        api_base.rstrip("/") + "/api/learn/from-zip",
                        files=files,
                        params={"project_id": effective_project_id},
                        timeout=int(timeout),
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(
                            f"✅ ZIP training complete.\n\n"
                            f"**Files processed:** {data.get('files_processed', '?')}\n"
                            f"**Blocks learned:** {data.get('blocks_learned', '?')}\n\n"
                            f"{data.get('message', '')}"
                        )
                    else:
                        st.error(
                            f"❌ ZIP training failed: {resp.status_code} – " f"{resp.text[:300]}"
                        )
                except Exception as e:
                    st.error(f"❌ Error while calling /api/learn/from-zip: {e}")

        st.markdown("---")
        st.markdown("#### Add external reference reports (optional)")
        ref_files = st.file_uploader(
            "Upload top-agency reports / decks to use as reference material",
            type=["pdf", "pptx", "docx", "txt"],
            accept_multiple_files=True,
        )
        if ref_files:
            st.info(
                f"📚 Ready to learn from {len(ref_files)} file(s). Click below to add to Phase L memory."
            )

            if st.button("📖 Teach AICMO from these files", key="teach_from_files"):
                with st.spinner("📚 Teaching AICMO from your files..."):
                    try:
                        # Extract text from uploaded files
                        extracted_files = []
                        for uploaded_file in ref_files:
                            try:
                                # Try to read as text (works for .txt, .docx preview, .pptx preview)
                                file_text = uploaded_file.read().decode("utf-8", errors="ignore")
                                if file_text.strip():
                                    extracted_files.append(
                                        {"filename": uploaded_file.name, "text": file_text}
                                    )
                                    st.caption(
                                        f"✓ Extracted: {uploaded_file.name} ({len(file_text)} chars)"
                                    )
                            except Exception as e:
                                st.caption(f"⚠️ Could not read {uploaded_file.name}: {str(e)[:100]}")

                        if not extracted_files:
                            st.error("❌ No readable text found in uploaded files.")
                        else:
                            # Send to backend
                            payload = {
                                "project_id": st.session_state.current_project_id,
                                "files": extracted_files,
                            }

                            result = call_backend(
                                "POST",
                                api_base,
                                "/api/learn/from-files",
                                json.dumps(payload),
                                timeout=timeout,
                            )

                            if result.get("status") == "ok":
                                items_learned = result.get("items_learned", 0)
                                st.success(
                                    f"✅ AICMO learned {items_learned} blocks from {len(extracted_files)} file(s)!"
                                )
                                st.json(
                                    {
                                        "files_processed": len(extracted_files),
                                        "blocks_learned": items_learned,
                                    }
                                )
                            else:
                                st.error(
                                    f"❌ Learning failed: {result.get('detail', 'Unknown error')}"
                                )
                    except Exception as exc:
                        error_msg = str(exc)
                        st.error(
                            f"❌ File teaching failed: {error_msg}\n\nMake sure the backend is running and the endpoint /api/learn/from-files is available."
                        )

# ═══════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════

elif nav == "Export":
    st.subheader("Step 4 – Export & Delivery")
    
    # PHASE 1.2: Export branch execution sentinel (unambiguous proof branch runs)
    st.markdown('<div data-testid="e2e-on-export-page">YES</div>', unsafe_allow_html=True)
    st.markdown(f'<div data-testid="e2e-export-branch-tick">{int(time.time())}</div>', unsafe_allow_html=True)

    # E2E Mode: Show validation status if available
    e2e_mode = os.getenv('AICMO_E2E_MODE') == '1'
    e2e_diagnostics = os.getenv('AICMO_E2E_DIAGNOSTICS') == '1'
    
    # Step 1.1: Initialize session state ONCE (top-level, always)
    st.session_state.setdefault("e2e_export_state", "IDLE")
    st.session_state.setdefault("e2e_export_run_id", "NONE")
    st.session_state.setdefault("e2e_export_last_error", "")
    st.session_state.setdefault("e2e_export_paths", None)
    st.session_state.setdefault("e2e_violation_mode", os.getenv('AICMO_E2E_VIOLATION_MODE') == '1')
    
    # STEP 1: Session-state byte cache (source of truth for downloads UI)
    # Cache structure: {"manifest_json": bytes, "validation_json": bytes, "section_map_json": bytes, 
    #                   "artifacts": {artifact_id: {"filename": str, "bytes": bytes, "sha256": str, "size": int}}}
    st.session_state.setdefault("e2e_download_cache", None)
    st.session_state.setdefault("e2e_download_cache_error", "")
    
    # Step 2.1: Ensure stub report exists BEFORE export (idempotent, E2E mode only)
    sys.stderr.write(f"[E2E DEBUG] Line 1510: e2e_mode={e2e_mode}, generated_report={st.session_state.get('generated_report') is not None}\n")
    sys.stderr.flush()
    if e2e_mode and not st.session_state.get("generated_report"):
        sys.stderr.write(f"[E2E DEBUG] Creating stub report at line 1512\n")
        sys.stderr.flush()
        st.session_state.generated_report = {
            "agency_baseline": {"enabled": True},
            "sections": {
                "Executive Summary": "E2E test executive summary content with meaningful data.",
                "Market Analysis": "E2E test market analysis content with competitive insights.",
                "Strategy Overview": "E2E test strategy content with actionable recommendations."
            },
            "markdown": "# E2E Test Report\n\n## Executive Summary\n\nTest content.\n\n## Market Analysis\n\nTest market data.\n\n## Strategy Overview\n\nTest strategy."
        }
    sys.stderr.write(f"[E2E DEBUG] Line 1520: After init, generated_report={st.session_state.get('generated_report') is not None}\n")
    sys.stderr.flush()
    
    if e2e_mode:
        st.markdown("---")
        st.markdown("#### 🔐 E2E Validation Status")
        
        # Step 1.2: Always-on sentinels (unconditional rendering)
        st.markdown(f'<div data-testid="e2e-export-state" style="display:none;">STATE: {st.session_state.e2e_export_state}</div>', unsafe_allow_html=True)
        st.markdown(f'<div data-testid="e2e-export-run-id" style="display:none;">RUN_ID: {st.session_state.e2e_export_run_id}</div>', unsafe_allow_html=True)
        st.markdown(f'<div data-testid="e2e-export-last-error" style="display:none;">ERROR: {st.session_state.e2e_export_last_error}</div>', unsafe_allow_html=True)
        
        # Step 1.3: Session-scoped violation toggle (UI controls session)
        if e2e_diagnostics:
            st.markdown('<div class="e2e-diagnostics" style="background-color: #ffe6e6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">', unsafe_allow_html=True)
            st.markdown("**⚠️ E2E Test Controls (Diagnostics Mode Only)**")
            
            st.markdown('<div data-testid="e2e-violation-toggle">', unsafe_allow_html=True)
            violation_mode_checkbox = st.checkbox(
                "[E2E] Violation mode",
                value=st.session_state.get("e2e_violation_mode", False),
                key="e2e_violation_mode_checkbox",
                help="When enabled, exports will deliberately violate contracts for negative testing"
            )
            st.session_state["e2e_violation_mode"] = violation_mode_checkbox
            st.markdown('</div>', unsafe_allow_html=True)
            
            if violation_mode_checkbox:
                st.info("⚠️ Violation mode ENABLED. Export will deliberately FAIL validation.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # OLD: Disk-based validation/downloads section removed in favor of cache-based PHASE 3 section below
        # E2E mode uses session-state cache (PHASE 3), non-E2E mode can use disk if needed

    # PHASE 2: Handler execution proof (counter + unambiguous entry detection)
    # Initialize ONLY if not already initialized (don't reset on every rerun!)
    if "e2e_export_handler_entries" not in st.session_state:
        st.session_state.e2e_export_handler_entries = 0
    
    sys.stderr.write(f"[E2E DEBUG] Line 1667: About to check generated_report, value={st.session_state.get('generated_report') is not None}\n")
    sys.stderr.flush()
    if not st.session_state.generated_report:
        st.info("No report available. Generate and refine one first.")
    else:
        # Render handler entry counter unconditionally (always visible)
        # NOTE: Counter render moved to AFTER button handler (line ~1770) so it shows updated value
        
        st.markdown("#### Export Final Report")
        fmt = st.selectbox(
            "Format",
            ["pdf", "pptx", "zip", "json"],
            index=0,
            key="export_format_select"
        )

        # Add stable selector for export button
        st.markdown('<div data-testid="e2e-run-export">', unsafe_allow_html=True)
        sys.stderr.write(f"[E2E DEBUG] Button render check: about to render button\n")
        sys.stderr.flush()
        if st.button("Generate export file", type="primary", key="generate_export_button"):
            sys.stderr.write(f"[E2E DEBUG] BUTTON CLICKED - entering handler\n")
            sys.stderr.flush()
            # PHASE 2: FIRST LINE — increment handler entries (unambiguous proof)
            st.session_state.e2e_export_handler_entries += 1
            sys.stderr.write(f"[E2E DEBUG] Handler entries incremented to {st.session_state.e2e_export_handler_entries}\n")
            sys.stderr.flush()
            
            # Set state to RUNNING immediately (don't rerun yet)
            if e2e_mode:
                st.session_state.e2e_export_state = "RUNNING"
                st.session_state.e2e_export_last_error = ""
                sys.stderr.write(f"[E2E DEBUG] State set to RUNNING\n")
                sys.stderr.flush()
            
            try:
                sys.stderr.write(f"[E2E DEBUG] Inside try block, e2e_mode={e2e_mode}\n")
                sys.stderr.flush()
                # Ensure report exists in E2E mode
                if e2e_mode and not st.session_state.generated_report:
                    # Create minimal stub report for E2E testing
                    st.session_state.generated_report = {
                        "agency_baseline": {"enabled": True},
                        "sections": {
                            "Executive Summary": "E2E test executive summary content.",
                            "Market Analysis": "E2E test market analysis content.",
                            "Strategy Overview": "E2E test strategy content."
                        },
                        "markdown": "# E2E Test Report\n\n## Executive Summary\n\nTest content.\n\n## Market Analysis\n\nTest market data."
                    }
                
                # Prepare output (with violation injection if in violation mode)
                output_to_export = st.session_state.generated_report.copy()
                
                # E2E Violation Mode: Inject forbidden pattern into section title
                violation_mode = st.session_state.get("e2e_violation_mode", False)
                if e2e_mode and violation_mode:
                    st.warning("⚠️ Violation Mode Active: Injecting 'TODO' into first section title")
                    
                    # Inject TODO into first section title
                    if 'sections' in output_to_export and isinstance(output_to_export['sections'], dict):
                        first_key = list(output_to_export['sections'].keys())[0] if output_to_export['sections'] else None
                        if first_key:
                            first_section_content = output_to_export['sections'][first_key]
                            del output_to_export['sections'][first_key]
                            output_to_export['sections'][f'TODO: {first_key}'] = first_section_content
                            st.info(f"Injected 'TODO:' into section title: '{first_key}' → 'TODO: {first_key}'")
                
                # E2E Mode: Bypass API and use local export gate directly
                validation_report = None
                file_bytes = None
                
                if e2e_mode:
                    try:
                        from aicmo.validation.export_gate import process_export_with_gate
                        from aicmo.delivery.gate import DeliveryBlockedError
                        from aicmo.validation.runtime_paths import get_runtime_paths
                        import io
                        from reportlab.lib.pagesizes import letter
                        from reportlab.pdfgen import canvas
                        
                        # Generate simple PDF bytes locally (no API call)
                        buffer = io.BytesIO()
                        c = canvas.Canvas(buffer, pagesize=letter)
                        c.drawString(100, 750, f"AICMO E2E Test Export")
                        c.drawString(100, 730, f"Brand: {st.session_state.current_brief.get('brand', {}).get('brand_name', 'Test')}")
                        c.drawString(100, 710, f"Format: {fmt}")
                        
                        # Add sections
                        y = 680
                        for section_title, section_content in output_to_export.get('sections', {}).items():
                            c.drawString(100, y, f"Section: {section_title}")
                            y -= 20
                            if isinstance(section_content, str):
                                c.drawString(120, y, section_content[:80])
                            y -= 30
                        
                        c.save()
                        file_bytes = buffer.getvalue()
                        
                        brand_name = st.session_state.current_brief.get("brand", {}).get(
                            "brand_name", "aicmo_report"
                        )
                        file_name = f"{brand_name}.{fmt}"
                        
                        # Process through export gate
                        file_bytes, validation_report = process_export_with_gate(
                            brief=st.session_state.current_brief,
                            output=output_to_export,
                            file_bytes=file_bytes,
                            format_=fmt,
                            filename=file_name,
                        )
                        
                        # Store paths as serializable dict
                        paths = get_runtime_paths()
                        sys.stderr.write(f"[E2E DEBUG] Setting state to PASS\n")
                        sys.stderr.flush()
                        st.session_state.e2e_export_state = "PASS"
                        st.session_state.e2e_export_run_id = paths.run_id
                        st.session_state.e2e_export_last_error = ""
                        st.session_state.e2e_export_paths = {
                            "manifest_path": str(paths.manifest_path),
                            "validation_path": str(paths.validation_path),
                            "section_map_path": str(paths.section_map_path),
                            "downloads_dir": str(paths.downloads_dir)
                        }
                        
                        # STEP 2B: Populate download cache with manifest + artifacts + hashes
                        if e2e_mode:
                            try:
                                import json
                                manifest_path = paths.manifest_path
                                with open(manifest_path) as f:
                                    manifest_json = json.load(f)
                                cache = populate_download_cache(st.session_state.e2e_export_paths, manifest_json, e2e_mode=True)
                                if "error" in cache:
                                    st.session_state.e2e_download_cache_error = cache["error"]
                                    st.session_state.e2e_download_cache = None
                                    sys.stderr.write(f"[E2E DEBUG] Cache population failed: {cache['error']}\n")
                                    sys.stderr.flush()
                                else:
                                    st.session_state.e2e_download_cache = cache
                                    sys.stderr.write(f"[E2E DEBUG] Cache populated: {len(cache.get('artifacts', {}))} artifacts\n")
                                    sys.stderr.flush()
                            except Exception as ex:
                                st.session_state.e2e_download_cache_error = str(ex)
                                st.session_state.e2e_download_cache = None
                                sys.stderr.write(f"[E2E DEBUG] Cache error: {ex}\n")
                                sys.stderr.flush()
                        
                    except DeliveryBlockedError as e:
                        # Validation FAIL (state mutation only)
                        paths = get_runtime_paths()
                        st.session_state.e2e_export_state = "FAIL"
                        st.session_state.e2e_export_run_id = paths.run_id
                        st.session_state.e2e_export_last_error = str(e)[:200]
                        st.session_state.e2e_export_paths = {
                            "manifest_path": str(paths.manifest_path),
                            "validation_path": str(paths.validation_path),
                            "section_map_path": str(paths.section_map_path),
                            "downloads_dir": str(paths.downloads_dir)
                        }
                        
                        # STEP 2C: For FAIL path, cache validation + section_map but NOT deliverables
                        if e2e_mode:
                            try:
                                cache = {
                                    "manifest_json": None,
                                    "validation_json": None,
                                    "section_map_json": None,
                                    "artifacts": {}
                                }
                                from pathlib import Path
                                validation_path = Path(paths.validation_path)
                                section_map_path = Path(paths.section_map_path)
                                
                                if validation_path.exists():
                                    with open(validation_path, 'rb') as f:
                                        cache["validation_json"] = f.read()
                                if section_map_path.exists():
                                    with open(section_map_path, 'rb') as f:
                                        cache["section_map_json"] = f.read()
                                
                                st.session_state.e2e_download_cache = cache
                                sys.stderr.write(f"[E2E DEBUG] FAIL cache populated (validation only)\n")
                                sys.stderr.flush()
                            except Exception as ex:
                                st.session_state.e2e_download_cache_error = str(ex)
                                st.session_state.e2e_download_cache = None
                                sys.stderr.write(f"[E2E DEBUG] FAIL cache error: {ex}\n")
                                sys.stderr.flush()
                        
                    except Exception as e:
                        # Export ERROR (state mutation only)
                        st.session_state.e2e_export_state = "ERROR"
                        st.session_state.e2e_export_last_error = str(e)[:200]
                else:
                    # Non-E2E mode: use API
                    file_bytes = aicmo_export(
                        api_base=api_base,
                        brief=st.session_state.current_brief,
                        output=output_to_export,
                        format_=fmt,
                        timeout=int(timeout),
                    )

                # Determine file extension and mimetype
                if fmt == "pdf":
                    ext = "pdf"
                    mime = "application/pdf"
                elif fmt == "pptx":
                    ext = "pptx"
                    mime = (
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )
                elif fmt == "zip":
                    ext = "zip"
                    mime = "application/zip"
                else:  # json
                    ext = "json"
                    mime = "application/json"

                brand_name = st.session_state.current_brief.get("brand", {}).get(
                    "brand_name", "aicmo_report"
                )
                file_name = f"{brand_name}.{ext}"

                st.download_button(
                    "Download report",
                    data=file_bytes,
                    file_name=file_name,
                    mime=mime,
                    key="download_report_button"
                )
                st.success("Export ready.")
                    
            except Exception as exc:
                st.error(f"Export failed: {exc}")
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close e2e-run-export div
        
        # PHASE 2: Re-render sentinels AFTER handler (so they show updated values)
        st.markdown(f'<div data-testid="e2e-export-handler-entries">{st.session_state.e2e_export_handler_entries}</div>', unsafe_allow_html=True)
        st.markdown(f'<div data-testid="e2e-export-state" style="display:none;">STATE: {st.session_state.e2e_export_state}</div>', unsafe_allow_html=True)
        st.markdown(f'<div data-testid="e2e-export-run-id" style="display:none;">RUN_ID: {st.session_state.e2e_export_run_id}</div>', unsafe_allow_html=True)
        
        # STEP 3: Top-level downloads (render ONLY from cache, no disk checks)
        if e2e_mode:
            export_state = st.session_state.get("e2e_export_state", "IDLE")
            cache = st.session_state.get("e2e_download_cache")
            cache_error = st.session_state.get("e2e_download_cache_error", "")
            
            sys.stderr.write(f"[E2E DEBUG] STEP 3 downloads: state={export_state}, cache_exists={cache is not None}\n")
            sys.stderr.flush()
            
            if export_state == "PASS":
                sys.stderr.write(f"[E2E DEBUG] Cache check: cache={cache is not None}, 'error' in cache={('error' in cache) if cache else 'N/A'}, cache keys={list(cache.keys()) if cache else 'N/A'}\n")
                sys.stderr.flush()
                if cache and not ("error" in cache):
                    sys.stderr.write(f"[E2E DEBUG] PASS rendering cache section: manifest_json type = {type(cache.get('manifest_json'))}, len = {len(cache.get('manifest_json', b'')) if isinstance(cache.get('manifest_json'), bytes) else 'N/A'}\n")
                    sys.stderr.flush()
                    st.markdown("---")
                    st.markdown("### 📦 Export Artifacts")
                    st.markdown('<div data-testid="e2e-downloads-ready" style="display:none;">READY</div>', unsafe_allow_html=True)
                    
                    # Column 1: Metadata files
                    st.markdown("#### Metadata Files")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown('<div data-testid="e2e-download-manifest">', unsafe_allow_html=True)
                        if cache.get("manifest_json"):
                            st.download_button(
                                "📋 Manifest JSON",
                                data=cache["manifest_json"],
                                file_name="manifest.json",
                                mime="application/json",
                                key="download_manifest_ui"
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div data-testid="e2e-download-validation">', unsafe_allow_html=True)
                        if cache.get("validation_json"):
                            st.download_button(
                                "✅ Validation JSON",
                                data=cache["validation_json"],
                                file_name="validation.json",
                                mime="application/json",
                                key="download_validation_ui"
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown('<div data-testid="e2e-download-section-map">', unsafe_allow_html=True)
                        if cache.get("section_map_json"):
                            st.download_button(
                                "🗺️ Section Map JSON",
                                data=cache["section_map_json"],
                                file_name="section_map.json",
                                mime="application/json",
                                key="download_section_map_ui"
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Deliverables from cache artifacts
                    st.markdown("#### Deliverables")
                    artifacts = cache.get("artifacts", {})
                    if artifacts:
                        for artifact_id, artifact_info in artifacts.items():
                            st.markdown(f'<div data-testid="e2e-download-{artifact_id}">', unsafe_allow_html=True)
                            filename = artifact_info.get("filename", artifact_id)
                            artifact_bytes = artifact_info.get("bytes")
                            sha256 = artifact_info.get("sha256", "unknown")
                            size = artifact_info.get("size", 0)
                            
                            if artifact_bytes:
                                # Infer MIME type from filename
                                if filename.lower().endswith(".pdf"):
                                    mime = "application/pdf"
                                elif filename.lower().endswith(".json"):
                                    mime = "application/json"
                                else:
                                    mime = "application/octet-stream"
                                
                                st.download_button(
                                    f"📄 {filename}",
                                    data=artifact_bytes,
                                    file_name=filename,
                                    mime=mime,
                                    key=f"download_{artifact_id}_ui"
                                )
                                st.caption(f"SHA256: {sha256[:16]}... ({size} bytes)")
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("No deliverable artifacts in cache")
                else:
                    st.markdown("---")
                    st.markdown('<div data-testid="e2e-downloads-error" style="display:none;">ERROR</div>', unsafe_allow_html=True)
                    st.error(f"Downloads cache missing or error: {cache_error or 'unknown'}")
            
            elif export_state == "FAIL":
                st.markdown("---")
                st.markdown('<div data-testid="e2e-downloads-blocked" style="display:none;">BLOCKED</div>', unsafe_allow_html=True)
                st.warning("📛 **Downloads Blocked**: Deliverables are not available due to validation failure.")
                
                # Allow validation + section_map download in FAIL state
                st.markdown("#### Validation Evidence")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div data-testid="e2e-download-validation-fail">', unsafe_allow_html=True)
                    if cache and cache.get("validation_json"):
                        st.download_button(
                            "✅ Validation Report (FAIL)",
                            data=cache["validation_json"],
                            file_name="validation.json",
                            mime="application/json",
                            key="download_validation_fail_ui"
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div data-testid="e2e-download-section-map-fail">', unsafe_allow_html=True)
                    if cache and cache.get("section_map_json"):
                        st.download_button(
                            "🗺️ Section Map",
                            data=cache["section_map_json"],
                            file_name="section_map.json",
                            mime="application/json",
                            key="download_section_map_fail_ui"
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Render violation reason in sentinel for test assertion
                error_msg = st.session_state.get("e2e_export_last_error", "")
                st.markdown(f'<div data-testid="e2e-validation-text">{error_msg}</div>', unsafe_allow_html=True)
                
                # Still allow downloading validation JSON for inspection
                try:
                    from aicmo.validation.runtime_paths import get_runtime_paths
                    paths = get_runtime_paths()
                    validation_path = paths.validation_path
                    
                    if validation_path.exists():
                        st.markdown("#### Validation Report (for debugging)")
                        st.markdown('<div data-testid="e2e-download-validation">', unsafe_allow_html=True)
                        with open(validation_path, 'rb') as f:
                            st.download_button(
                                "⚠️ Download Validation JSON",
                                f.read(),
                                file_name="validation.json",
                                mime="application/json",
                                key="download_validation_fail_ui"
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error loading validation for inspection: {e}")

        st.markdown("---")
        st.markdown("#### Creatives / Assets Bundle")
        st.info("ZIP format includes strategy documents, creatives, persona cards, and assets.")

# ═══════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════

elif nav == "🛡️ Operator QC":
    # Import and run the operator_qc module
    try:
        from streamlit_pages.operator_qc import main as operator_qc_main

        operator_qc_main()
    except ImportError as e:
        st.error(f"Operator QC module not available: {e}")
    except Exception as e:
        st.error(f"Error loading Operator QC: {e}")

elif nav == "Settings":
    st.subheader("Settings & Diagnostics")
    
    # E2E Mode Controls
    e2e_mode = os.getenv('AICMO_E2E_MODE') == '1'
    if e2e_mode:
        st.markdown("### 🧪 E2E Test Mode Controls")
        st.info("E2E mode is ACTIVE")
        
        # Show current paths
        try:
            from aicmo.validation import get_runtime_paths
            paths = get_runtime_paths()
            
            st.json(paths.to_dict())
            
            # Hard reset button
            if st.button("🔄 Hard Reset E2E State", type="secondary", key="e2e_hard_reset"):
                import shutil
                from aicmo.validation import reset_runtime_paths
                
                # Delete artifact directory
                if paths.run_dir.exists():
                    shutil.rmtree(paths.run_dir)
                    st.success(f"Deleted {paths.run_dir}")
                
                # Reset paths singleton
                reset_runtime_paths()
                
                # Clear session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                
                st.success("E2E state reset complete")
                st.rerun()
                
        except Exception as e:
            st.error(f"E2E controls error: {e}")
        
        st.markdown("---")
    
    # Rest of settings...
    st.markdown("### General Settings")
    st.write("Additional settings coming soon...")
    st.subheader("Settings & Diagnostics")

    st.markdown('<div class="aicmo-card">', unsafe_allow_html=True)
    st.markdown("### Connection check")
    if st.button("Ping backend /health", use_container_width=True):
        try:
            resp = call_backend("GET", api_base, "/health", timeout=int(timeout))
            st.success(f"Backend responded: {resp.status_code} – {resp.text[:200]}")
        except Exception as exc:
            st.error(f"Health check failed: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

    # STEP 4: Admin smoke test panel
    st.markdown('<div class="aicmo-card">', unsafe_allow_html=True)
    st.markdown("### 🚀 Admin: Smoke Test All Packs")
    st.caption("⚠️ Requires LLM keys configured. Runs all packs end-to-end.")

    admin_password = st.text_input("Admin password", type="password", key="smoke_pw")
    if st.button("🔥 Run Full Smoke Test", use_container_width=True):
        if admin_password != "admin123":  # Replace with env var in production
            st.error("❌ Invalid admin password")
        else:
            with st.spinner("Running smoke tests for all packs..."):
                try:
                    result = subprocess.run(
                        ["python", "scripts/smoke_run_all_packs.py"],
                        capture_output=True,
                        text=True,
                        timeout=300,
                        cwd="/workspaces/AICMO",
                    )
                    st.success("✅ Smoke test completed")
                    with st.expander("📋 Test Output", expanded=True):
                        st.code(result.stdout, language="text")
                        if result.stderr:
                            st.warning("Stderr:")
                            st.code(result.stderr, language="text")
                except subprocess.TimeoutExpired:
                    st.error("❌ Smoke test timed out (>5 minutes)")
                except Exception as exc:
                    st.error(f"❌ Smoke test failed: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

    # STEP 3: Admin live LLM verification
    st.markdown('<div class="aicmo-card">', unsafe_allow_html=True)
    st.markdown("### 🔬 Admin: Live LLM Verification")
    st.caption("⚠️ Requires LLM keys. Tests real packs with production API.")

    if st.button("🧪 Run Live LLM Check", use_container_width=True, key="live_llm_check"):
        with st.spinner("Running live LLM verification..."):
            try:
                result = subprocess.run(
                    ["python", "scripts/check_llm_live.py"],
                    capture_output=True,
                    text=True,
                    timeout=180,  # 3 minutes
                    cwd="/workspaces/AICMO",
                )

                # Check exit code
                if result.returncode == 0:
                    st.success("✅ All live LLM tests PASSED")
                else:
                    st.error(f"❌ Live LLM tests FAILED (exit code: {result.returncode})")

                # Show output
                with st.expander("📋 Test Output", expanded=True):
                    # Filter out backend logs for cleaner display
                    output_lines = result.stdout.split("\n")
                    filtered_lines = [
                        line
                        for line in output_lines
                        if not line.startswith("2025-") and not line.startswith("[LLM Enhance]")
                    ]
                    st.code("\n".join(filtered_lines), language="text")

                    if result.stderr:
                        st.warning("Stderr:")
                        st.code(result.stderr, language="text")

            except subprocess.TimeoutExpired:
                st.error("❌ Live LLM check timed out (>3 minutes)")
            except Exception as exc:
                st.error(f"❌ Live LLM check failed: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="aicmo-card">', unsafe_allow_html=True)
    st.markdown("### Advanced toggles")
    safe_mode = st.checkbox("Use stub/safe mode where available", value=False)
    verbose = st.checkbox("Verbose logging (dev only)", value=False)
    st.caption(
        "Wire these flags into your backend calls via headers / query params if you support them."
    )
    st.markdown("</div>", unsafe_allow_html=True)
