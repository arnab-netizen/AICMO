# DISCOVERY REPORT - P0/P1 FIXES

**Date**: December 16, 2025  
**Scope**: Evidence-only discovery for AOL hardening fixes  
**Methodology**: File paths + command output verified

---

## 1. CANONICAL UI + DUPLICATES

### Discovery Commands
```bash
# Canonical UI directory
ls -lah streamlit_pages/
# Result: aicmo_operator.py exists + 4 others (ops_shell, cam_engine_ui, operator_qc, proof_utils)

# Root-level entrypoints
find . -maxdepth 1 -name "*app*.py" -o -name "launch*.py"
# Result: ./app.py, ./test_section_mapping.py, ./launch_operator.py, ./streamlit_app.py
```

### Canonical UI File
**Path**: [streamlit_pages/aicmo_operator.py](streamlit_pages/aicmo_operator.py)  
**Evidence**: Contains `import streamlit as st` and `st.set_page_config()` [line 33, line 108]  
**Size**: 105K (fully-featured)  
**Status**: PRIMARY, Currently used

### Deprecated Entrypoints (Confirmed)
| File | Evidence | Action |
|------|----------|--------|
| `app.py` | Root, <5K | QUARANTINE |
| `streamlit_app.py` | Root, <5K | QUARANTINE |
| `launch_operator.py` | Root, unclear purpose | QUARANTINE |

### Makefile Wiring (Current)
```
Line 79:  streamlit run streamlit_pages/aicmo_operator.py
Line 84:  streamlit run streamlit_pages/aicmo_ops_shell.py --server.port 8510
```
**Status**: Makefile already correct ✓

---

## 2. DATABASE + ALEMBIC WIRING

### Alembic Status
- **alembic.ini exists** ✓ [Root level]
- **alembic/ directory**: NOT FOUND ✗
- **Status**: PARTIAL - Config file only, no migrations directory

### Database URL Configuration
**Source**: `aicmo/core/db.py` [line 51]
```python
db_url = url or os.getenv('DATABASE_URL', 'sqlite:///local.db')
```

**Multiple DB engines found**:
- `aicmo/orchestration/daemon.py`: Uses DATABASE_URL env
- `aicmo/orchestration/lease.py`: Uses DATABASE_URL env  
- `aicmo/cam/api/review_queue.py`: Uses `sqlite:///./cam.db` hardcoded
- Default: `sqlite:///local.db`

**Current DB file**:
```bash
ls -lah *.db
# Result: local.db exists (12K)
```

### Schema Creation Strategy (Current)
**File**: `scripts/run_aol_daemon.py` [lines 48-50]
```python
from aicmo.orchestration.models import Base
Base.metadata.create_all(engine)
```

**File**: `scripts/bootstrap_db_schema.py` [exists, 167 lines]
- Runs `alembic upgrade head` programmatically
- Falls back to `Base.metadata.create_all()` if alembic fails
- Detects sqlite vs postgres

**Current Tables in local.db** (Confirmed via audit):
```
sqlite_master tables: alembic_version, memory_items, learn_items
Missing: aol_control_flags, aol_tick_ledger, aol_lease, aol_actions, aol_execution_logs
```

---

## 3. AOL CODE LOCATIONS + SCHEMA DEFINITION

### AOL Models (Confirmed)
**File**: `aicmo/orchestration/models.py` [lines 1-210]

**Tables Defined** (all in code, NOT in DB):
1. `aol_control_flags` - Daemon control (pause, kill, proof_mode)
2. `aol_tick_ledger` - Tick execution summaries
3. `aol_lease` - Distributed lock for daemon exclusivity
4. `aol_actions` - Task queue
5. `aol_execution_logs` - Execution traces

**Indexes Defined** (in code):
```python
Index("idx_aol_actions_status", "status")
Index("idx_aol_actions_not_before", "not_before_utc")
Index("idx_aol_actions_idempotency", "idempotency_key")
```

### AOL Imports in Codebase
- `aicmo/orchestration/daemon.py` - Main loop
- `aicmo/orchestration/lease.py` - Lease management
- `tests/orchestration/` - Unit tests (17 passing)
- `scripts/run_aol_daemon.py` - Runner script

### Schema Creation Call Sites
- **`scripts/run_aol_daemon.py`** [line 50]: `Base.metadata.create_all(engine)`
- **`scripts/bootstrap_db_schema.py`**: `alembic upgrade head` + fallback
- **Tests**: All tests use temp SQLite via `Base.metadata.create_all()`

