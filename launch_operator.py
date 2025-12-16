#!/usr/bin/env python3
"""
AICMO Canonical Operator Dashboard — Streamlit Application.

⚠️  LEGACY SHIM (DO NOT USE IN NEW DEPLOYMENTS):

THIS FILE IS DEPRECATED. Use the canonical launch script instead:

  scripts/launch_operator_ui.sh
  OR
  python -m streamlit run streamlit_pages/aicmo_operator.py

Historical note:
- This file was used before scripts/launch_operator_ui.sh was created
- It attempted to be a minimal wrapper but added unnecessary indirection
- All new deployments should use scripts/launch_operator_ui.sh
"""

import sys
import os

# PHASE 2: DEPRECATED LAUNCHER GUARD
if os.getenv('AICMO_ALLOW_DEPRECATED_LAUNCHER', '').lower() != '1':
    sys.stderr.write(
        "ERROR: launch_operator.py is deprecated.\n"
        "Use: scripts/launch_operator_ui.sh\n"
        "     OR: python -m streamlit run streamlit_pages/aicmo_operator.py\n"
        "\n"
        "To override (dev only): export AICMO_ALLOW_DEPRECATED_LAUNCHER=1\n"
    )
    sys.stderr.flush()
    sys.exit(1)

# Setup path (avoid using pathlib here to prevent circular import with operator module)
_operator_file_dir = os.path.dirname(os.path.abspath(__file__))
if _operator_file_dir not in sys.path:
    sys.path.insert(0, _operator_file_dir)

# Load environment
from dotenv import load_dotenv
_env_path = os.path.join(_operator_file_dir, ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)

# Now import and run the canonical UI
# Since this file is executed as __main__, we can safely import the aicmo module
# and other dependencies without name collision
try:
    from streamlit_pages import aicmo_operator  # noqa: F401
    
except Exception as e:
    # Graceful error handling
    import streamlit as st
    st.set_page_config(page_title="AICMO Operator — Startup Error", layout="wide")
    st.error(f"Failed to load AICMO Operator Dashboard: {str(e)}")
    
    import traceback
    with st.expander("Full Error Details"):
        st.code(traceback.format_exc())
    
    st.stop()
