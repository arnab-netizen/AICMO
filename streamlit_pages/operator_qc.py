#!/usr/bin/env python3
"""
DEPRECATED_STREAMLIT_ENTRYPOINT: AICMO Operator QC

This is an internal Quality Assurance & Audit Panel for development use only.

**Production deployment must use: streamlit_pages/aicmo_operator.py**

Rationale:
- operator_qc.py is an internal QC panel (not for end-users or operators)
- aicmo_operator.py (109 KB) is the production operator UI
- RUNBOOK_RENDER_STREAMLIT.md:33 specifies: streamlit_pages/aicmo_operator.py

If run directly, raises RuntimeError to prevent accidental deployment.
"""

import sys

raise RuntimeError(
    "DEPRECATED_STREAMLIT_ENTRYPOINT: streamlit_pages/operator_qc.py is internal QC panel. "
    "Use 'streamlit run streamlit_pages/aicmo_operator.py' for production. "
    "See RUNBOOK_RENDER_STREAMLIT.md:33 for details."
)

sys.exit(1)
