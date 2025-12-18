"""
DEPRECATED UI ENTRYPOINT

This file was moved from streamlit_pages/aicmo_operator.py as part of Phase 1 canonicalization.
It is FORBIDDEN to import from this file. Use operator_v2.py as the ONLY UI entrypoint.
"""
"""DEPRECATED: wrapper for canonical dashboard

This file previously contained a full Streamlit app. It is now a
deprecated wrapper that forwards to the canonical `operator_v2.main()`.
Run `streamlit run operator_v2.py --server.port 8502 --server.headless true` as the canonical entrypoint.
"""

import os
import re
import sys
from typing import Any, List

import streamlit as st
from operator_v2 import main as operator_v2_main

try:
    # optional imports used in helpers; not fatal if absent
    from aicmo.operator_services import get_session
    OPERATOR_SERVICES_AVAILABLE = True
except Exception:
    get_session = None
    OPERATOR_SERVICES_AVAILABLE = False

st.warning("DEPRECATED: use `streamlit run operator_v2.py` — forwarding to operator_v2")

if __name__ == "__main__":
    operator_v2_main()
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


# PHASE 3: SAFE DATABASE CALL WRAPPER
def safe_db_call(fn, default=None, label: str = "DB operation"):
    """
    Safely execute a database function, catching and logging all errors.
    
    The UI must never crash due to DB issues. This wrapper ensures:
    - All DB errors are caught and logged
    - A sensible default is returned
    - Error details are available for debugging
    
    Args:
        fn: Callable that takes (db_session) and returns a value
        default: Value to return if fn fails (default: None)
        label: Human-readable label for error messages
        
    Returns:
        Result of fn(session) or default value
    """
    if not get_session or not OPERATOR_SERVICES_AVAILABLE:
        # DB not available; return default
        st.warning(f"⚠️ Database unavailable for {label}")
        return default
    
    try:
        with get_session() as session:
            return fn(session)
    except Exception as e:
        import traceback
        st.error(f"❌ Error during {label}: {type(e).__name__}")
        with st.expander("Debug details"):
            st.code(f"{str(e)}\n\n{traceback.format_exc()}", language="python")
        return default

