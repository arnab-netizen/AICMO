"""AICMO Operator Dashboard – Complete Streamlit Application.

This is a professional workspace for generating, refining, and exporting
client marketing reports. Integrates with backend endpoints:
- /aicmo/generate
- /aicmo/revise
- /aicmo/learn
- /aicmo/export
- /health (diagnostics)
"""

import json
from typing import Any, Dict, Optional

import requests
import streamlit as st

# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG & GLOBAL STYLE
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AICMO Operator Dashboard",
    page_icon="🎯",
    layout="wide",
)

# Modern dark workspace styling
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    section[data-testid="stSidebar"] {
        background-color: #020617;
        color: #e5e7eb;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #e5e7eb;
    }

    .aicmo-card {
        background-color: #020617;
        border-radius: 0.75rem;
        padding: 1rem 1.25rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.35);
        border: 1px solid #1f2937;
    }

    .aicmo-card h3 {
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }

    .aicmo-card p {
        font-size: 0.875rem;
        color: #9ca3af;
        margin-bottom: 0.25rem;
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
    """Call /aicmo/learn endpoint (Phase 5 learning store)."""
    payload = {
        "project_id": project_id,
        "brief": brief,
        "report": final_report,
        "tags": tags,
    }
    resp = call_backend("POST", api_base, "/aicmo/learn", json_body=payload, timeout=timeout)
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
    nav = st.radio(
        "Navigation",
        ["Dashboard", "Brief & Generate", "Workshop", "Learn & Improve", "Export", "Settings"],
        index=0,
    )


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


# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════

if nav == "Dashboard":
    top_left, top_right = st.columns([2, 1])

    with top_left:
        st.markdown('<div class="aicmo-card">', unsafe_allow_html=True)
        st.markdown("### Usage")
        reports = st.session_state.usage_counter["reports"]
        words = st.session_state.usage_counter["words"]
        st.metric("Reports Generated", reports)
        st.metric("Estimated Words Generated", f"{words:,}")
        st.markdown("</div>", unsafe_allow_html=True)

    with top_right:
        st.markdown('<div class="aicmo-card">', unsafe_allow_html=True)
        st.markdown("### Current Project")
        st.markdown(f"**{_safe_get_current_project_name()}**")
        if st.session_state.current_project_id:
            st.caption(f"Project ID: {st.session_state.current_project_id}")
        else:
            st.caption("No project generated yet in this session.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<h3 class="aicmo-section-title">Recent Reports</h3>', unsafe_allow_html=True)
    if not st.session_state.recent_projects:
        st.info(
            "No recent reports yet. Generate your first client report from the **Brief & Generate** tab."
        )
    else:
        cols = st.columns(3)
        for idx, proj in enumerate(st.session_state.recent_projects[:3]):
            with cols[idx % 3]:
                st.markdown('<div class="aicmo-card">', unsafe_allow_html=True)
                st.markdown(f"**{proj.get('name', 'Unnamed project')}**")
                st.caption(proj.get("subtitle", ""))
                if st.button("Open", key=f"open_proj_{idx}", use_container_width=True):
                    st.session_state.current_project_id = proj.get("id")
                    st.session_state.current_brief = proj.get("brief")
                    st.session_state.generated_report = proj.get("report")
                st.markdown("</div>", unsafe_allow_html=True)

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
                    "Calling AICMO (CopyHook) to generate hero variants…", expanded=True
                ) as status:
                    try:
                        result = aicmo_generate(
                            api_base=api_base,
                            brief=brief,
                            industry=selected_industry,
                            outputs=selected_outputs,
                            timeout=int(timeout),
                        )
                        st.session_state.current_brief = brief
                        st.session_state.generated_report = result

                        status.update(label="Variants generated.", state="complete")
                        st.success("CopyHook variants generated successfully.")

                        # Show them in a nice way
                        variants = result.get("variants") or result.get("headlines") or []
                        if variants:
                            for i, v in enumerate(variants, 1):
                                st.markdown(f"### Variant {i}")
                                headline = v.get("headline") or v.get("title") or ""
                                body = v.get("body") or v.get("copy") or ""
                                st.write(f"**{headline}**")
                                if body:
                                    st.write(body)
                                st.markdown("---")
                        else:
                            st.json(result)
                    except Exception as exc:
                        status.update(label="Generation failed.", state="error")
                        st.error(f"Generation failed: {exc}")

# ═══════════════════════════════════════════════════════════════════════
# WORKSHOP (MARKETING PLAN)
# ═══════════════════════════════════════════════════════════════════════

elif nav == "Workshop":
    st.subheader("Step 2 – Workshop & Refine")

    if not st.session_state.generated_report:
        st.info("No draft report yet. Generate one from **Brief & Generate** first.")
    else:
        report = st.session_state.generated_report

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
                st.success("Project sent to learning store.")
                st.json(result)
            except Exception as exc:
                st.error(f"Learning call failed: {exc}")

        st.markdown("---")
        st.markdown("#### Add external reference reports (optional)")
        ref_files = st.file_uploader(
            "Upload top-agency reports / decks to use as reference material",
            type=["pdf", "pptx", "docx"],
            accept_multiple_files=True,
        )
        if ref_files:
            st.warning(
                "Backend wiring needed: send these files to your reference/embedding pipeline."
            )
            st.write([f.name for f in ref_files])

# ═══════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════

elif nav == "Export":
    st.subheader("Step 4 – Export & Delivery")

    if not st.session_state.generated_report:
        st.info("No report available. Generate and refine one first.")
    else:
        st.markdown("#### Export Final Report")
        fmt = st.selectbox(
            "Format",
            ["pdf", "pptx", "zip", "json"],
            index=0,
        )

        if st.button("Generate export file", type="primary"):
            try:
                file_bytes = aicmo_export(
                    api_base=api_base,
                    brief=st.session_state.current_brief,
                    output=st.session_state.generated_report,
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
                )
                st.success("Export ready.")
            except Exception as exc:
                st.error(f"Export failed: {exc}")

        st.markdown("---")
        st.markdown("#### Creatives / Assets Bundle")
        st.info("ZIP format includes strategy documents, creatives, persona cards, and assets.")

# ═══════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════

elif nav == "Settings":
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

    st.markdown('<div class="aicmo-card">', unsafe_allow_html=True)
    st.markdown("### Advanced toggles")
    safe_mode = st.checkbox("Use stub/safe mode where available", value=False)
    verbose = st.checkbox("Verbose logging (dev only)", value=False)
    st.caption(
        "Wire these flags into your backend calls via headers / query params if you support them."
    )
    st.markdown("</div>", unsafe_allow_html=True)
