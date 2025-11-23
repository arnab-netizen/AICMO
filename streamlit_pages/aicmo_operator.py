import io
import json
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

# Ensure project root is in PYTHONPATH for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests  # noqa: E402
import streamlit as st  # noqa: E402
from openai import OpenAI  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

# Try to import creative directions if available
if TYPE_CHECKING:
    from aicmo.creative.directions_engine import CreativeDirection
else:
    try:
        from aicmo.creative.directions_engine import CreativeDirection
    except Exception:  # optional, feature gate if not available
        CreativeDirection = None  # type: ignore

# Try to import humanization wrapper for post-processing
try:
    from backend.humanization_wrapper import default_wrapper as humanizer
except Exception:  # optional, feature gate if not available
    humanizer = None  # type: ignore

# Try to import industry presets if available
try:
    from aicmo.presets.industry_presets import INDUSTRY_PRESETS
except Exception:  # optional dependency
    INDUSTRY_PRESETS: Dict[str, Any] = {}

# PDF export availability flag
try:
    from backend.export.pdf_utils import ensure_pdf_for_report

    PDF_EXPORT_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    ensure_pdf_for_report = None  # type: ignore[assignment]
    PDF_EXPORT_AVAILABLE = False


# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="AICMO Operator – Premium",
    layout="wide",
)


# -------------------------------------------------
# Helper functions
# -------------------------------------------------


def remove_placeholders(text: str) -> str:
    """Remove common placeholder text that indicates incomplete generation."""
    if not text:
        return text

    forbidden = [
        "not yet summarised",
        "will be refined later",
        "N/A",
        "Not specified",
        "undefined",
    ]
    for f in forbidden:
        text = text.replace(f, "")
    return text


def _slugify_filename(value: str, default: str = "aicmo_report") -> str:
    """Convert a string into a safe filename."""
    value = (value or "").strip() or default
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or default


def _directions_to_markdown(directions: List[Any]) -> str:
    """Convert creative directions to markdown format."""
    lines: List[str] = []
    for idx, d in enumerate(directions, start=1):
        lines.append(f"## Direction {idx}: {d.name}")
        if d.tagline:
            lines.append(f"**Tagline:** {d.tagline}")
        if d.description:
            lines.append("")
            lines.append(d.description)
        if d.visual_style:
            lines.append("")
            lines.append(f"**Visual style:** {d.visual_style}")
        if d.color_directions:
            lines.append(f"**Color direction:** {d.color_directions}")
        if d.tone_voice:
            lines.append(f"**Tone & voice:** {d.tone_voice}")
        if d.messaging_pillars:
            lines.append("")
            lines.append("**Messaging pillars:**")
            for p in d.messaging_pillars:
                lines.append(f"- {p}")
        if d.example_hooks:
            lines.append("")
            lines.append("**Example hooks:**")
            for h in d.example_hooks:
                lines.append(f"- {h}")
        if d.example_post_ideas:
            lines.append("")
            lines.append("**Example post ideas:**")
            for idea in d.example_post_ideas:
                lines.append(f"- {idea}")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def _report_with_creative_directions(report_obj: Any) -> Any:
    """Merge creative directions markdown into report for deck export."""
    cd_md = st.session_state.get("creative_directions_markdown")
    if not cd_md:
        return report_obj

    # Best-effort conversion to dict
    try:
        if hasattr(report_obj, "model_dump"):
            base = report_obj.model_dump()
        elif hasattr(report_obj, "dict"):
            base = report_obj.dict()
        elif hasattr(report_obj, "__dict__"):
            base = dict(report_obj.__dict__)
        elif isinstance(report_obj, dict):
            base = dict(report_obj)
        else:
            base = {"raw": str(report_obj)}
    except Exception:
        base = {"raw": str(report_obj)}

    base["creative_directions"] = cd_md
    return base


