# AICMO Streamlit UI - Canonical Entrypoint

## Quick Start
```bash
# Run the canonical AICMO operator dashboard:
python -m streamlit run aicmo_operator.py --server.port 8501
```

Or use the official launcher:
```bash
python run_streamlit.py
```

---

## Canonical UI: `aicmo_operator.py`

**This is the single, authoritative Streamlit UI for AICMO.**

### Features:
- ✅ Complete client acquisition (CAM) workflows
- ✅ Creative generation and direction management
- ✅ Social media campaign planning
- ✅ Quality control (QC) operator interface
- ✅ Delivery tracking and export management
- ✅ PDF report generation and download
- ✅ E2E testing and proof mode support
- ✅ Backend API integration
- ✅ Database-backed workflows

### File Details:
- **Lines**: 2,602
- **Functions**: 29
- **Located**: `streamlit_pages/aicmo_operator.py`
- **Used by**: `run_streamlit.py`, test suite, tools/audit scripts
- **Last modified**: Actively maintained

---

## Deprecated/Alternative Files

### `app.py` (Simple Example)
- **Status**: ⚠️ Deprecated (example only)
- **Use case**: Minimal demo dashboard for simple CopyHook/VisualGen calls
- **NOT for production**: Limited feature set (30% coverage)
- **Action**: Can be removed if not needed for demos

### `streamlit_app.py` (Report Generation)
- **Status**: ⚠️ Deprecated (backward compatibility only)
- **Use case**: E2E report generation tests
- **Features**: Report parsing, SHA256 hashing, download caching
- **Action**: Kept for legacy E2E tests; redirect new tests to aicmo_operator.py

### `.archive/deprecated_ui_prototypes/aicmo_operator_new.py.archived`
- **Status**: ❌ Removed (unused prototype)
- **Reason**: No active code references, Phase 5-7 docs only, feature parity with main operator

---

## Decision Criteria

The canonical UI was selected based on:

1. **Feature Coverage**: 92% (12/13 core features)
2. **Code Maturity**: 2,602 lines, 29 functions, actively maintained
3. **Integration Depth**: 7/7 integration points (official launcher, tests, tools, backend APIs, proof mode, QC, humanizer)
4. **Documentation**: 40+ references in completion docs
5. **Runtime Stability**: All three UIs boot successfully, but aicmo_operator.py is most comprehensive

See `UI_CANONICAL_DECISION_REPORT.md` for detailed analysis.

---

## Migration Guide

If you were using other UI files, migrate to the canonical one:

### From `app.py`:
```bash
# Old:
python -m streamlit run app.py

# New:
python -m streamlit run streamlit_pages/aicmo_operator.py
```

### From `streamlit_app.py`:
```bash
# Old:
streamlit run streamlit_app.py

# New:
streamlit run streamlit_pages/aicmo_operator.py
```

---

## Single Source of Truth

Going forward:
- ✅ **DO** use: `streamlit run streamlit_pages/aicmo_operator.py`
- ❌ **DON'T** use: `app.py`, `streamlit_app.py`, or any other operator*.py

All official documentation, scripts, and CI/CD should reference only the canonical UI.

---

## Questions?

Refer to `UI_CANONICAL_DECISION_REPORT.md` for the full audit trail and decision rationale.
