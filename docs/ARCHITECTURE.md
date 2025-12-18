# ARCHITECTURE.md — Canonical Entrypoints (Phase 1)

## Canonical Backend Entry

- **File:** backend/app.py
- **Status:** CANONICAL
- **Description:**
  - This is the ONLY backend entrypoint for AICMO.
  - All REST API routes are defined here.
  - Alternative: backend/main.py is DEPRECATED (shim only).
  - DO NOT add routes to backend/main.py.

## Canonical UI Entry

- **File:** operator_v2.py
- **Status:** CANONICAL
- **Description:**
  - This is the ONLY operator dashboard for AICMO.
  - All UI workflow logic is defined here.
  - Alternative: deprecated/ui/aicmo_operator_legacy.py is DEPRECATED.
  - DO NOT import from deprecated/ui/aicmo_operator_legacy.py.

## Deprecated Entrypoints

- **File:** deprecated/ui/aicmo_operator_legacy.py
  - DEPRECATED: Formerly streamlit_pages/aicmo_operator.py. Forbidden for import/use.
- **File:** backend/main.py
  - DEPRECATED: Shim for legacy compatibility. Forbidden for new routes.

