import io
import json
import os
import re
import sys
import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

# Load .env early
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Ensure project root is in PYTHONPATH for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests  # noqa: E402
import streamlit as st  # noqa: E402
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
        "include_agency_grade": True,
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
    "Full-Funnel Growth Suite (Premium)": "full_funnel_growth_suite",
    "Launch & GTM Pack": "launch_gtm_pack",
    "Brand Turnaround Lab": "brand_turnaround_lab",
    "Retention & CRM Booster": "retention_crm_booster",
    "Performance Audit & Revamp": "performance_audit_revamp",
    "PR & Reputation Pack": "pr_reputation_pack",
    "Always-on Content Engine": "always_on_content_engine",
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
        "max_tokens": 12000,
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
        "industry_key": None,
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


def validate_required_brief_fields() -> Tuple[bool, str]:
    """
    Validate that all required brief fields are filled.

    Returns:
        (is_valid: bool, error_message: str)
    """
    required_fields = {
        "brand_name": "Brand / product name",
        "product_service": "Product / service",
        "industry": "Industry / category",
        "objectives": "Primary objectives",
    }

    meta = st.session_state.get("client_brief_meta", {})
    missing_fields = []

    for field_key, field_label in required_fields.items():
        value = (meta.get(field_key, "") or "").strip()
        if not value:
            missing_fields.append(field_label)

    if missing_fields:
        message = f"Required fields missing: {', '.join(missing_fields)}"
        return False, message

    return True, ""


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

    # Default mode: unknown until we successfully hit one of the paths
    st.session_state["generation_mode"] = "unknown"

    client_payload = build_client_brief_payload()
    services = st.session_state["services"]
    package_name = st.session_state["selected_package"]
    refinement_name, refinement_cfg = get_refinement_mode()
    learn_items = load_learn_items()

    # 🔥 Force-enable core WOW services so every package is agency-grade internally
    services["marketing_plan"] = True
    services["campaign_blueprint"] = True
    services["social_calendar"] = True
    services["creatives"] = True
    services["include_agency_grade"] = True

    # Resolve WOW package key from the selected package label
    wow_package_key = PACKAGE_KEY_BY_LABEL.get(package_name)

    payload: Dict[str, Any] = {
        "stage": stage,
        "client_brief": client_payload,
        "services": services,
        "package_name": package_name,
        "wow_enabled": bool(wow_package_key),
        "wow_package_key": wow_package_key,
        "refinement_mode": {
            "name": refinement_name,
            **refinement_cfg,
        },
        "feedback": extra_feedback,
        "previous_draft": st.session_state.get("draft_report") or "",
        "learn_items": learn_items,
        "use_learning": True,
        "industry_key": st.session_state.get("industry_key"),
        "competitor_snapshot": st.session_state.get("competitor_snapshot", []),
    }

    st.session_state["last_backend_payload"] = payload

    # Backend URL resolution: prefer AICMO_BACKEND_URL, fall back to BACKEND_URL
    base_url = (
        st.secrets.get("AICMO_BACKEND_URL")
        if hasattr(st, "secrets") and "AICMO_BACKEND_URL" in st.secrets
        else os.environ.get("AICMO_BACKEND_URL") or os.environ.get("BACKEND_URL") or ""
    )
    base_url = base_url.rstrip("/")

    # ----------------------------
    # Backend HTTP endpoint (no auto-fallback)
    # ----------------------------
    if base_url:
        url = f"{base_url}/api/aicmo/generate_report"

        # Connection attempt with detailed error reporting
        try:
            resp = requests.post(
                url,
                json=payload,
                timeout=(10, 300),  # (connect_timeout, read_timeout)
            )
        except requests.RequestException as e:
            st.error(f"❌ Backend connection error: {e}")
            st.error("Cannot reach backend. Check AICMO_BACKEND_URL and network.")
            return None

        # HTTP status check – show exact error, no fallback
        if resp.status_code != 200:
            st.error(
                f"❌ Backend returned HTTP {resp.status_code} for /api/aicmo/generate_report\n\n"
                f"**Raw response (first 2000 chars):**\n```\n{resp.text[:2000]}\n```"
            )
            return None

        # JSON parsing
        try:
            data = resp.json()
        except Exception:
            st.error(
                f"❌ Backend returned non-JSON response.\n\n"
                f"**Raw body (first 1000 chars):**\n```\n{resp.text[:1000]}\n```"
            )
            return None

        # Validate response structure
        if isinstance(data, dict) and "report_markdown" in data:
            st.session_state["generation_mode"] = "http-backend"
            st.success("✅ Report generated using backend with Phase-L learning.")
            return data["report_markdown"]
        else:
            st.error(
                f"❌ Backend returned unexpected structure. Expected 'report_markdown' key.\n\n"
                f"**Got keys:** {list(data.keys()) if isinstance(data, dict) else type(data)}"
            )
            return None

    else:
        st.error("⚠️  AICMO_BACKEND_URL is not configured. Backend pipeline cannot be used.")
        return None