**CRITICAL FINDING**: 
- Code assumes tables exist
- Tests create tables on-the-fly (temp DB)
- Production DB has NO AOL tables
- **Daemon will crash on first LeaseManager.acquire_or_renew() call**

---

## 4. OPENAI HARD DEPENDENCY (Runtime Call Sites)

### Import Locations
```python
aicmo/creative/directions_engine.py:     from openai import OpenAI
aicmo/memory/engine.py:                 from openai import OpenAI
aicmo/llm/brief_parser.py:              from openai import OpenAI
aicmo/llm/client.py:                    from openai import OpenAI
```

### Runtime API Key Checks
- `aicmo/llm/brief_parser.py` [line ~15]: Raises if no OPENAI_API_KEY
- `aicmo/llm/client.py` [line ~30]: Reads OPENAI_API_KEY, no fallback
- `aicmo/self_test/external_integrations_health.py`: Checks if configured

### LLM Runtime Gating (Exists)
**File**: `aicmo/core/llm/runtime.py`
```python
def llm_enabled() -> bool  # Checks if OPENAI_API_KEY set
def llm_status() -> dict   # Returns {enabled, reason, provider_name, key_present}
def require_llm()          # Raises RuntimeError if not enabled
```

**Status**: Helper layer EXISTS but NOT fully wired to call-sites

### UI LLM Status Display (Exists)
**File**: `streamlit_pages/aicmo_ops_shell.py`
```python
has_key = bool(os.getenv('OPENAI_API_KEY', '').strip())
st.write(f"**OPENAI_API_KEY**: {'✓ Set' if has_key else '✗ Not set'}")
```

**Status**: UI shows status but doesn't block operations safely

---

## 5. TEST COVERAGE & CURRENT STATE

### Existing Tests
- **`tests/test_db_schema_bootstrap_smoke.py`**: Tests bootstrap script
- **`tests/orchestration/`**: 17 AOL tests (all passing)
- **`tests/conftest.py`**: Uses temp SQLite, creates tables via `Base.metadata.create_all()`

### Reality Gap
- Tests: Temp SQLite + `Base.metadata.create_all()` = tables exist ✓
- Production: `local.db` has no aol_* tables ✗
- **Result**: FALSE CONFIDENCE - Tests pass but code fails on real DB

### Integration Tests
**File**: `tests/e2e/` exists but minimal
- NO postgres integration test for AOL
- NO test of daemon ticks with real DB + persistence

---

## 6. STREAMLIT ENTRYPOINT DEPRECATION

### Current Makefile (Already Correct)
```makefile
ui:
  streamlit run streamlit_pages/aicmo_operator.py
```

### Deprecated Files Still in Repo
- `app.py` - No deprecation warning found
- `streamlit_app.py` - No deprecation warning found
- `launch_operator.py` - Purpose unclear

### Required Action
Add deprecation warnings to old files

---

## 7. CURRENT DB STATE (Confirmed)

```bash
$ sqlite3 local.db ".tables"
alembic_version  memory_items     learn_items
```

**Missing**: All 5 AOL tables

---

## SUMMARY TABLE

| Item | Status | Evidence |
|------|--------|----------|
| **Canonical UI** | IDENTIFIED | `streamlit_pages/aicmo_operator.py` ✓ |
| **Deprecated Entrypoints** | FOUND | `app.py`, `streamlit_app.py`, `launch_operator.py` |
| **Alembic Config** | PARTIAL | `alembic.ini` exists, no migrations dir |
| **DB URL Source** | CONFIRMED | `os.getenv('DATABASE_URL', 'sqlite:///local.db')` |
| **AOL Models** | DEFINED | `aicmo/orchestration/models.py` [5 tables] |
| **AOL Schema in DB** | MISSING | local.db has NO aol_* tables |
| **AOL Bootstrap Script** | EXISTS | `scripts/bootstrap_db_schema.py` + `scripts/run_aol_daemon.py` |
| **OpenAI Imports** | 4 FILES | creative, memory, llm/brief_parser, llm/client |
| **LLM Runtime Helper** | EXISTS | `aicmo/core/llm/runtime.py` partially wired |
| **Daemon Runner** | EXISTS | `scripts/run_aol_daemon.py` |
| **Integration Tests** | MINIMAL | Only unit tests, no real DB tests |

---

## BLOCKERS FOUND

1. ✗ **AOL tables not migrated** → Daemon crashes immediately
2. ✗ **No integration test vs real DB** → False confidence
3. ✗ **LLM gating not fully wired** → UI not safe without key
4. ✗ **Deprecated entrypoints confusing** → No clear signal which to use

---

## READY FOR IMPLEMENTATION

**All facts established. Proceeding to STEP 1.**
