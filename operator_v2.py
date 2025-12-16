"""
AICMO Operator Dashboard V2 - Production Entrypoint

Build: OPERATOR_V2_2025_12_16
File: operator_v2.py
Launch: python -m streamlit run operator_v2.py

This is the new canonical Streamlit entrypoint with modular V2 architecture.
Features:
- 11 independent tabs (Intake, Strategy, Creatives, Execution, Monitoring, Lead Gen, 
  Campaigns, Autonomy, Delivery, Learn, System Diagnostics)
- Safe DB session wrapping (Fix C1)
- Backend-first HTTP wiring (Fix D)
- Comprehensive DB diagnostics (Fix C3)
- Graceful error handling - tabs degrade independently
- Production-ready watermark tracking
"""

import os
import sys
from pathlib import Path

# ===================================================================
# BUILD MARKER & DASHBOARD IDENTIFICATION
# ===================================================================
# This watermark should be visible in the running dashboard UI.
# If switching from operator.py to operator_v2.py doesn't change this watermark,
# the entrypoint switch is not working correctly.

DASHBOARD_BUILD = "OPERATOR_V2_2025_12_16"
RUNNING_FILE = __file__
RUNNING_CWD = os.getcwd()

# Print watermark to stderr on startup for entrypoint verification
print(f"[DASHBOARD] DASHBOARD_BUILD={DASHBOARD_BUILD}", flush=True)
print(f"[DASHBOARD] Running from: {RUNNING_FILE}", flush=True)
print(f"[DASHBOARD] Working directory: {RUNNING_CWD}", flush=True)

# ===================================================================
# ENVIRONMENT SETUP
# ===================================================================

# Load .env early
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Ensure project root is in PYTHONPATH
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set dashboard build in environment for child modules
os.environ["DASHBOARD_BUILD"] = DASHBOARD_BUILD

# ===================================================================
# STREAMLIT PAGE CONFIGURATION
# ===================================================================

import streamlit as st

st.set_page_config(
    page_title="AICMO Operator Dashboard V2",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================================================================
# MAIN APPLICATION
# ===================================================================

def main():
    """Main application entry point"""
    
    # Import router after page config is set
    from aicmo.ui_v2.router import render_router
    
    # Render the router with all tabs
    render_router()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import streamlit as st
        st.error(f"Critical error in operator_v2.py: {str(e)}")
        st.exception(e)
        sys.exit(1)
