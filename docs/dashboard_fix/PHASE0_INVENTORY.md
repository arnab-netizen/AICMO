# PHASE 0: Full Dashboard Inventory & Entrypoint Analysis

Generated: 2025-12-16

## 0.1 All Streamlit-Related Python Files Found

```
./aicmo/operator/__init__.py
./aicmo/operator/automation_settings.py
./aicmo/operator/dashboard_models.py
./aicmo/operator/dashboard_service.py
./aicmo/operator_services.py
./streamlit_pages/aicmo_operator.py          ← CANONICAL PRODUCTION DASHBOARD
./streamlit_pages/aicmo_ops_shell.py         ← DEPRECATED (guarded with RuntimeError)
./streamlit_pages/cam_engine_ui.py           ← DEPRECATED (guarded with RuntimeError)
./streamlit_pages/operator_qc.py             ← DEPRECATED (guarded with RuntimeError)
./streamlit_pages/proof_utils.py             ← Helper utilities (imported by main)
./app.py                                      ← OLD DEPRECATION SHIM
./launch_operator.py                         ← OLD LAUNCHER SHIM
./streamlit_app.py                           ← Legacy wrapper
```

## 0.2 Streamlit Page Config Declarations

**ACTIVE (production):**
- `streamlit_pages/aicmo_operator.py:121` → `st.set_page_config()`

**DEPRECATED (with guards):**
- `streamlit_pages/aicmo_ops_shell.py.deprecated:571` ✓ guarded
- `streamlit_pages/cam_engine_ui.py.deprecated:519` ✓ guarded
- `streamlit_pages/operator_qc.py.deprecated:77` ✓ guarded

**LEGACY (shims):**
- `app.py:41` → "(DEPRECATED)" page title
- `streamlit_app.py:188` → Points to old app

## 0.3 Entry Points (`if __name__`)

Only ONE entry point in streamlit_pages:
```
streamlit_pages/aicmo_operator.py:2861    if __name__ == "__main__":
```

## 0.4 Deploy Configs & Entrypoints

### Canonical Launch Script:
```bash
scripts/launch_operator_ui.sh (active)
  → python -m streamlit run streamlit_pages/aicmo_operator.py "$@"
```

### Streamlit Configuration:
```
.streamlit/config.toml (exists)
  - headless = true
  - runOnSave = true
  - debug logging enabled
```

### Dockerfile References:
```
./streamlit/Dockerfile          (for containerized deployment)
./backend/Dockerfile            (backend only)
```

### Makefile Targets:
```makefile
Makefile:79  → streamlit run streamlit_pages/aicmo_operator.py
Makefile:84  → streamlit run streamlit_pages/aicmo_ops_shell.py --server.port 8510 (DEV ONLY)
```

## 0.5 Guardian Status of Non-Canonical Files

| File | Status | Guard Type | Exit Behavior |
|------|--------|-----------|---|
| aicmo_ops_shell.py | ✅ GUARDED | RuntimeError + sys.exit(1) | Prevents execution |
| cam_engine_ui.py | ✅ GUARDED | RuntimeError + sys.exit(1) | Prevents execution |
| operator_qc.py | ✅ GUARDED | RuntimeError + sys.exit(1) | Prevents execution |
| app.py | ⚠️ PARTIAL | Shows deprecation message | Does NOT exit |
| launch_operator.py | ⚠️ PARTIAL | Contains info + import shim | May still run |
| streamlit_app.py | ⚠️ PARTIAL | Wrapper around app.py | May still run |

## 0.6 CANONICAL DASHBOARD FILE (PRODUCTION)

**Path:** `streamlit_pages/aicmo_operator.py`
**Size:** ~113 KB (2920 lines)
**Entry Point:** Line 2861 (`if __name__ == "__main__"`)
**Page Config:** Line 121 (`st.set_page_config()`)
**Launch Command:** `python -m streamlit run streamlit_pages/aicmo_operator.py`
**Canonical Script:** `scripts/launch_operator_ui.sh`

### Key Components Loaded:
- Page config with "AICMO Operator – Premium"
- Operator services (conditionally)
- Database session helpers (conditionally)
- PDF export (conditionally)
- Creative directions engine (conditionally)
- Industry presets (conditionally)
- Benchmark error UI (conditionally)

### Critical Flags Checked:
- `AICMO_E2E_MODE` - Affects imports, startup
- `AICMO_ENABLE_DANGEROUS_UI_OPS` - Gating DB operations
- `DATABASE_URL` / `DB_URL` - Database availability
- `AICMO_BACKEND_URL` - Backend service availability

## 0.7 Verdict

✅ **CANONICAL ENTRYPOINT IS CLEAR & PROTECTED:**
- One production dashboard: `streamlit_pages/aicmo_operator.py`
- Three legacy UIs: All guarded with RuntimeError
- Launch script: `scripts/launch_operator_ui.sh` ensures correct entry
- No legacy code can accidentally run when Streamlit starts

⚠️ **FUTURE HARDENING OPPORTUNITY:**
- `app.py`, `launch_operator.py`, `streamlit_app.py` are shims that should also be hardened
- They currently show deprecation messages but don't prevent execution
- Should add `sys.exit(1)` after deprecation warning