# -------------------------------------------------
# Package presets (Fiverr/Upwork-style)
# -------------------------------------------------
PACKAGE_PRESETS: Dict[str, Dict[str, bool]] = {
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
    "Full-Funnel Growth Suite (Premium)": {
        "marketing_plan": True,
        "campaign_blueprint": True,
        "social_calendar": True,
        "performance_review": True,
        "creatives": True,
        "include_agency_grade": True,
    },
    # SPECIALISED PACKAGES
    "Launch & GTM Pack": {
        "marketing_plan": True,
        "campaign_blueprint": True,
        "social_calendar": True,
        "performance_review": False,
        "creatives": True,
        "include_agency_grade": True,
    },
    "Brand Turnaround Lab": {
        "marketing_plan": True,
        "campaign_blueprint": True,
        "social_calendar": False,
        "performance_review": True,
        "creatives": True,
        "include_agency_grade": True,
    },
    "Retention & CRM Booster": {
        "marketing_plan": True,
        "campaign_blueprint": False,
        "social_calendar": True,
        "performance_review": True,
        "creatives": False,
        "include_agency_grade": False,
    },
    "Performance Audit & Revamp": {
        "marketing_plan": False,
        "campaign_blueprint": False,
        "social_calendar": False,
        "performance_review": True,
        "creatives": False,
        "include_agency_grade": True,
    },
    "PR & Reputation Pack": {
        "marketing_plan": True,
        "campaign_blueprint": True,
        "social_calendar": False,
        "performance_review": False,
        "creatives": True,
        "include_agency_grade": True,
    },
    "Always-on Content Engine": {
        "marketing_plan": False,
        "campaign_blueprint": False,
        "social_calendar": True,
        "performance_review": True,
        "creatives": True,
        "include_agency_grade": False,
    },
}

# -------------------------------------------------
# WOW Templates mapping (dropdown label → internal package key)
# -------------------------------------------------
PACKAGE_KEY_BY_LABEL: Dict[str, str] = {
    "Quick Social Pack (Basic)": "quick_social_basic",
    "Strategy + Campaign Pack (Standard)": "strategy_campaign_standard",
    "Full-Funnel Growth Suite (Premium)": "full_funnel_premium",
    "Launch & GTM Pack": "launch_gtm",
    "Brand Turnaround Lab": "brand_turnaround",
    "Retention & CRM Booster": "retention_crm",
    "Performance Audit & Revamp": "performance_audit",
}

# -------------------------------------------------
# Refinement modes
# -------------------------------------------------
REFINEMENT_MODES: Dict[str, Dict[str, Any]] = {
    "Fast draft": {
        "passes": 1,
        "max_tokens": 3000,
        "temperature": 0.9,
        "label": "Fast first draft – good for internal thinking, not client-ready.",
    },
    "Balanced": {
        "passes": 2,
        "max_tokens": 6000,
        "temperature": 0.7,
        "label": "Balanced quality + speed – default for most projects.",
    },
    "Agency-grade": {
        "passes": 3,
        "max_tokens": 9000,
        "temperature": 0.6,
        "label": "Polished, top-agency style with layered passes.",
    },
    "Deep audit": {
        "passes": 2,
        "max_tokens": 7000,
        "temperature": 0.4,
        "include_audit": True,
        "label": "Adds critique, teardown, and risk flags to the output.",
    },
}


# -------------------------------------------------
# Database (Neon via DATABASE_URL / DB_URL) - Optional
# -------------------------------------------------
DB_URL = os.getenv("DB_URL") or os.getenv("DATABASE_URL")
_db_available = bool(DB_URL)


@st.cache_resource
def get_engine() -> Optional[Engine]:
    """
    Return a cached SQLAlchemy engine for the configured DB.
    Returns None if DATABASE_URL/DB_URL not set (graceful fallback).
    """
    if not DB_URL:
        return None
    return create_engine(DB_URL, pool_pre_ping=True, future=True)


def ensure_learn_table() -> None:
    """
    Create the learn-items table if it doesn't exist.
    This is idempotent and safe to call multiple times.
    Only runs if database is configured.
    """
    engine = get_engine()
    if not engine:
        return  # Database not configured, skip
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS aicmo_learn_items (
                        id SERIAL PRIMARY KEY,
                        kind TEXT NOT NULL,
                        filename TEXT,
                        size_bytes BIGINT,
                        notes TEXT,
                        tags JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
            )
    except Exception as e:
        st.warning(f"Database table creation skipped: {e}")


