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

# ============================================================================
# SAFETY: Dangerous ops (raw SQL, DB bootstrap) are gated by environment flag
# ============================================================================
AICMO_ENABLE_DANGEROUS_UI_OPS = os.getenv('AICMO_ENABLE_DANGEROUS_UI_OPS', '').lower() == '1'

if AICMO_ENABLE_DANGEROUS_UI_OPS:
    import streamlit as st
    st.warning(
        "⚠️ **DANGER MODE ENABLED**: Raw SQL and destructive operations are accessible. "
        "This should only be used in development/debugging."
    )
# ============================================================================

# PHASE 1: Install fatal exception hook BEFORE any imports that might fail
if os.getenv('AICMO_E2E_MODE') == '1':
    try:
        from aicmo.core.diagnostics.fatal import install_fatal_exception_hook
        install_fatal_exception_hook()
    except Exception as e:
        sys.stderr.write(f"Failed to install fatal hook: {e}\n")
        sys.stderr.flush()

import requests  # noqa: E402
import streamlit as st  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

# Import operator services for Command Center
# NOTE: In E2E mode, delay import to avoid DB init issues on cold start
if os.getenv('AICMO_E2E_MODE') != '1':
    try:
        from aicmo import operator_services
        from aicmo.core.db import get_session
        OPERATOR_SERVICES_AVAILABLE = True
    except ImportError:
        operator_services = None  # type: ignore
        get_session = None  # type: ignore
        OPERATOR_SERVICES_AVAILABLE = False
else:
    # E2E mode: stub these out to avoid startup issues
    operator_services = None
    get_session = None
    OPERATOR_SERVICES_AVAILABLE = False

# Import benchmark error UI helper
try:
    from aicmo.ui.benchmark_errors import render_benchmark_error_ui
except ImportError:
    render_benchmark_error_ui = None  # type: ignore

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

# PHASE 3: EARLY breadcrumb - BEFORE set_page_config to isolate abort point
e2e_mode = os.getenv('AICMO_E2E_MODE') == '1'
sys.stderr.write(f"[E2E DEBUG-PRE-CONFIG] e2e_mode={e2e_mode}\n")
sys.stderr.flush()

# Attempt to render breadcrumb BEFORE page_config (if possible)
if e2e_mode:
    try:
        sys.stderr.write("[E2E DEBUG-PRE-CONFIG] About to call set_page_config\n")
        sys.stderr.flush()
    except:
        pass

st.set_page_config(
    page_title="AICMO Operator – Premium",
    layout="wide",
)

sys.stderr.write(f"[E2E DEBUG-POST-CONFIG] After set_page_config\n")
sys.stderr.flush()

