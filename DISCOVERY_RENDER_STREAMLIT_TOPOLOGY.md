# DISCOVERY REPORT: RENDER + STREAMLIT TOPOLOGY
**Date**: December 16, 2025  
**Purpose**: Evidence-based assessment of deployment infrastructure

---

## 0.1 BACKEND FRAMEWORK + ENTRYPOINT

**Status**: ✅ **FOUND + FUNCTIONAL**

**Framework**: FastAPI (3 routers: health, learn, cam)

**Entrypoint File**: `backend/main.py` (line 383)

**Evidence**:
```python
# backend/main.py line 383
app = FastAPI(title="AICMO API")

# Routers included:
include_router(health_router, tags=["health"])
include_router(learn_router, tags=["learn"])
include_router(cam_router)
```

**Launch Command**:
```bash
python -m uvicorn backend.main:app --reload
# or for Render:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Current Health Routes**: Already include `/health` endpoint (status/version)

**Critical Finding**: NO __main__ block in backend/main.py → Must be run via uvicorn, not `python backend/main.py`

---

## 0.2 CANONICAL STREAMLIT UI

**Status**: ✅ **FOUND + FUNCTIONAL**

**File**: `streamlit_pages/aicmo_operator.py` (109,376 bytes)

**Other Streamlit Pages** (for reference):
- aicmo_ops_shell.py (19,495 bytes) — shell commands
- cam_engine_ui.py (23,645 bytes) — CAM-specific
- operator_qc.py (24,078 bytes) — QC workflows
- proof_utils.py (8,830 bytes) — utilities

**Launch Command**:
```bash
streamlit run streamlit_pages/aicmo_operator.py --server.port 8501
```

**Verified in Makefile**:
```bash
grep -A3 "^ui:" Makefile
# Output: streamlit run streamlit_pages/aicmo_operator.py
```

---

## 0.3 AOL (AUTONOMY) IMPLEMENTATION + RUNNERS

**Status**: ✅ **PARTIAL** (core exists, worker missing)

**AOL Module**: `aicmo/orchestration/` (19 files, well-structured)

**Key Components**:
- `aicmo/orchestration/daemon.py` — AOL tick loop
- `aicmo/orchestration/models.py` — DB tables (aol_*, leak, flags, etc.)
- `aicmo/orchestration/queue.py` — action queue + retry
- `aicmo/orchestration/adapters/` — 3 action adapters

**Existing Runners**:
| File | Exists | Purpose | Status |
|------|--------|---------|--------|
| `scripts/run_aol_daemon.py` | ✅ YES | Manual daemon trigger | Working (manual only) |
| `scripts/run_aol_worker.py` | ❌ NO | Render continuous worker | **MUST CREATE** |

**Critical Gap**: Daemon exists but **NOT auto-scheduled** (no cron, no systemd, no Render worker config)

---

## 0.4 DANGEROUS OPS IN STREAMLIT

**Status**: ⚠️ **HIGH-RISK FOUND**

**Raw SQL Execution Locations**:

| File | Line | Operation | Risk |
|------|------|-----------|------|
| `streamlit_pages/aicmo_operator.py` | 561-562 | `conn.execute(text(...))` | 🔴 RAW SQL |
| `streamlit_pages/aicmo_operator.py` | 610-611 | `conn.execute(text(...))` | 🔴 RAW SQL |
| `streamlit_pages/aicmo_operator.py` | 683-686 | `INSERT INTO aicmo_learn_items ...` | 🔴 RAW SQL |
| `streamlit_pages/aicmo_ops_shell.py` | 199 | `cursor.execute("SELECT ...")` | 🔴 RAW SQL |

**Example**:
```python
# streamlit_pages/aicmo_operator.py lines 561-562
conn.execute(
    text(
        """UPDATE aol_control_flags SET paused = :paused WHERE id = :id"""
    ),
    {"paused": paused, "id": flags.id}
)
```

**Assessment**: 
- ✅ Parameterized (not vulnerable to injection)
- ⚠️ But directly exposed in Streamlit UI
- ❌ No environment gating (always enabled)
- ❌ No confirmation dialogs

**Required Fix**: Wrap in `if AICMO_ENABLE_DANGEROUS_UI_OPS==1:` gate + confirmation

---

## 0.5 TEST FAILURE ROOT CAUSES (TOP 4)

**Total Test Collection**: 3,091 items collected with **4 ERRORS**

**Root Causes**:

| Error | File | Reason | Fix |
|-------|------|--------|-----|
| **Missing Dependency** | `tests/test_phase_c_analytics.py:25` | `from scipy import stats` — scipy not installed | Add to requirements |
| **Missing Export** | `tests/test_validation_integration.py:14` | Cannot import `_apply_wow_optional` from backend.main | Mark as xfail/legacy |
| **Syntax Error** | `aicmo/cam/auto.py:22` | Invalid Python (malformed function def) | Fix syntax |
| **Missing Class** | `backend/tests/test_cam_orchestrator.py:15` | Cannot import `CAMCycleConfig` from orchestrator | Mark as xfail/legacy |

**Evidence**:
```bash
pytest -q 2>&1 | grep "ERROR\|SyntaxError" | head -5

# Output:
# ERROR collecting tests/test_phase_c_analytics.py - ModuleNotFoundError: No module named 'scipy'
# ERROR collecting tests/test_validation_integration.py - ImportError: cannot import name '_apply_wow_optional'
# ERROR collecting backend/tests/test_cam_auto_runner.py - SyntaxError: invalid syntax
# ERROR collecting backend/tests/test_cam_orchestrator.py - ImportError: cannot import name 'CAMCycleConfig'
```

---

## SUMMARY TABLE

| Component | Status | Evidence | Blocker |
|-----------|--------|----------|---------|
| **Backend Framework** | ✅ FastAPI | backend/main.py:383, 3 routers | None |
| **Backend Entrypoint** | ✅ Ready | `uvicorn backend.main:app` | None |
| **Streamlit Canonical** | ✅ Found | streamlit_pages/aicmo_operator.py | None |
| **Streamlit Launch** | ✅ Ready | `streamlit run streamlit_pages/aicmo_operator.py` | None |
| **AOL Core** | ✅ Exists | aicmo/orchestration/ (19 files) | None |
| **AOL Daemon Manual** | ✅ Works | scripts/run_aol_daemon.py | Not auto-scheduled |
| **AOL Worker (Render)** | ❌ Missing | scripts/run_aol_worker.py not found | **MUST CREATE** |
| **Backend Health Endpoint** | ✅ Exists | /health in health_router | Need AOL-specific /health/aol |
| **Dangerous SQL in UI** | ⚠️ Present | 4 locations with raw SQL | Needs env gate + confirm |
| **Test Collection** | ❌ Broken | 4 import/syntax errors | Must fix to run tests |

---

## NEXT STEPS

✅ **Discovery Complete** - All required information gathered

**Proceeding to**:
1. **STEP 1**: Create `scripts/run_aol_worker.py` for Render continuous worker
2. **STEP 2**: Add `/health/aol` endpoint to backend
3. **STEP 3**: Wrap dangerous ops in Streamlit with env gate
4. **STEP 4**: Fix test collection errors + implement smoke test set
5. **STEP 5**: Create RUNBOOK_RENDER_STREAMLIT.md

---

**Discovery Status**: ✅ **COMPLETE**  
**Can Proceed to Implementation**: ✅ **YES**