# -------------------------------------------------
# Learn-store backed by Neon (Postgres) or memory fallback
# -------------------------------------------------
@st.session_state.setdefault
def _get_memory_learn_store() -> List[Dict[str, Any]]:
    """Fallback in-memory store when database is not available."""
    return []


def load_learn_items() -> List[Dict[str, Any]]:
    """
    Load all learn items from Neon, or from memory if DB unavailable.
    Returns a list of dicts:
    {
        "kind": "good" | "bad",
        "filename": str | None,
        "size_bytes": int | None,
        "notes": str,
        "tags": list[str],
        "created_at": ISO timestamp | None
    }
    """
    engine = get_engine()
    if not engine:
        # Fallback to memory store
        return st.session_state.get("_memory_learn_store", [])

    try:
        ensure_learn_table()
        with engine.begin() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        kind,
                        filename,
                        size_bytes,
                        notes,
                        tags,
                        created_at
                    FROM aicmo_learn_items
                    ORDER BY created_at DESC
                    """
                )
            ).mappings()

            items: List[Dict[str, Any]] = []
            for r in rows:
                tags = r.get("tags") or []
                # tags may already be a list if SQLAlchemy decodes jsonb, or a JSON string
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except json.JSONDecodeError:
                        tags = []

                created_at = r.get("created_at")
                items.append(
                    {
                        "kind": r.get("kind"),
                        "filename": r.get("filename"),
                        "size_bytes": r.get("size_bytes"),
                        "notes": r.get("notes") or "",
                        "tags": tags,
                        "created_at": created_at.isoformat() if created_at else None,
                    }
                )
            return items
    except Exception as e:
        # Fallback to memory store on any database error
        st.warning(f"Using in-memory learn store: {e}")
        return st.session_state.get("_memory_learn_store", [])


def append_learn_item(item: Dict[str, Any]) -> None:
    """
    Insert a learn item into Neon, or into memory store if DB unavailable.
    `item` is expected to have: kind, filename, size_bytes, notes, tags.
    """
    engine = get_engine()
    if not engine:
        # Fallback to memory store
        if "_memory_learn_store" not in st.session_state:
            st.session_state._memory_learn_store = []
        st.session_state._memory_learn_store.append(item)
        return

    try:
        ensure_learn_table()
        tags = item.get("tags") or []
        if not isinstance(tags, (list, dict)):
            # defensive: if someone passes a string, wrap in list
            tags = [str(tags)]

        payload = {
            "kind": item.get("kind") or "good",
            "filename": item.get("filename"),
            "size_bytes": int(item.get("size_bytes") or 0),
            "notes": item.get("notes") or "",
            "tags": tags,  # Pass Python list/dict; SQLAlchemy handles JSON conversion
        }

        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO aicmo_learn_items (kind, filename, size_bytes, notes, tags)
                    VALUES (:kind, :filename, :size_bytes, :notes, :tags)
                    """
                ),
                payload,
            )
    except Exception as e:
        # Fallback to memory store on any database error
        st.warning(f"Item saved to memory (DB error): {e}")
        if "_memory_learn_store" not in st.session_state:
            st.session_state._memory_learn_store = []
        st.session_state._memory_learn_store.append(item)


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def init_session_state() -> None:
    defaults: Dict[str, Any] = {
        "selected_package": list(PACKAGE_PRESETS.keys())[0],
        "services": PACKAGE_PRESETS[list(PACKAGE_PRESETS.keys())[0]].copy(),
        "refinement_mode": "Balanced",
        "client_brief_text": "",
        "client_brief_meta": {},
        "upload_buffer": None,
        "draft_report": "",
        "final_report": "",
        "feedback_notes": "",
        "feedback_history": [],
        "last_backend_payload": None,
        "industry_preset": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def build_services_matrix() -> Dict[str, bool]:
    """
    Build / modify the services selection matrix via 3 expanders.
    """
    services = st.session_state["services"]

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.expander("Strategy & Research"):
            services["marketing_plan"] = st.checkbox(
                "Full marketing plan",
                value=services.get("marketing_plan", False),
                help="Positioning, audience, funnel, channels, budget split.",
            )
            services["brand_audit"] = st.checkbox(
                "Brand & competitor audit",
                value=services.get("brand_audit", False),
            )
            services["audience_research"] = st.checkbox(
                "Audience personas & JTBD",
                value=services.get("audience_research", False),
            )

    with col2:
        with st.expander("Campaign & Content"):
            services["campaign_blueprint"] = st.checkbox(
                "Campaign blueprint",
                value=services.get("campaign_blueprint", False),
                help="Big idea, pillars, hooks, examples.",
            )
            services["social_calendar"] = st.checkbox(
                "Social/content calendar",
                value=services.get("social_calendar", False),
            )
            services["creatives"] = st.checkbox(
                "Copy + creative directions",
                value=services.get("creatives", False),
            )

    with col3:
        with st.expander("Measurement & Optimisation"):
            services["performance_review"] = st.checkbox(
                "Performance review / audit",
                value=services.get("performance_review", False),
            )
            services["testing_roadmap"] = st.checkbox(
                "Testing & experiment roadmap",
                value=services.get("testing_roadmap", False),
            )
            services["include_agency_grade"] = st.checkbox(
                "Agency-grade polish",
                value=services.get("include_agency_grade", False),
                help="Extra time for structure, polish, and storytelling.",
            )

    st.session_state["services"] = services
    return services


def summarise_upload(uploaded_file: Optional[io.BytesIO]) -> Dict[str, Any]:
    if uploaded_file is None:
        return {}
    return {
        "filename": uploaded_file.name,
        "size_bytes": len(uploaded_file.getvalue()),
        "type": uploaded_file.type,
    }


def get_refinement_mode() -> Tuple[str, Dict[str, Any]]:
    mode_name = st.session_state.get("refinement_mode", "Balanced")
    config = REFINEMENT_MODES.get(mode_name, REFINEMENT_MODES["Balanced"])
    return mode_name, config


def build_client_brief_payload() -> Dict[str, Any]:
    """
    Build a generic client-brief payload dict from session state.
    This is designed to be flexible with backend models.
    """
    return {
        "client_name": st.session_state["client_brief_meta"].get("client_name"),
        "brand_name": st.session_state["client_brief_meta"].get("brand_name"),
        "product_service": st.session_state["client_brief_meta"].get("product_service"),
        "industry": st.session_state["client_brief_meta"].get("industry"),
        "geography": st.session_state["client_brief_meta"].get("geography"),
        "objectives": st.session_state["client_brief_meta"].get("objectives"),
        "budget": st.session_state["client_brief_meta"].get("budget"),
        "timeline": st.session_state["client_brief_meta"].get("timeline"),
        "constraints": st.session_state["client_brief_meta"].get("constraints"),
        "raw_brief_text": st.session_state["client_brief_text"],
        "uploaded_brief_meta": summarise_upload(st.session_state.get("upload_buffer")),
    }


def call_backend_generate(
    stage: str,  # "draft" | "refine" | "final"
    extra_feedback: str = "",
) -> Optional[str]:
    """
    Main integration point:
    - builds payload
    - calls backend API if configured
    - falls back to local OpenAI call if needed
    - returns markdown report or None on failure
    """
    client_payload = build_client_brief_payload()
    services = st.session_state["services"]
    package_name = st.session_state["selected_package"]
    refinement_name, refinement_cfg = get_refinement_mode()
    learn_items = load_learn_items()

    # Resolve WOW package key from the selected package label
    wow_package_key = PACKAGE_KEY_BY_LABEL.get(package_name)

    payload: Dict[str, Any] = {
        "stage": stage,
        "client_brief": client_payload,
        "services": services,
        "package_name": package_name,
        "wow_enabled": bool(wow_package_key),  # Enable WOW if we have a valid key
        "wow_package_key": wow_package_key,
        "refinement_mode": {
            "name": refinement_name,
            **refinement_cfg,
        },
        "feedback": extra_feedback,
        "previous_draft": st.session_state.get("draft_report") or "",
        "learn_items": learn_items,
        "use_learning": len(learn_items) > 0,  # ✅ Enable memory engine if training data exists
        "industry_preset": st.session_state.get("industry_preset"),
    }

    st.session_state["last_backend_payload"] = payload

    base_url = os.environ.get("AICMO_BACKEND_URL")
    if base_url:
        try:
            resp = requests.post(
                base_url.rstrip("/") + "/api/aicmo/generate_report",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            # Expecting {"report_markdown": "...", ...}
            if isinstance(data, dict) and "report_markdown" in data:
                return data["report_markdown"]
        except Exception as e:  # pragma: no cover - UX only
            st.error("Backend API call failed, falling back to direct model call.")
            st.exception(e)

    # Fallback: direct OpenAI call
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("OPENAI_API_KEY not set; cannot generate report.")
            return None

        client = OpenAI(api_key=api_key)

        system_prompt = (
            "You are AICMO, a senior strategist at a top-tier global marketing agency. "
            "You create structured, client-ready marketing deliverables: marketing plans, "
            "campaign blueprints, social calendars, performance reviews, and creative directions. "
            "Your writing is clear, structured, and presentation-ready."
        )

        # We pass the whole payload as JSON inside the user message.
        user_prompt = (
            "Generate a client-ready marketing deliverable in markdown based on the JSON below.\n\n"
            "JSON payload:\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
            "Output guidelines:\n"
            "- Use H1/H2/H3 headings\n"
            "- Use bullet lists where helpful\n"
            "- Include channel-wise recommendations\n"
            "- Make it directly usable as a client deck outline or report."
        )

        completion = client.chat.completions.create(
            model=os.environ.get("AICMO_OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=refinement_cfg.get("max_tokens", 6000),
            temperature=refinement_cfg.get("temperature", 0.7),
        )
        return completion.choices[0].message.content or ""
    except Exception as e:  # pragma: no cover - UX only
        st.error("Model call failed.")
        st.exception(e)
        return None


def _apply_humanization(
    text: str,
    brand_name: Optional[str] = None,
    objectives: Optional[str] = None,
) -> str:
    """
    Apply the humanization wrapper to make output sound less AI-like.
    Gracefully degrades if humanizer is not available.
    """
    if humanizer is None or not text:
        return text

    brand_voice = f"Brand: {brand_name}" if brand_name else None
    extra_context = f"Objectives: {objectives}" if objectives else None

    try:
        return humanizer.process_text(
            text,
            brand_voice=brand_voice,
            extra_context=extra_context,
        )
    except Exception:
        # Fail soft: return original text
        return text


# -------------------------------------------------
# UI Sections
# -------------------------------------------------
def render_header() -> None:
    st.title("AICMO Operator – Premium Dashboard")
    st.caption(
        "Attach client briefs → choose a package → generate agency-grade reports → refine → export."
    )


def render_client_input_tab() -> None:
    st.subheader("1️⃣ Client Input & Package Selection")

    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        st.markdown("#### Client brief")

        uploaded = st.file_uploader(
            "Attach client brief (PDF, DOCX, TXT, PPT, etc.)",
            type=[
                "pdf",
                "docx",
                "txt",
                "md",
                "pptx",
                "ppt",
            ],
        )
        if uploaded is not None:
            st.session_state["upload_buffer"] = uploaded

        st.session_state["client_brief_text"] = st.text_area(
            "Or paste key brief details here",
            value=st.session_state.get("client_brief_text", ""),
            height=220,
            placeholder="Objectives, target audience, geography, budget, timing, mandatories, etc.",
        )

        with st.expander("Brief meta (optional but recommended)", expanded=False):
            meta = st.session_state.get("client_brief_meta", {}) or {}
            meta["client_name"] = st.text_input(
                "Client / company",
                value=meta.get("client_name", ""),
            )
            meta["brand_name"] = st.text_input(
                "Brand / product name",
                value=meta.get("brand_name", ""),
            )
            meta["product_service"] = st.text_input(
                "Product / service",
                value=meta.get("product_service", ""),
            )
            meta["industry"] = st.text_input(
                "Industry / category",
                value=meta.get("industry", ""),
            )
            meta["geography"] = st.text_input(
                "Primary geography / market",
                value=meta.get("geography", ""),
            )
            meta["objectives"] = st.text_area(
                "Primary objectives",
                value=meta.get("objectives", ""),
                height=80,
            )
            meta["budget"] = st.text_input(
                "Budget (if known)",
                value=meta.get("budget", ""),
            )
            meta["timeline"] = st.text_input(
                "Key timings / launch dates",
                value=meta.get("timeline", ""),
            )
            meta["constraints"] = st.text_area(
                "Mandatories / constraints",
                value=meta.get("constraints", ""),
                height=80,
            )

            st.session_state["client_brief_meta"] = meta

        with st.expander("Industry presets (optional)", expanded=False):
            if INDUSTRY_PRESETS:
                preset_names = list(INDUSTRY_PRESETS.keys())
                selected = st.selectbox(
                    "Select industry preset",
                    options=["None"] + preset_names,
                    index=0,
                )
                if selected != "None":
                    st.session_state["industry_preset"] = INDUSTRY_PRESETS[selected]
            else:
                st.info("No industry presets available in this environment.")

    with col_right:
        st.markdown("#### Package & services")

        pkg_name = st.selectbox(
            "Select package",
            options=list(PACKAGE_PRESETS.keys()),
            index=list(PACKAGE_PRESETS.keys()).index(
                st.session_state.get("selected_package", list(PACKAGE_PRESETS.keys())[0])
            ),
        )
        if pkg_name != st.session_state["selected_package"]:
            st.session_state["selected_package"] = pkg_name
            st.session_state["services"] = PACKAGE_PRESETS[pkg_name].copy()

        st.markdown("##### Service matrix")
        build_services_matrix()

        st.markdown("##### 📘 WOW Package Preview")
        if pkg_name:
            st.info(f"**Selected Package:** {pkg_name}")
            st.markdown(
                """
This will generate an agency-grade WOW report with:
- ✨ Branded template
- 📅 14/30 day content calendar  
- 📝 10+ captions
- 🎬 Reel ideas
- #️⃣ Hashtag banks
- 🏆 Competitor benchmark  
- 📧 Email sequences (select packages)
- 🎯 Landing page wireframe (premium)
            """
            )

        st.markdown("##### Refinement mode")
        mode_names = list(REFINEMENT_MODES.keys())
        current_mode = st.session_state.get("refinement_mode", "Balanced")
        idx = mode_names.index(current_mode) if current_mode in mode_names else 1
        selected_mode = st.radio(
            "Depth & quality level",
            options=mode_names,
            index=idx,
        )
        st.session_state["refinement_mode"] = selected_mode
        st.caption(REFINEMENT_MODES[selected_mode]["label"])

        if st.button("Generate draft report", type="primary", use_container_width=True):
            with st.spinner("Generating draft report with AICMO..."):
                report_md = call_backend_generate(stage="draft")
            if report_md:
                # Apply humanization layer to make it sound less AI-like
                brand_name = st.session_state["client_brief_meta"].get("brand_name")
                objectives = st.session_state["client_brief_meta"].get("objectives")
                humanized_report = _apply_humanization(report_md, brand_name, objectives)
                st.session_state["draft_report"] = humanized_report
                st.toast("Draft report generated. Go to the Workshop tab.", icon="✅")


def render_workshop_tab() -> None:
    st.subheader("2️⃣ Workshop – Review & Ask AICMO to Improve")

    if not st.session_state.get("draft_report"):
        st.info("No draft yet. Generate a draft from the Client Input tab first.")
        return

    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown("#### Working draft (editable)")
        edited = st.text_area(
            "You can lightly edit this before sending feedback.",
            value=st.session_state.get("draft_report", ""),
            height=520,
        )
        st.session_state["draft_report"] = edited

    with col_right:
        st.markdown("#### Feedback to AICMO")
        st.session_state["feedback_notes"] = st.text_area(
            "Tell AICMO what to improve, add, remove, or reframe.",
            value=st.session_state.get("feedback_notes", ""),
            height=240,
            placeholder=(
                "Examples:\n"
                "- Make the tone more conversational for founders\n"
                "- Add more India-specific channel ideas\n"
                "- Tighten the KPIs and measurement section\n"
                "- Add a section for risks and mitigation"
            ),
        )

        st.markdown("#### Refinement")
        col_a, col_b = st.columns(2)
        with col_a:
            bump_depth = st.checkbox(
                "Bump refinement one level up for this pass",
                value=False,
                help="Temporarily use a deeper mode without changing the default.",
            )
        with col_b:
            show_last_payload = st.checkbox(
                "Show last backend payload (for debugging)",
                value=False,
            )

        if st.button("Apply feedback & regenerate", type="primary", use_container_width=True):
            with st.spinner("Refining draft with AICMO..."):
                original_mode = st.session_state["refinement_mode"]
                if bump_depth:
                    mode_names = list(REFINEMENT_MODES.keys())
                    idx = mode_names.index(original_mode)
                    if idx < len(mode_names) - 1:
                        st.session_state["refinement_mode"] = mode_names[idx + 1]

                refined_md = call_backend_generate(
                    stage="refine",
                    extra_feedback=st.session_state.get("feedback_notes", ""),
                )

                # restore mode
                st.session_state["refinement_mode"] = original_mode

            if refined_md:
                # Apply humanization layer to refined output
                brand_name = st.session_state["client_brief_meta"].get("brand_name")
                objectives = st.session_state["client_brief_meta"].get("objectives")
                humanized_refined = _apply_humanization(refined_md, brand_name, objectives)

                history = st.session_state.get("feedback_history", [])
                history.append(
                    {
                        "feedback": st.session_state.get("feedback_notes", ""),
                        "draft_snapshot": st.session_state.get("draft_report", ""),
                    }
                )
                st.session_state["feedback_history"] = history
                st.session_state["draft_report"] = humanized_refined
                st.toast("Draft refined. Review the updated version on the left.", icon="✨")

        if show_last_payload and st.session_state.get("last_backend_payload"):
            st.markdown("##### Debug – last payload sent to backend")
            st.json(st.session_state["last_backend_payload"])


def render_final_output_tab() -> None:
    st.subheader("3️⃣ Final Output – Export Client-Ready Report")

    if not st.session_state.get("draft_report") and not st.session_state.get("final_report"):
        st.info("No content yet. Generate and refine a draft first.")
        return

    if not st.session_state.get("final_report"):
        st.session_state["final_report"] = st.session_state.get("draft_report", "")

    st.markdown("#### Final report preview")
    st.markdown(st.session_state["final_report"])

    st.markdown("---")
    st.markdown("#### Export")

    as_markdown = st.session_state["final_report"]
    md_bytes = as_markdown.encode("utf-8")
    st.download_button(
        "⬇️ Download as Markdown (.md)",
        data=md_bytes,
        file_name="aicmo_report.md",
        mime="text/markdown",
    )

    # Also export as simple text
    st.download_button(
        "⬇️ Download as Text (.txt)",
        data=md_bytes,
        file_name="aicmo_report.txt",
        mime="text/plain",
    )

    # --- PDF EXPORT SECTION ---
    with st.expander("📄 Export as PDF", expanded=False):
        if not PDF_EXPORT_AVAILABLE:
            st.info(
                "PDF export isn't available in this deployment because the backend "
                "PDF module isn't loaded. Deploy the full backend to enable this feature."
            )
        else:
            if st.button("Generate PDF", key="btn_generate_pdf", use_container_width=True):
                if not st.session_state.get("final_report"):
                    st.warning("Generate a report first before exporting to PDF.")
                else:
                    with st.spinner("Generating PDF report…"):
                        try:
                            # Ensure PDF metadata is tracked for the report
                            ensure_pdf_for_report(
                                report_id=st.session_state.get("report_id", "aicmo_report"),
                                markdown=st.session_state["final_report"],
                                meta={
                                    "title": st.session_state.get("client_brief_meta", {}).get(
                                        "brand_name", "AICMO Report"
                                    ),
                                    "report_type": "Final Output",
                                },
                            )

                            # For now, we'll generate simple PDF bytes from markdown
                            # In production, integrate with your PDF library
                            pdf_bytes = st.session_state.get("_pdf_bytes")
                            if not pdf_bytes:
                                # Fallback: convert markdown to text for PDF
                                pdf_text = st.session_state["final_report"].encode("utf-8")
                                st.session_state["_pdf_bytes"] = pdf_text
                                pdf_bytes = pdf_text

                            if pdf_bytes:
                                st.download_button(
                                    "⬇️ Download PDF",
                                    data=pdf_bytes,
                                    file_name="aicmo_report.pdf",
                                    mime="application/pdf",
                                    key="btn_download_pdf",
                                    use_container_width=True,
                                )
                        except Exception as e:
                            st.error(f"PDF generation failed: {str(e)}")

    if st.button("Mark this as final & lock draft", use_container_width=True):
        st.toast("Final report locked for this project.", icon="🔒")


def render_learn_tab() -> None:
    st.subheader("4️⃣ Learn – Teach AICMO Using Gold-Standard Reports")

    st.markdown(
        "Use this area to feed AICMO examples from top agencies: great decks, reports, "
        "calendars, and audits. These are not sent to clients; they are only used as "
        "learning references to shape future outputs."
    )

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown("#### Section A – Good / gold-standard examples")
        good_file = st.file_uploader(
            "Upload a strong example (PDF, PPTX, DOCX, etc.)",
            type=["pdf", "pptx", "ppt", "docx", "txt", "md"],
            key="learn_good_file",
        )
        good_notes = st.text_area(
            "What makes this good? (structure, tone, visuals, etc.)",
            key="learn_good_notes",
            height=140,
        )
        good_tags = st.text_input(
            "Tags (comma-separated, e.g.: B2B SaaS, GTM, launch, India)",
            key="learn_good_tags",
        )

        if st.button("Save good example", key="save_good_example", use_container_width=True):
            if good_file is None:
                st.warning("Attach a file before saving.")
            else:
                item = {
                    "kind": "good",
                    "filename": good_file.name,
                    "size_bytes": len(good_file.getvalue()),
                    "notes": good_notes,
                    "tags": [t.strip() for t in good_tags.split(",") if t.strip()],
                }
                append_learn_item(item)
                st.toast("Saved good example for learning.", icon="✅")

    with col_b:
        st.markdown("#### Section B – Weak / needs-improvement examples")
        bad_file = st.file_uploader(
            "Upload a weak / problematic example",
            type=["pdf", "pptx", "ppt", "docx", "txt", "md"],
            key="learn_bad_file",
        )
        bad_notes = st.text_area(
            "What is weak here? (messy structure, vague KPIs, poor storytelling, etc.)",
            key="learn_bad_notes",
            height=140,
        )
        bad_tags = st.text_input(
            "Tags (comma-separated)",
            key="learn_bad_tags",
        )

        if st.button("Save weak example", key="save_bad_example", use_container_width=True):
            if bad_file is None:
                st.warning("Attach a file before saving.")
            else:
                item = {
                    "kind": "bad",
                    "filename": bad_file.name,
                    "size_bytes": len(bad_file.getvalue()),
                    "notes": bad_notes,
                    "tags": [t.strip() for t in bad_tags.split(",") if t.strip()],
                }
                append_learn_item(item)
                st.toast("Saved weak example for learning.", icon="⚠️")

    st.markdown("---")
    all_items = load_learn_items()
    if all_items:
        st.markdown("#### Stored learning examples")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total examples",
                len(all_items),
            )
        with col2:
            st.metric(
                "Gold-standard",
                sum(1 for i in all_items if i.get("kind") == "good"),
            )
        with col3:
            st.metric(
                "Weak / anti-patterns",
                sum(1 for i in all_items if i.get("kind") == "bad"),
            )

        with st.expander("View raw learn-store items"):
            st.json(all_items)
    else:
        st.info("No learning examples saved yet. Start by uploading a few gold-standard decks.")


def main() -> None:
    init_session_state()
    render_header()

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Client Input",
            "Workshop",
            "Final Output",
            "Learn",
        ]
    )

    with tab1:
        render_client_input_tab()
    with tab2:
        render_workshop_tab()
    with tab3:
        render_final_output_tab()
    with tab4:
        render_learn_tab()


if __name__ == "__main__":
    main()