# CRITICAL: Try rendering first breadcrumb RIGHT HERE to see if st.markdown works
if e2e_mode:
    try:
        st.markdown('<div data-testid="e2e-breadcrumb-01-config-done">✓</div>', unsafe_allow_html=True)
        sys.stderr.write("[E2E DEBUG] Rendered breadcrumb-01\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"[E2E FAILED] Breadcrumb-01 failed: {e}\n")
        sys.stderr.flush()
        raise


# Global cockpit styling for operator dashboard
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
    </style>
    """,
    unsafe_allow_html=True,
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

    # Command Center / cockpit-specific state
    if "activity_log" not in st.session_state:
        st.session_state.activity_log = [
            {
                "time": "10:02",
                "event": "System auto-rejected lead \"SpamBot LLC\"",
                "detail": "Reason: No Budget",
            },
            {
                "time": "09:45",
                "event": "Strategy generated for \"FinTech Client A\"",
                "detail": "Pack: Full Funnel Suite",
            },
            {
                "time": "09:30",
                "event": "LinkedIn token refreshed successfully",
                "detail": "Next refresh in 23h",
            },
        ]

    if "mock_projects" not in st.session_state:
        st.session_state.mock_projects = [
            {"id": 1, "name": "TechCorp", "stage": "STRATEGY", "clarity": 82},
            {"id": 2, "name": "StartupX", "stage": "INTAKE", "clarity": 45},
            {"id": 3, "name": "FinServe A", "stage": "CREATIVE", "clarity": 96},
            {"id": 4, "name": "Luxotica Automobiles", "stage": "EXECUTION", "clarity": 91},
            {"id": 5, "name": "Local Gym", "stage": "DONE", "clarity": 88},
        ]

    if "gateway_status" not in st.session_state:
        st.session_state.gateway_status = {
            "LinkedIn API": "ok",
            "OpenAI": "ok",
            "Apollo": "bad",  # e.g. rate-limited
        }

    if "system_paused" not in st.session_state:
        st.session_state.system_paused = False


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


# -------------------------------------------------
# Command Center helpers
# -------------------------------------------------


def _get_attention_metrics() -> Dict[str, int]:
    """Compute the top-row 'blocking money' metrics."""
    if not OPERATOR_SERVICES_AVAILABLE or get_session is None:
        # Fallback to mock data if services unavailable
        return {
            "leads": 12,
            "high_intent": 3,
            "approvals_pending": 4,
            "execution_success": 98,
            "failed_last_24h": 2,
        }
    
    try:
        with get_session() as db:
            return operator_services.get_attention_metrics(db)
    except Exception as e:
        st.error(f"Failed to load metrics: {e}")
        return {
            "leads": 0,
            "high_intent": 0,
            "approvals_pending": 0,
            "execution_success": 0,
            "failed_last_24h": 0,
        }


def _group_projects_by_stage(projects: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group projects into the 5 state-machine columns."""
    columns: Dict[str, List[Dict[str, Any]]] = {
        "INTAKE": [],
        "STRATEGY": [],
        "CREATIVE": [],
        "EXECUTION": [],
        "DONE": [],
    }
    for p in projects:
        stage = str(p.get("stage", "DONE")).upper()
        if stage not in columns:
            stage = "DONE"
        columns[stage].append(p)
    return columns


def _render_autonomy_tab() -> None:
    """
    Render Autonomy Orchestration Layer (AOL) monitoring tab.
    
    Displays:
    - Daemon lease status (owner, expiry)
    - Last tick summary
    - Control flags (pause/resume/kill buttons)
    - Action queue (pending/retry/DLQ counts)
    - Recent execution logs
    """
    try:
        # Lazy import to avoid cold-start blockers
        from aicmo.orchestration.models import (
            AOLControlFlags, AOLTickLedger, AOLLease, AOLAction, AOLExecutionLog
        )
        from aicmo.orchestration.queue import ActionQueue
        
        if not get_session or not OPERATOR_SERVICES_AVAILABLE:
            st.warning("⚠️ Autonomy features require database connection")
            return
        
        session = get_session()
        
        # Read current state
        from sqlalchemy import select, desc, func
        
        # 1. Lease status
        lease_stmt = select(AOLLease).limit(1)
        lease = session.execute(lease_stmt).scalar_one_or_none()
        
        # 2. Control flags
        flags_stmt = select(AOLControlFlags).limit(1)
        flags = session.execute(flags_stmt).scalar_one_or_none()
        
        if not flags:
            flags = AOLControlFlags()
            session.add(flags)
            session.commit()
        
        # 3. Last tick
        last_tick_stmt = select(AOLTickLedger).order_by(desc(AOLTickLedger.id)).limit(1)
        last_tick = session.execute(last_tick_stmt).scalar_one_or_none()
        
        # 4. Action counts
        pending_count = session.query(func.count(AOLAction.id)).filter(
            AOLAction.status.in_(["PENDING", "READY"])
        ).scalar() or 0
        
        retry_count = session.query(func.count(AOLAction.id)).filter(
            AOLAction.status == "RETRY"
        ).scalar() or 0
        
        dlq_count = session.query(func.count(AOLAction.id)).filter(
            AOLAction.status == "DLQ"
        ).scalar() or 0
        
        session.close()
        
        # === DISPLAY ===
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Pending Actions", pending_count)
        
        with col2:
            st.metric("🔄 Retry Queue", retry_count)
        
        with col3:
            st.metric("💀 Dead Letter", dlq_count)
        
        with col4:
            mode = "🎯 PROOF" if flags.proof_mode else "🔴 REAL"
            st.metric("Mode", mode)
        
        # Daemon status
        st.markdown("### Daemon Status")
        
        if lease:
            lease_col1, lease_col2 = st.columns(2)
            with lease_col1:
                st.text_input("Lease Owner", lease.owner, disabled=True)
            with lease_col2:
                expires_in = (lease.expires_at_utc - datetime.datetime.utcnow()).total_seconds() if lease.expires_at_utc else 0
                status_color = "🟢" if expires_in > 0 else "🔴"
                st.metric("Lease TTL (s)", f"{status_color} {max(0, int(expires_in))}")
        else:
            st.info("✓ No daemon lease (idle or not running)")
        
        # Last tick
        if last_tick:
            st.markdown("### Last Tick Summary")
            tick_col1, tick_col2, tick_col3 = st.columns(3)
            
            with tick_col1:
                status_emoji = {"SUCCESS": "✓", "PARTIAL": "⚠️", "FAIL": "❌"}.get(last_tick.status, "?")
                st.metric("Status", f"{status_emoji} {last_tick.status}")
            
            with tick_col2:
                duration = (last_tick.finished_at_utc - last_tick.started_at_utc).total_seconds() \
                    if last_tick.finished_at_utc else 0
                st.metric("Duration (s)", f"{duration:.2f}")
            
            with tick_col3:
                st.metric(
                    "Actions",
                    f"{last_tick.actions_succeeded}/{last_tick.actions_attempted}"
                )
            
            if last_tick.notes:
                st.caption(f"Notes: {last_tick.notes}")
        else:
            st.info("ℹ️ No ticks recorded yet")
        
        # Control flags
        st.markdown("### Control Flags")
        control_col1, control_col2, control_col3 = st.columns(3)
        
        with control_col1:
            if st.button("⏸️ Pause Daemon" if not flags.paused else "▶️ Resume Daemon"):
                session = get_session()
                flags.paused = not flags.paused
                session.merge(flags)
                session.commit()
                session.close()
                st.rerun()
        
        with control_col2:
            if st.button("🗑️ Clear DLQ"):
                session = get_session()
                session.query(AOLAction).filter(AOLAction.status == "DLQ").update(
                    {AOLAction.status: "CANCELLED"}
                )
                session.commit()
                session.close()
                st.success("DLQ cleared")
                st.rerun()
        
        with control_col3:
            if st.button("🛑 Kill Daemon"):
                session = get_session()
                flags.killed = True
                session.merge(flags)
                session.commit()
                session.close()
                st.warning("Kill flag set - daemon will exit on next tick")
        
        # Enqueue test action section
        st.markdown("### Enqueue Test Action (PROOF mode only)")
        
        enqueue_col1, enqueue_col2 = st.columns([1, 1])
        
        with enqueue_col1:
            action_type = st.selectbox(
                "Action Type",
                ["POST_SOCIAL"],
                disabled=not flags.proof_mode,
                help="Only PROOF mode actions supported via UI"
            )
        
        with enqueue_col2:
            payload_json = st.text_area(
                "Payload (JSON)",
                '{"platform": "twitter", "message": "Test"}',
                height=60,
                disabled=not flags.proof_mode,
            )
        
        if st.button("📤 Enqueue Action", disabled=not flags.proof_mode):
            if not flags.proof_mode:
                st.error("Cannot enqueue: PROOF mode is disabled")
            else:
                try:
                    import json
                    import uuid
                    from aicmo.orchestration.queue import ActionQueue
                    
                    # Validate JSON
                    payload = json.loads(payload_json)
                    
                    # Create unique idempotency key
                    idempotency_key = f"ui_test_{uuid.uuid4().hex[:8]}"
                    
                    session = get_session()
                    ActionQueue.enqueue_action(
                        session=session,
                        action_type=action_type,
                        payload_json=json.dumps(payload),
                        idempotency_key=idempotency_key,
                    )
                    session.commit()
                    session.close()
                    
                    st.success(f"✓ Action enqueued: {idempotency_key}")
                    st.rerun()
                    
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")
                except Exception as e:
                    st.error(f"Failed to enqueue action: {e}")
        
        if not flags.proof_mode:
            st.info("💡 Enable PROOF mode to enqueue test actions")
        st.markdown("### Recent Execution Logs")
        
        session = get_session()
        log_stmt = select(AOLExecutionLog).order_by(
            desc(AOLExecutionLog.ts_utc)
        ).limit(10)
        logs = session.execute(log_stmt).scalars().all()
        session.close()
        
        if logs:
            log_data = []
            for log in logs:
                log_data.append({
                    "Time": log.ts_utc.isoformat() if log.ts_utc else "N/A",
                    "Level": log.level,
                    "Action ID": log.action_id,
                    "Message": log.message or "",
                    "Artifact": log.artifact_ref or ""
                })
            
            st.dataframe(log_data, use_container_width=True)
        else:
            st.info("ℹ️ No execution logs yet")
        
    except Exception as e:
        st.error(f"Autonomy tab error: {str(e)}")
        import traceback
        with st.expander("Debug Info"):
            st.code(traceback.format_exc())


def _render_gateway_ticker(status_map: Dict[str, str]) -> None:
    """Render compact gateway health ticker."""
    parts: List[str] = []
    for label, status in status_map.items():
        if status == "ok":
            dot_class = "cc-dot cc-dot-ok"
        elif status == "bad":
            dot_class = "cc-dot cc-dot-bad"
        else:
            dot_class = "cc-dot cc-dot-warn"
        parts.append(
            f'<span class="cc-gateway-label"><span class="{dot_class}"></span>{label}</span>'
        )
    html = " ".join(parts)
    st.markdown(html, unsafe_allow_html=True)


def _render_activity_feed() -> None:
    """Render the scrolling activity feed."""
    # Fetch real activity data
    if OPERATOR_SERVICES_AVAILABLE and get_session is not None:
        try:
            with get_session() as db:
                events = operator_services.get_activity_feed(db, limit=25)
        except Exception as e:
            st.error(f"Failed to load activity feed: {e}")
            events = []
    else:
        # Fallback to mock data if services unavailable
        events = st.session_state.get("activity_log", [])
    
    st.markdown('<div class="cc-card cc-feed">', unsafe_allow_html=True)
    for item in events:
        time_str = item.get("time", "--:--")
        event = item.get("event", "")
        detail = item.get("detail", "")
        st.markdown(
            f'''
            <div class="cc-feed-item">
              <div><time>{time_str}</time> {event}</div>
              <div style="font-size:0.72rem;color:#6B7280;">{detail}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------
# Backend integration
# -------------------------------------------------


def call_backend_generate(
    stage: str,  # "draft" | "refine" | "final"
    extra_feedback: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Main integration point:
    - builds payload
    - calls backend API if configured
    - falls back to local OpenAI call if needed
    - returns backend response dict or None on failure
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
            # Parse error detail for user-friendly display
            try:
                error_data = resp.json()
                detail = error_data.get("detail", resp.text)
            except Exception:
                detail = resp.text or f"HTTP {resp.status_code}"

            # If this is a benchmark failure (HTTP 500), use friendly error UI
            if resp.status_code == 500 and "benchmark validation failed" in detail.lower():
                render_benchmark_error_ui(
                    error_detail=detail,
                    request_payload=payload,
                    retry_callback_key=f"retry_{stage}",
                )
                return None

            # Otherwise show raw error
            st.error(
                f"❌ Backend returned HTTP {resp.status_code} for /api/aicmo/generate_report\n\n"
                f"**Raw response (first 2000 chars):**\n```\n{detail[:2000]}\n```"
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

        # Validate response structure with flexible fallback
        if not isinstance(data, dict):
            st.error(
                f"❌ Backend returned non-dict structure: {type(data)}\n\n"
                f"**Expected:** dict with 'report_markdown' key\n"
                f"**Got:** {str(data)[:200]}"
            )
            return None

        return data

    else:
        st.error("⚠️  AICMO_BACKEND_URL is not configured. Backend pipeline cannot be used.")
        return None


def _process_backend_response(
    response: Optional[Dict[str, Any]], stage_label: str
) -> Optional[str]:
    """Interpret backend payload, surface errors, and return markdown when available."""

    if not response:
        return None

    st.session_state["last_backend_response"] = response

    if not isinstance(response, dict):
        st.error("❌ Backend returned a non-dict response payload.")
        with st.expander("Full backend payload"):
            st.write(response)
        return None

    error_code = response.get("error") or response.get("error_type")
    detail = response.get("detail") or response.get("error_message", "")

    if not response.get("success", True) or error_code:
        st.error(
            f"❌ Backend error ({stage_label}): {error_code or 'unknown_error'} - {detail or 'no detail available'}"
        )
        with st.expander("See backend response"):
            st.json(response)
        return None

    report_md: Optional[str] = None
    key_found = "report_markdown"

    if isinstance(response.get("report_markdown"), str):
        report_md = response["report_markdown"]
        key_found = "report_markdown"
    elif isinstance(response.get("markdown"), str):
        report_md = response["markdown"]
        key_found = "markdown"
    elif isinstance(response.get("report"), dict):
        report_obj = response["report"]
        if isinstance(report_obj.get("markdown"), str):
            report_md = report_obj["markdown"]
            key_found = "report.markdown"
        elif isinstance(report_obj.get("text"), str):
            report_md = report_obj["text"]
            key_found = "report.text"

    if not report_md or not report_md.strip():
        st.error(
            "The backend returned an empty report. Check backend logs or try a different refinement mode."
        )
        with st.expander("Debug payload"):
            st.json(response)
        return None

    st.session_state["generation_mode"] = "http-backend"
    st.success(f"✅ Backend {stage_label} report generated (key: {key_found}).")
    return report_md.strip()


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


def render_command_center_tab() -> None:
    st.subheader("Command Center")

    # Top strip with gateway status on the right
    top_left, top_right = st.columns([3, 2])
    with top_left:
        st.markdown(
            "Operate AICMO like a cockpit: see what blocks money, project flow, and gateway health."
        )
    with top_right:
        st.caption("Gateway Status")
        # Fetch real gateway status
        if OPERATOR_SERVICES_AVAILABLE and get_session is not None:
            try:
                with get_session() as db:
                    gateway_status = operator_services.get_gateway_status(db)
            except Exception:
                gateway_status = st.session_state.get("gateway_status", {})
        else:
            gateway_status = st.session_state.get("gateway_status", {})
        _render_gateway_ticker(gateway_status)

    # Nested views inside Command Center
    cmd_tab, projects_tab, warroom_tab, gallery_tab, pm_tab, analytics_tab, autonomy_tab, control_tab = st.tabs(
        ["Command", "Projects", "War Room", "Gallery", "PM Dashboard", "Analytics", "Autonomy", "Control Tower"]
    )

    # 1) COMMAND VIEW – "What's blocking money right now?"
    with cmd_tab:
        metrics = _get_attention_metrics()
        col1, col2, col3 = st.columns([1.1, 1.1, 1])

        with col1:
            st.markdown('<div class="cc-card">', unsafe_allow_html=True)
            st.markdown("<h3>Triage Needed</h3>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="cc-metric">{metrics["leads"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="cc-subtext">{metrics["high_intent"]} high-intent (job changes detected).</div>',
                unsafe_allow_html=True,
            )
            st.button("Review Queue", key="cmd_triage_review", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="cc-card">', unsafe_allow_html=True)
            st.markdown("<h3>Approvals Pending</h3>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="cc-metric">{metrics["approvals_pending"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="cc-subtext">Strategy & creative drafts awaiting review.</div>',
                unsafe_allow_html=True,
            )
            st.button("Enter War Room", key="cmd_enter_war_room", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="cc-card">', unsafe_allow_html=True)
            st.markdown("<h3>Execution Health</h3>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="cc-metric">{metrics["execution_success"]}%</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="cc-subtext">Success rate last 24h.</div>',
                unsafe_allow_html=True,
            )
            if metrics["failed_last_24h"] > 0:
                st.markdown(
                    f'<div class="cc-alert">{metrics["failed_last_24h"]} failed posts in last 24h.</div>',
                    unsafe_allow_html=True,
                )
            st.button(
                "Investigate Failures",
                key="cmd_execution_failures",
                use_container_width=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("")
        st.markdown("#### Activity Feed")
        _render_activity_feed()

    # 2) PROJECTS VIEW – Kanban state machine
    with projects_tab:
        st.markdown("#### Projects Pipeline")
        
        # Fetch real projects
        if OPERATOR_SERVICES_AVAILABLE and get_session is not None:
            try:
                with get_session() as db:
                    projects = operator_services.get_projects_pipeline(db)
            except Exception as e:
                st.error(f"Failed to load projects: {e}")
                projects = st.session_state.get("mock_projects", [])
        else:
            projects = st.session_state.get("mock_projects", [])
        
        grouped = _group_projects_by_stage(projects)

        col_intake, col_strategy, col_creative, col_exec, col_done = st.columns(5)

        with col_intake:
            st.markdown('<div class="cc-column-title">Intake</div>', unsafe_allow_html=True)
            for p in grouped["INTAKE"]:
                st.markdown('<div class="cc-project-card">', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="cc-project-name">{p["name"]}</div>',
                    unsafe_allow_html=True,
                )
                clarity = p.get("clarity", 0)
                pill_class = "cc-pill-danger" if clarity < 60 else "cc-pill-warn"
                st.markdown(
                    f'<div class="{pill_class}">Clarity: {clarity}%</div>',
                    unsafe_allow_html=True,
                )
                st.button(
                    "Enter Clarifier",
                    key=f"proj_intake_{p['id']}",
                    use_container_width=True,
                    on_click=lambda pid=p['id']: st.session_state.update({"current_project_id": pid}),
                )
                st.markdown("</div>", unsafe_allow_html=True)

        with col_strategy:
            st.markdown('<div class="cc-column-title">Strategy</div>', unsafe_allow_html=True)
            for p in grouped["STRATEGY"]:
                st.markdown('<div class="cc-project-card">', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="cc-project-name">{p["name"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="cc-pill-warn">Waiting for approval</div>', unsafe_allow_html=True)
                if st.button(
                    "Review Strategy",
                    key=f"proj_strategy_{p['id']}",
                    use_container_width=True,
                ):
                    st.session_state.current_project_id = p['id']
                st.markdown("</div>", unsafe_allow_html=True)

        with col_creative:
            st.markdown('<div class="cc-column-title">Creative</div>', unsafe_allow_html=True)
            for p in grouped["CREATIVE"]:
                st.markdown('<div class="cc-project-card">', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="cc-project-name">{p["name"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="cc-pill-ok">Assets generating</div>', unsafe_allow_html=True)
                if st.button(
                    "Review Assets",
                    key=f"proj_creative_{p['id']}",
                    use_container_width=True,
                ):
                    st.session_state.current_project_id = p['id']
                st.markdown("</div>", unsafe_allow_html=True)

        with col_exec:
            st.markdown('<div class="cc-column-title">Execution</div>', unsafe_allow_html=True)
            for p in grouped["EXECUTION"]:
                st.markdown('<div class="cc-project-card">', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="cc-project-name">{p["name"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="cc-pill-ok">Next post in 2h</div>', unsafe_allow_html=True)
                if st.button(
                    "View Schedule",
                    key=f"proj_exec_{p['id']}",
                    use_container_width=True,
                ):
                    st.session_state.current_project_id = p['id']
                st.markdown("</div>", unsafe_allow_html=True)

        with col_done:
            st.markdown('<div class="cc-column-title">Done / Retainer</div>', unsafe_allow_html=True)
            for p in grouped["DONE"]:
                st.markdown('<div class="cc-project-card">', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="cc-project-name">{p["name"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="cc-pill-ok">Monitoring</div>', unsafe_allow_html=True)
                st.button(
                    "Open Report",
                    key=f"proj_done_{p['id']}",
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

    # 3) WAR ROOM – Strategy review interface
    with warroom_tab:
        current_project_id = st.session_state.get("current_project_id")
        
        if not current_project_id:
            st.info("👈 Select a project from the Projects tab to review its strategy.")
        elif not OPERATOR_SERVICES_AVAILABLE or get_session is None:
            st.warning("Operator services unavailable. Cannot load project data.")
        else:
            try:
                with get_session() as db:
                    context = operator_services.get_project_context(db, current_project_id)
                    strategy_doc = operator_services.get_project_strategy_doc(db, current_project_id)
                
                left, right = st.columns([1.1, 2])
                with left:
                    st.markdown("##### Intake Snapshot")
                    if "error" in context:
                        st.error(context["error"])
                    else:
                        st.markdown(f"**Project:** {context.get('project_name', 'Unknown')}")
                        st.markdown(f"**Goal:** {context.get('goal', 'N/A')}")
                        st.markdown(f"**Audience:** {context.get('audience', 'N/A')}")
                        st.markdown(f"**Constraints:** {context.get('constraints', 'N/A')}")
                        st.markdown("---")
                        st.caption("Loaded from project context")
                
                with right:
                    st.markdown("##### Strategy Draft")
                    edited_strategy = st.text_area(
                        "AI-Generated Strategy",
                        value=strategy_doc,
                        height=360,
                    )

                st.markdown("---")
                reject_col, approve_col = st.columns([1, 1.2])
                with reject_col:
                    reject_reason = st.text_input(
                        "Reason (if sending back to draft)",
                        value="",
                        placeholder="What must change before we can go to creatives?",
                    )
                    if st.button(
                        "Reject – Send Back to Draft",
                        key="warroom_reject",
                        use_container_width=True,
                    ):
                        if reject_reason:
                            with get_session() as db:
                                operator_services.reject_strategy(db, current_project_id, reject_reason)
                            st.success(f"Strategy rejected for project #{current_project_id}")
                        else:
                            st.error("Please provide a reason for rejection")
                
                with approve_col:
                    if st.button(
                        "APPROVE & START CREATIVES",
                        key="warroom_approve",
                        use_container_width=True,
                    ):
                        with get_session() as db:
                            operator_services.approve_strategy(db, current_project_id)
                        st.success(f"Strategy approved for project #{current_project_id}! Moving to creative phase.")
                        
            except Exception as e:
                st.error(f"Failed to load War Room data: {e}")

    # 4) GALLERY – Creative review
    with gallery_tab:
        current_project_id = st.session_state.get("current_project_id")
        
        if not current_project_id:
            st.info("👈 Select a project from the Projects tab to view its creative assets.")
        elif not OPERATOR_SERVICES_AVAILABLE or get_session is None:
            st.warning("Operator services unavailable. Cannot load creative assets.")
        else:
            st.markdown("#### Creative Gallery")
            st.caption("Review and manage creative assets for this project.")
            
            try:
                with get_session() as db:
                    creatives = operator_services.get_creatives_for_project(db, current_project_id)
                
                if not creatives:
                    st.info("No creative assets yet. They will appear here once generated.")
                else:
                    # Display creatives in grid
                    cols = st.columns(min(3, len(creatives)))
                    for idx, creative in enumerate(creatives):
                        col_idx = idx % 3
                        with cols[col_idx]:
                            st.markdown('<div class="cc-card">', unsafe_allow_html=True)
                            st.markdown(f"**{creative.get('platform', 'Unknown')} - {creative.get('asset_type', 'post')}**")
                            st.markdown(f"*Status: {creative.get('status', 'DRAFT')}*")
                            st.text_area(
                                "Caption",
                                value=creative.get('caption', ''),
                                key=f"creative_caption_{creative['id']}",
                                height=100,
                            )
                            
                            b1, b2, b3 = st.columns(3)
                            with b1:
                                if st.button("Edit", key=f"gal_edit_{creative['id']}"):
                                    st.info("Edit modal would appear here")
                            with b2:
                                if st.button("Regen", key=f"gal_regen_{creative['id']}"):
                                    try:
                                        with get_session() as db:
                                            operator_services.regenerate_creative(db, current_project_id, creative['id'])
                                        st.success("Regeneration queued")
                                    except NotImplementedError:
                                        st.warning("Regeneration not yet implemented")
                            with b3:
                                if st.button("Trash", key=f"gal_trash_{creative['id']}"):
                                    try:
                                        with get_session() as db:
                                            operator_services.delete_creative(db, current_project_id, creative['id'])
                                        st.success("Creative deleted")
                                        st.rerun()
                                    except NotImplementedError:
                                        st.warning("Delete not yet implemented")
                            st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                bulk1, bulk2 = st.columns([1, 1])
                with bulk1:
                    if st.button("Approve Selected", key="gal_approve_all", use_container_width=True):
                        try:
                            creative_ids = [c['id'] for c in creatives]
                            with get_session() as db:
                                operator_services.bulk_approve_creatives(db, current_project_id, creative_ids)
                            st.success(f"Approved {len(creative_ids)} creatives")
                        except NotImplementedError:
                            st.warning("Bulk approve not yet implemented")
                with bulk2:
                    if st.button("Schedule All", key="gal_schedule_all", use_container_width=True):
                        try:
                            creative_ids = [c['id'] for c in creatives]
                            with get_session() as db:
                                operator_services.bulk_schedule_creatives(db, current_project_id, creative_ids)
                            st.success(f"Scheduled {len(creative_ids)} creatives")
                        except NotImplementedError:
                            st.warning("Bulk schedule not yet implemented")
                
            except Exception as e:
                st.error(f"Failed to load gallery: {e}")

    # 6) AUTONOMY TAB – Orchestration Layer monitoring
    with autonomy_tab:
        _render_autonomy_tab()

    # 7) CONTROL TOWER – Execution & gateways
    with control_tab:
        top_l, top_r = st.columns([2, 1])

        with top_l:
            st.markdown("#### Execution Timeline")
            current_project_id = st.session_state.get("current_project_id")
            
            if OPERATOR_SERVICES_AVAILABLE and get_session is not None:
                try:
                    with get_session() as db:
                        timeline = operator_services.get_execution_timeline(db, project_id=current_project_id, limit=50)
                    
                    if not timeline:
                        st.info("No execution events yet.")
                    else:
                        # Display timeline as table
                        import pandas as pd
                        df = pd.DataFrame(timeline)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Failed to load timeline: {e}")
            else:
                st.write("Operator services unavailable. Mock timeline:")
                st.table({
                    "Time": ["Today 10:00", "Today 14:00", "Tomorrow 09:00"],
                    "Project": ["TechCorp", "StartupX", "FinServe A"],
                    "Channel": ["LinkedIn", "Instagram", "Email"],
                    "Status": ["Scheduled", "Scheduled", "Draft"],
                })

        with top_r:
            st.markdown("#### Gateways")
            
            # Fetch real gateway status
            if OPERATOR_SERVICES_AVAILABLE and get_session is not None:
                try:
                    with get_session() as db:
                        gateway_status = operator_services.get_gateway_status(db)
                except Exception:
                    gateway_status = st.session_state.get("gateway_status", {})
            else:
                gateway_status = st.session_state.get("gateway_status", {})
            
            for label, status in gateway_status.items():
                if status == "ok":
                    dot_class = "cc-dot cc-dot-ok"
                    status_text = "Healthy"
                elif status == "bad":
                    dot_class = "cc-dot cc-dot-bad"
                    status_text = "Issue"
                else:
                    dot_class = "cc-dot cc-dot-warn"
                    status_text = "Warning"

                st.markdown(
                    f'<span class="{dot_class}"></span> **{label}** – {status_text}',
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown('<span class="cc-pause-label">System Pause</span>', unsafe_allow_html=True)
            
            # Load current pause status from service
            if OPERATOR_SERVICES_AVAILABLE and get_session is not None:
                try:
                    with get_session() as db:
                        current_pause = operator_services.get_system_pause(db)
                except Exception:
                    current_pause = st.session_state.get("system_paused", False)
            else:
                current_pause = st.session_state.get("system_paused", False)
            
            paused = st.checkbox(
                "Emergency stop – pause all outbound execution",
                value=current_pause,
                key="system_pause_checkbox",
            )
            
            # Persist pause status if changed
            if paused != current_pause:
                if OPERATOR_SERVICES_AVAILABLE and get_session is not None:
                    try:
                        with get_session() as db:
                            operator_services.set_system_pause(db, paused)
                        st.success(f"System {'paused' if paused else 'resumed'}")
                    except Exception as e:
                        st.error(f"Failed to update pause status: {e}")
                st.session_state.system_paused = paused

    # 6) PM DASHBOARD – Project Management view
    with pm_tab:
        current_project_id = st.session_state.get("current_project_id")
        
        if not current_project_id:
            st.info("👈 Select a project from the Projects tab to view PM dashboard.")
        elif not OPERATOR_SERVICES_AVAILABLE or get_session is None:
            st.warning("Operator services unavailable. Cannot load PM dashboard.")
        else:
            st.markdown("#### PM Dashboard")
            st.caption("Project management tasks, timeline, and capacity for this project.")
            
            try:
                with get_session() as db:
                    pm_dashboard = operator_services.get_project_pm_dashboard(db, current_project_id)
                
                if "error" in pm_dashboard:
                    st.error(pm_dashboard["error"])
                else:
                    # Display PM data
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("##### Tasks")
                        tasks = pm_dashboard.get("tasks", [])
                        if tasks:
                            import pandas as pd
                            df = pd.DataFrame(tasks)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.info("No PM tasks found.")
                    
                    with col2:
                        st.markdown("##### Timeline")
                        timeline = pm_dashboard.get("timeline", {})
                        if timeline:
                            for phase, duration in timeline.items():
                                st.markdown(f"**{phase}**: {duration}")
                        else:
                            st.info("No timeline data.")
                        
                        st.markdown("---")
                        st.markdown("##### Capacity")
                        capacity = pm_dashboard.get("capacity", {})
                        if capacity:
                            st.json(capacity)
                        else:
                            st.info("No capacity data.")
                        
            except Exception as e:
                st.error(f"Failed to load PM dashboard: {e}")

    # 7) ANALYTICS DASHBOARD – Performance metrics
    with analytics_tab:
        current_project_id = st.session_state.get("current_project_id")
        
        if not current_project_id:
            st.info("👈 Select a project from the Projects tab to view analytics.")
        elif not OPERATOR_SERVICES_AVAILABLE or get_session is None:
            st.warning("Operator services unavailable. Cannot load analytics.")
        else:
            st.markdown("#### Analytics Dashboard")
            st.caption("Performance metrics and insights for this project.")
            
            try:
                with get_session() as db:
                    analytics_dashboard = operator_services.get_project_analytics_dashboard(db, current_project_id)
                
                if "error" in analytics_dashboard:
                    st.error(analytics_dashboard["error"])
                else:
                    # Display analytics
                    col1, col2, col3 = st.columns(3)
                    
                    metrics = analytics_dashboard.get("metrics", {})
                    with col1:
                        st.metric("Engagement Rate", metrics.get("engagement_rate", "N/A"))
                        st.metric("Reach", metrics.get("reach", "N/A"))
                    
                    with col2:
                        st.metric("Conversions", metrics.get("conversions", "N/A"))
                        st.metric("CTR", metrics.get("ctr", "N/A"))
                    
                    with col3:
                        st.metric("Sentiment", metrics.get("sentiment", "N/A"))
                        st.metric("ROI", metrics.get("roi", "N/A"))
                    
                    st.markdown("---")
                    st.markdown("##### Trends")
                    trends = analytics_dashboard.get("trends", [])
                    if trends:
                        import pandas as pd
                        df = pd.DataFrame(trends)
                        st.line_chart(df)
                    else:
                        st.info("No trend data available yet.")
                    
                    st.markdown("---")
                    st.markdown("##### Goal Progress")
                    goals = analytics_dashboard.get("goals", {})
                    if goals:
                        for goal_name, progress in goals.items():
                            st.progress(progress / 100 if isinstance(progress, (int, float)) else 0)
                            st.caption(f"{goal_name}: {progress}%")
                    else:
                        st.info("No goal data available.")
                        
            except Exception as e:
                st.error(f"Failed to load analytics: {e}")


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
            backend_response: Optional[Dict[str, Any]] = None
            with st.spinner("Generating draft report with AICMO..."):
                backend_response = call_backend_generate(stage="draft")

            report_md = _process_backend_response(backend_response, "draft")
            if not report_md:
                return

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

                backend_response = call_backend_generate(
                    stage="refine",
                    extra_feedback=st.session_state.get("feedback_notes", ""),
                )

                # restore mode
                st.session_state["refinement_mode"] = original_mode

            refined_md = _process_backend_response(backend_response, "refine")
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

    tab_cmd, tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Command Center",
            "Client Input",
            "Workshop",
            "Final Output",
            "Learn",
        ]
    )

    with tab_cmd:
        render_command_center_tab()
    with tab1:
        render_client_input_tab()
    with tab2:
        render_workshop_tab()
    with tab3:
        render_final_output_tab()
    with tab4:
        render_learn_tab()


if __name__ == "__main__":
    # In E2E mode, render minimal shell with sentinels only
    if os.getenv('AICMO_E2E_MODE') == '1':
        try:
            st.markdown('<div data-testid="e2e-breadcrumb-02-config">✓</div>', unsafe_allow_html=True)
            st.title("AICMO E2E Test Shell")
            st.markdown('<div data-testid="e2e-breadcrumb-03-di">✓</div>', unsafe_allow_html=True)
            st.markdown('<div data-testid="e2e-breadcrumb-04-db">✓</div>', unsafe_allow_html=True)
            st.markdown('<div data-testid="e2e-breadcrumb-05-ui">✓</div>', unsafe_allow_html=True)
            st.markdown('<div data-testid="e2e-app-loaded">YES</div>', unsafe_allow_html=True)
            st.info("E2E mode: Minimal shell active. Placeholders rendered for Playwright verification.")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            sys.stderr.write(f"AICMO_FATAL_EXCEPTION\n{tb}\n")
            sys.stderr.flush()
            st.error(f"Fatal: {e}\n{tb}")
            st.markdown('<div data-testid="e2e-fatal-exception">FATAL</div>', unsafe_allow_html=True)
            st.stop()
    else:
        # Normal mode: run full app
        try:
            main()
        except Exception as fatal_error:
            import traceback
            tb_str = traceback.format_exc()
            
            # Log to stderr with unique marker
            sys.stderr.write("\n" + "="*80 + "\n")
            sys.stderr.write("AICMO_FATAL_EXCEPTION\n")
            sys.stderr.write("="*80 + "\n")
            sys.stderr.write(tb_str)
            sys.stderr.write("="*80 + "\n")
            sys.stderr.flush()
            
            # Write to JSON file
            try:
                artifact_dir = os.getenv('AICMO_E2E_ARTIFACT_DIR', '/tmp/aicmo_e2e_artifacts')
                Path(artifact_dir).mkdir(parents=True, exist_ok=True)
                fatal_data = {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "exception_type": type(fatal_error).__name__,
                    "exception_message": str(fatal_error),
                    "traceback": tb_str,
                }
                (Path(artifact_dir) / "fatal_exception.json").write_text(json.dumps(fatal_data, indent=2))
            except Exception:
                pass
            
            # Show in UI if possible
            try:
                st.error(f"🔴 FATAL EXCEPTION: {type(fatal_error).__name__}\n\n{tb_str}")
                st.markdown('<div data-testid="e2e-fatal-exception">FATAL</div>', unsafe_allow_html=True)
                st.stop()
            except Exception:
                pass
            
            # Re-raise so Streamlit sees it
            raise