def _apply_humanization(
    text: str,
    brand_name: Optional[str] = None,
    objectives: Optional[str] = None,
) -> str:
    """
    Apply the humanization wrapper to make output sound less AI-like.
    Gracefully degrades if humanizer is not available.

    ⚠️  FIX #4: Skip humanization for large reports (>8000 chars)
    to avoid token limit truncation at the humanization LLM layer.
    """
    if humanizer is None or not text:
        return text

    # Skip humanization for large reports to avoid token truncation
    if len(text) > 8000:
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
                "Brand / product name *",
                value=meta.get("brand_name", ""),
                help="Required - will be used in all generated content",
            )
            meta["product_service"] = st.text_input(
                "Product / service *",
                value=meta.get("product_service", ""),
                help="Required - describe the main offering",
            )
            meta["industry"] = st.text_input(
                "Industry / category *",
                value=meta.get("industry", ""),
                help="Required - e.g., SaaS, e-commerce, healthcare",
            )
            meta["geography"] = st.text_input(
                "Primary geography / market",
                value=meta.get("geography", ""),
            )
            meta["objectives"] = st.text_area(
                "Primary objectives *",
                value=meta.get("objectives", ""),
                height=80,
                help="Required - core goals and key metrics",
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
                    st.session_state["industry_key"] = selected
                else:
                    st.session_state["industry_key"] = None
            else:
                st.info("No industry presets available in this environment.")

        # ================================
        # Competitor Research (Optional)
        # ================================
        st.markdown("### Competitor Research (Optional)")

        enable_competitor_research = st.checkbox(
            "Enable Competitor Research for this report",
            value=False,
            help="Fetch local competitors based on industry + geography to improve strategic recommendations.",
        )

        competitor_snapshot = []

        if enable_competitor_research:
            meta = st.session_state.get("client_brief_meta", {}) or {}
            location = meta.get("geography", "")
            industry = meta.get("industry", "")

            if not (location and industry):
                st.warning("Enter location and industry above to fetch competitors.")
            else:
                with st.spinner("Fetching competitors based on location and industry..."):
                    try:
                        # Try to call backend API for competitor research
                        backend_url = (
                            os.environ.get("AICMO_BACKEND_URL")
                            or os.environ.get("BACKEND_URL")
                            or ""
                        )
                        backend_url = backend_url.rstrip("/")

                        if backend_url:
                            resp = requests.post(
                                f"{backend_url}/api/competitor/research",
                                json={
                                    "location": location,
                                    "industry": industry,
                                },
                                timeout=60,
                            )

                            if resp.status_code == 200:
                                competitor_snapshot = resp.json().get("competitors", [])
                                st.session_state["competitor_snapshot"] = competitor_snapshot
                            elif resp.status_code == 404:
                                st.info("Competitor research API not yet implemented on backend.")
                            else:
                                st.error(f"Competitor API error: {resp.text[:200]}")
                        else:
                            st.warning(
                                "Backend URL not configured. Competitor research unavailable."
                            )

                    except requests.exceptions.ReadTimeout:
                        st.warning(
                            "Competitor research timed out. Continuing without competitors..."
                        )
                    except Exception as e:
                        st.warning(f"Error fetching competitors: {str(e)}")

            # Display results
            if competitor_snapshot:
                st.subheader("Local Competitor Snapshot")
                st.dataframe(competitor_snapshot, use_container_width=True)
            elif enable_competitor_research:
                st.info("No competitors found or competitor research is not yet available.")

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

        # Validate required fields
        is_valid, error_msg = validate_required_brief_fields()

        if not is_valid:
            st.warning(f"⚠️ {error_msg}")

        if st.button(
            "Generate draft report",
            type="primary",
            use_container_width=True,
            disabled=not is_valid,
        ):
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

    mode = st.session_state.get("generation_mode", "unknown")
    if mode == "http-backend":
        st.caption("✅ Source: AICMO backend (WOW presets + learning + agency-grade filters)")
    elif mode == "direct-openai-fallback":
        st.caption("⚠️ Source: Direct OpenAI fallback (no backend WOW / Phase-L)")
    else:
        st.caption("ℹ️ Source: Not recorded for this run (legacy or manual edit).")

    if not st.session_state.get("draft_report") and not st.session_state.get("final_report"):
        st.info("No content yet. Generate and refine a draft first.")
        return

    if not st.session_state.get("final_report"):
        st.session_state["final_report"] = st.session_state.get("draft_report", "")

    # 🛡️ OPERATOR MODE: Generate proof file
    if st.session_state.get("final_report"):
        try:
            from backend.proof_utils import save_proof_file

            brief_dict = build_client_brief_payload()
            package_key = st.session_state.get("selected_package", "unknown").lower()

            proof_path = save_proof_file(
                report_markdown=st.session_state["final_report"],
                brief=brief_dict,
                package_key=package_key,
            )
            st.session_state["last_proof_file"] = str(proof_path)
        except Exception:
            pass  # Silently fail if proof_utils not available

    st.markdown("#### Final report preview")
    # ✨ FIX #3: Use safe chunked renderer to prevent truncation of large reports
    from aicmo.renderers import render_full_report

    render_full_report(st.session_state["final_report"], use_chunks=True)

    # 🛡️ OPERATOR MODE: Show proof file info
    if st.session_state.get("last_proof_file"):
        with st.expander("📋 Proof File Info (Operator Mode)"):
            st.success(f"✅ Proof file generated: {Path(st.session_state['last_proof_file']).name}")
            st.caption(f"📂 Path: `{st.session_state['last_proof_file']}`")
            st.markdown(
                "This proof file contains:\n"
                "- Brief metadata\n"
                "- Placeholder injection table\n"
                "- Quality gate results\n"
                "- Sanitization report\n"
                "- Full sanitized report"
            )

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
        # Check if backend is available
        backend_url = os.environ.get("AICMO_BACKEND_URL") or os.environ.get("BACKEND_URL")

        if not PDF_EXPORT_AVAILABLE:
            st.info(
                "PDF export isn't available in this deployment because the backend "
                "PDF module isn't loaded. Deploy the full backend to enable this feature."
            )
        elif not backend_url:
            st.info(
                "PDF export is available only when connected to the full backend. "
                "Set AICMO_BACKEND_URL to enable this feature."
            )
        else:
            # Agency mode toggle
            agency_mode = st.checkbox(
                "Generate agency-grade PDF (Ogilvy/McCann style)",
                value=False,
                help="When enabled, uses AICMO's full HTML-designed layout. When disabled, uses the classic text PDF.",
            )

            if st.button("Generate PDF", key="btn_generate_pdf", use_container_width=True):
                if not st.session_state.get("final_report"):
                    st.warning("Generate a report first before exporting to PDF.")
                else:
                    with st.spinner("Generating PDF report…"):
                        try:
                            pdf_bytes = None
                            export_error = None

                            try:
                                # Build payload with agency mode flags
                                payload = {
                                    "markdown": st.session_state["final_report"],
                                    "wow_enabled": bool(agency_mode),
                                    "wow_package_key": "strategy_campaign_standard",
                                }

                                # Call backend PDF export endpoint
                                resp = requests.post(
                                    backend_url.rstrip("/") + "/aicmo/export/pdf",
                                    json=payload,
                                    timeout=60,
                                )

                                # Check status code first
                                if resp.status_code != 200:
                                    # Backend returned an error (likely JSON)
                                    try:
                                        error_data = resp.json()
                                        export_error = error_data.get(
                                            "message", "PDF export failed on backend"
                                        )
                                    except Exception:
                                        export_error = f"Backend returned status {resp.status_code}"
                                else:
                                    # Success – check content-type first
                                    content_type = resp.headers.get("Content-Type", "")
                                    if not content_type.startswith("application/pdf"):
                                        export_error = (
                                            f"Backend returned wrong content-type: {content_type}"
                                        )
                                    else:
                                        # Extract PDF bytes
                                        pdf_bytes = resp.content

                                        # Sanity check: PDF must start with %PDF header
                                        if pdf_bytes and not pdf_bytes.startswith(b"%PDF"):
                                            export_error = "Backend returned invalid PDF data (missing PDF header)"
                                            pdf_bytes = None

                                        # Optionally track PDF metadata
                                        if pdf_bytes and ensure_pdf_for_report:
                                            try:
                                                ensure_pdf_for_report(
                                                    report_id=st.session_state.get(
                                                        "report_id", "aicmo_report"
                                                    ),
                                                    markdown=st.session_state["final_report"],
                                                    meta={
                                                        "title": st.session_state.get(
                                                            "client_brief_meta", {}
                                                        ).get("brand_name", "AICMO Report"),
                                                        "report_type": "Final Output",
                                                    },
                                                )
                                            except Exception:
                                                pass  # Non-critical, don't block download

                            except requests.exceptions.RequestException as e:
                                export_error = f"Backend request failed: {str(e)[:100]}"
                            except Exception as e:
                                export_error = f"Unexpected error: {str(e)[:100]}"

                            # Show error if we couldn't get a valid PDF
                            if export_error:
                                st.error(f"❌ PDF export failed: {export_error}")
                                st.info(
                                    "💡 Check that the backend is running and the report content is valid."
                                )
                            elif pdf_bytes:
                                # Success: show download button
                                st.download_button(
                                    "⬇️ Download PDF",
                                    data=pdf_bytes,
                                    file_name="aicmo_report.pdf",
                                    mime="application/pdf",
                                    key="btn_download_pdf",
                                    use_container_width=True,
                                )
                                st.success("✅ PDF generated successfully!")
                            else:
                                st.error("❌ No PDF data received. Check backend logs.")

                        except Exception as e:
                            st.error(f"PDF generation workflow failed: {str(e)}")

    if st.button("Mark this as final & lock draft", use_container_width=True):
        st.toast("Final report locked for this project.", icon="🔒")


def render_learn_tab() -> None:
    st.subheader("4️⃣ Learn – Teach AICMO Using Gold-Standard Reports")

    # DEBUG MARKER
    st.error("DEBUG: ZIP-LEARNING BUILD ACTIVE", icon="💾")

    st.markdown(
        "Use this area to feed AICMO examples from top agencies: great decks, reports, "
        "calendars, and audits. These are not sent to clients; they are only used as "
        "learning references to shape future outputs."
    )

    # 🔹 SHOW REAL MEMORY STATS FROM BACKEND
    st.markdown("---")
    st.markdown("#### Backend Learning Statistics")

    backend_url = os.environ.get(
        "AICMO_BACKEND_URL", os.environ.get("BACKEND_URL", "http://localhost:8000")
    )

    with st.expander("Memory Database Stats", expanded=True):
        try:
            resp = requests.get(
                f"{backend_url}/api/learn/debug/summary",
                timeout=10,
            )
            if resp.ok:
                data = resp.json()
                total_items = data.get("total_items", 0)
                per_kind = data.get("per_kind", {})

                st.metric("Total memory items", total_items)

                if per_kind:
                    st.write("**Items per kind:**")
                    for kind, cnt in per_kind.items():
                        st.write(f"- {kind}: {cnt}")
                else:
                    st.info("No learning items stored yet.")
            else:
                st.warning(f"Could not fetch stats: HTTP {resp.status_code}")
        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to backend. Is it running? (python -m uvicorn backend.main:app --reload)"
            )
        except Exception as e:
            st.warning(f"Error fetching learning stats: {e}")

    # ZIP upload section for bulk training
    st.markdown("---")
    st.markdown("#### Bulk Training – Upload ZIP Archive")
    st.markdown(
        "Upload a ZIP file containing multiple training documents (.txt, .md, .pdf) "
        "to quickly train AICMO on best practices. The system will extract, process, "
        "and archive your files for audit trail."
    )

    col_zip_upload, col_zip_info = st.columns([3, 2])

    with col_zip_upload:
        training_zip = st.file_uploader(
            "Select a ZIP file containing training documents",
            type=["zip"],
            key="learn_zip_file",
        )

    with col_zip_info:
        st.info(
            "**Supported formats:** .txt, .md, .pdf\n\n"
            "Files are organized and archived in `/data/learning/` for audit trail."
        )

    col_zip_btn, col_zip_spinner = st.columns([1, 3])

    with col_zip_btn:
        process_zip = st.button(
            "Train from ZIP",
            key="process_zip",
            use_container_width=True,
            type="primary",
        )

    if process_zip:
        if training_zip is None:
            st.warning("Please attach a ZIP file first.")
        else:
            with st.spinner("Processing ZIP and training AICMO..."):
                try:
                    # Prepare files for POST
                    files = {
                        "file": (training_zip.name, training_zip.getvalue(), "application/zip")
                    }

                    # Get backend URL from environment
                    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")

                    # Send to backend
                    response = requests.post(
                        f"{backend_url}/api/learn/from-zip",
                        files=files,
                        params={"project_id": st.session_state.get("project_id", "default")},
                        timeout=60,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success(
                            f"✅ Training complete!\n\n"
                            f"**Files processed:** {result['files_processed']}\n"
                            f"**Blocks learned:** {result['blocks_learned']}\n\n"
                            f"{result['message']}"
                        )
                        # Log the learning event
                        learn_item = {
                            "kind": "zip_upload",
                            "filename": training_zip.name,
                            "size_bytes": len(training_zip.getvalue()),
                            "files_processed": result["files_processed"],
                            "blocks_learned": result["blocks_learned"],
                            "timestamp": datetime.datetime.now().isoformat(),
                        }
                        append_learn_item(learn_item)
                    else:
                        error_detail = response.json().get("detail", "Unknown error")
                        st.error(f"❌ Training failed: {error_detail}")
                except requests.exceptions.Timeout:
                    st.error("Training request timed out. ZIP file may be too large.")
                except Exception as e:
                    st.error(f"Error processing ZIP: {str(e)}")

    st.markdown("---")

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

    # 🛡️ OPERATOR MODE TOGGLE (sidebar)
    with st.sidebar:
        st.markdown("---")
        operator_mode = st.toggle("🛡️ Operator Mode (QC)", value=False)
        if operator_mode:
            st.caption("✅ Internal QA tools enabled")
            st.markdown(
                """
**Quick Links:**
- 📊 [QC Dashboard](/operator_qc)
- 📁 [Proof Files](.aicmo/proof/)
- 🧪 [WOW Audit](scripts/dev/aicmo_wow_end_to_end_check.py)
            """
            )

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
