#!/usr/bin/env python3
"""
AICMO Canonical Operator Dashboard — Streamlit Application.

THIS IS THE CANONICAL UI ENTRYPOINT FOR ALL AICMO OPERATIONS.

This file is executed directly by Streamlit (not imported).
It bootstraps the complete dashboard from streamlit_pages/aicmo_operator.py

Usage:
  streamlit run operator.py
  streamlit run operator.py --server.port 8501

Design Notes:
- Minimal wrapper to avoid import/naming collisions
- All UI logic in streamlit_pages/aicmo_operator.py (modular)
- Streamlit loads this file directly, NOT as an importable module
"""

# ===== CRITICAL SECTION =====
# When Streamlit executes "streamlit run operator.py", it:
# 1. Executes this file as __main__
# 2. Does NOT import it as a module (no module namespace pollution)
# 3. Allows us to import operators module safely
# 
# This approach avoids the name collision issue where operator.py
# would shadow Python's built-in operator module if imported.
# ===========================

import sys
import os

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
