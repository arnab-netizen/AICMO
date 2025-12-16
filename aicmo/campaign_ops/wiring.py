"""
Campaign Operations Wiring - Integration glue code.

Central place to:
1. Register AOL action handlers with daemon
2. Wire Streamlit UI integration
3. Manage configuration flags
"""

import os

# ============================================================================
# Feature Flags
# ============================================================================

AICMO_CAMPAIGN_OPS_ENABLED = os.getenv("AICMO_CAMPAIGN_OPS_ENABLED", "true").lower() == "true"

# ============================================================================
# AOL Action Handler Registration
# ============================================================================

def register_campaign_ops_handlers():
    """
    Register Campaign Ops action handlers with AOL daemon.
    
    This is called from aicmo/orchestration/daemon.py dispatch loop.
    Returns a dict of {action_type: handler_function}
    """
    if not AICMO_CAMPAIGN_OPS_ENABLED:
        return {}
    
    try:
        from aicmo.campaign_ops.actions import (
            handle_campaign_tick,
            handle_escalate_overdue_tasks,
            handle_weekly_campaign_summary,
        )
        
        return {
            "CAMPAIGN_TICK": handle_campaign_tick,
            "ESCALATE_OVERDUE_TASKS": handle_escalate_overdue_tasks,
            "WEEKLY_CAMPAIGN_SUMMARY": handle_weekly_campaign_summary,
        }
    except ImportError as e:
        print(f"Warning: Could not import Campaign Ops handlers: {e}")
        return {}


# ============================================================================
# Streamlit UI Helper
# ============================================================================

def get_session_for_campaign_ops():
    """
    Get database session for Campaign Ops operations.
    
    Used by Streamlit UI to access campaign data.
    Returns SQLAlchemy session or None if DB unavailable.
    """
    try:
        from aicmo.core.db import get_session
        return next(get_session())
    except Exception as e:
        print(f"Warning: Could not get database session: {e}")
        return None


def render_campaign_ops_ui():
    """
    Render Campaign Ops Streamlit UI.
    
    This is called from streamlit_pages/aicmo_operator.py in the Campaign Ops tab.
    """
    if not AICMO_CAMPAIGN_OPS_ENABLED:
        import streamlit as st
        st.error("Campaign Ops feature is not enabled. Set AICMO_CAMPAIGN_OPS_ENABLED=true")
        return
    
    try:
        from aicmo.campaign_ops.ui import render_campaign_ops_dashboard
        render_campaign_ops_dashboard()
    except ImportError as e:
        import streamlit as st
        st.error(f"Could not load Campaign Ops UI: {e}")
    except Exception as e:
        import streamlit as st
        st.error(f"Error rendering Campaign Ops UI: {e}")
