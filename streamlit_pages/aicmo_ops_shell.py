#!/usr/bin/env python3
"""
DEPRECATED_STREAMLIT_ENTRYPOINT: AICMO Ops Shell

This is a diagnostic/testing UI used for internal development and E2E sentinels.

**Production deployment must use: streamlit_pages/aicmo_operator.py**

Rationale:
- aicmo_ops_shell.py is a diagnostics dashboard (not for end-users)
- aicmo_operator.py (109 KB) is the production operator UI
- RUNBOOK_RENDER_STREAMLIT.md:33 specifies: streamlit_pages/aicmo_operator.py

If run directly, raises RuntimeError to prevent accidental deployment.
"""

import sys

raise RuntimeError(
    "DEPRECATED_STREAMLIT_ENTRYPOINT: streamlit_pages/aicmo_ops_shell.py is dev-only. "
    "Use 'streamlit run streamlit_pages/aicmo_operator.py' for production. "
    "See RUNBOOK_RENDER_STREAMLIT.md:33 for details."
)

sys.exit(1)
