#!/usr/bin/env python3
"""
DEPRECATED_STREAMLIT_ENTRYPOINT: CAM Engine UI

This is a CAM (Client Acquisition Module)-specific UI for testing the autonomous engine.

**Production deployment must use: streamlit_pages/aicmo_operator.py**

Rationale:
- cam_engine_ui.py is CAM-specific only (not general-purpose)
- aicmo_operator.py (109 KB) is the production operator UI (supports all modules)
- RUNBOOK_RENDER_STREAMLIT.md:33 specifies: streamlit_pages/aicmo_operator.py

If run directly, raises RuntimeError to prevent accidental deployment.
"""

import sys

raise RuntimeError(
    "DEPRECATED_STREAMLIT_ENTRYPOINT: streamlit_pages/cam_engine_ui.py is CAM-specific dev UI. "
    "Use 'streamlit run streamlit_pages/aicmo_operator.py' for production. "
    "See RUNBOOK_RENDER_STREAMLIT.md:33 for details."
)

sys.exit(1)
