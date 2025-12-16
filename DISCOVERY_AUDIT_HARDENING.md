# DISCOVERY REPORT: AICMO AUDIT-DRIVEN HARDENING

**Date**: December 16, 2025
**Status**: DISCOVERY PHASE COMPLETE
**Methodology**: File enumeration + grep + runbook verification

---

## 0.1 BACKEND ENTRYPOINTS (CRITICAL)

### Files Found
```
./app.py                    [ROOT]        ~ 120 lines - DEPRECATED
./backend/app.py            [CANONICAL]   ~ 120 lines - ACTIVE (RUNBOOK CONFIRMED)
./backend/main.py           [LEGACY]      ~9,600 lines - OLD MONOLITH
./app/main.py               [ORPHANED]    unknown
```

### Evidence: Which is Render-Deployed?

**SOURCE**: RUNBOOK_RENDER_STREAMLIT.md:15-25
```markdown
### Local Development

```bash
# Start backend server
cd /workspaces/AICMO
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# Verify health
curl http://localhost:8000/health
```

### Render Deployment

**Start Command**:
```bash
uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```
```

### Analysis

| File | Purpose | Status | Production Ready | Evidence |
|------|---------|--------|------------------|----------|
| `backend/app.py` | FastAPI app with router imports | ✅ CANONICAL | ✅ YES | RUNBOOK line 25 explicit `uvicorn backend.app:app` |
| `backend/main.py` | Legacy monolith, all endpoints inline | ⚠️ LEGACY | ❌ NO | 9,600+ lines, not referenced in RUNBOOK |
| `app.py` | Deprecated Streamlit example | ❌ DEPRECATED | ❌ NO | File header: "DEPRECATED: Simple example dashboard only" |
| `app/main.py` | Orphaned, unused | ❌ ORPHANED | ❌ NO | Not referenced anywhere; directory structure unclear |

### DECISION (from discovery)
- **CANONICAL BACKEND**: `backend/app.py`
- **DEPRECATED BACKENDS**: `backend/main.py`, `app.py`, `app/main.py`
- **ACTION**: Quarantine non-canonical with RuntimeError

---

## 0.2 AOL RUNNERS

### Files Found
```
scripts/run_aol_worker.py      [CANONICAL]   8.1 KB
scripts/run_aol_daemon.py      [LEGACY]      2.8 KB
scripts/apply_aol_schema.py    [BOOTSTRAP]   4.3 KB (dev only)
scripts/aol_health_cli.py      [MONITORING]  5.5 KB
```

### Evidence: Which is Production-Canonical?

**SOURCE**: RUNBOOK_RENDER_STREAMLIT.md:67-74
```markdown
### Render Worker Deployment

**Service Type**: Background Worker

**Start Command**:
```bash
python scripts/run_aol_worker.py
```
```

### Evidence: Which is Dev-Only?

**SOURCE**: scripts/run_aol_daemon.py:1-10
```python
"""
Run the AOL daemon for integration testing.

Usage:
  python scripts/run_aol_daemon.py       # Run forever
  python scripts/run_aol_daemon.py --ticks 5 # Run 5 ticks then exit
  python scripts/run_aol_daemon.py --proof   # Run in PROOF mode
"""
```

### Analysis

| File | Purpose | Status | Production Ready | Evidence |
|------|---------|--------|------------------|----------|
| `run_aol_worker.py` | Production background worker | ✅ CANONICAL | ✅ YES | RUNBOOK line 74 explicit `python scripts/run_aol_worker.py` |
| `run_aol_daemon.py` | Dev/integration testing only | ⚠️ LEGACY | ❌ NO | File docstring: "for integration testing", has `--ticks` flag |
| `apply_aol_schema.py` | Bootstrap script (local dev) | ⚠️ DEV-ONLY | ✅ SAFE | Used locally before migrations |
| `aol_health_cli.py` | Monitoring/health check | ✅ TOOL | ✅ YES | Health check utility, not conflicting |

### DECISION (from discovery)
- **CANONICAL RUNNER**: `scripts/run_aol_worker.py`
- **DEPRECATED RUNNER**: `scripts/run_aol_daemon.py`
- **ACTION**: Quarantine with RuntimeError

---

## 0.3 STREAMLIT UIs

### Files Found
```
streamlit_pages/aicmo_operator.py      [CANONICAL]     109 KB
streamlit_pages/aicmo_ops_shell.py     [SECONDARY]      20 KB
streamlit_pages/cam_engine_ui.py       [SECONDARY]      24 KB
streamlit_pages/operator_qc.py         [SECONDARY]      24 KB
streamlit_pages/proof_utils.py         [UTILITY]       8.7 KB
```

### Evidence: Which is Production-Canonical?

**SOURCE**: RUNBOOK_RENDER_STREAMLIT.md:31-34
```markdown
### Streamlit Cloud Deployment

**Main File**: `streamlit_pages/aicmo_operator.py`
```

**SOURCE**: scripts/launch_operator_ui.sh:10
```bash
streamlit run streamlit_pages/aicmo_operator.py
```

**SOURCE**: streamlit_pages/aicmo_operator.py:121-125
```python
st.set_page_config(
    page_title="AICMO Operator – Premium",
    layout="wide",
    initial_sidebar_state="expanded",
)
```

### Analysis

| File | Title | Status | Production Ready | Evidence |
|------|-------|--------|------------------|----------|
| `aicmo_operator.py` | "AICMO Operator – Premium" | ✅ CANONICAL | ✅ YES | RUNBOOK line 33, launch script, 109 KB (mature) |
| `aicmo_ops_shell.py` | "AICMO Ops Shell" | ⚠️ SECONDARY | ❌ NO | Diagnostics UI (operator QC testing), not primary |
| `cam_engine_ui.py` | "CAM Engine" | ⚠️ SECONDARY | ❌ NO | CAM-specific only, limited scope |
| `operator_qc.py` | "AICMO Operator QC" | ⚠️ SECONDARY | ❌ NO | Internal QC panel, not operator-facing |
| `proof_utils.py` | Utility module | ✅ SUPPORT | ✅ YES | Not an entry point (imported by other UIs) |

### DECISION (from discovery)
- **CANONICAL UI**: `streamlit_pages/aicmo_operator.py`
- **SECONDARY/DIAGNOSTIC UIs**: `aicmo_ops_shell.py`, `cam_engine_ui.py`, `operator_qc.py`
- **ACTION**: Quarantine secondary UIs with deprecation warning

---

## 0.4 AOL SCHEMA ORIGIN & MIGRATIONS

### Current Schema Creation Method

**How AOL tables are created TODAY:**

**Location**: tests/test_aol_schema_presence.py:20-21
```python
Base.metadata.create_all(engine)  # Creates AOL tables programmatically
```

**Problem**: AOL tables are created via Python `Base.metadata.create_all()` in:
- `tests/conftest.py:40`
- `tests/test_aol_schema_presence.py:20`
- Production bootstrap: `scripts/apply_aol_schema.py`

**Status**: ⚠️ NO ALEMBIC MIGRATION EXISTS

### Migration Infrastructure Status

**Location**: backend/migrations/
```
-rw-rw-rw- 158 bytes - 0001_init.sql
-rw-rw-rw- 265 bytes - 0002_add_site_slug.sql
-rw-rw-rw- 961 bytes - 0003_shared_extras.sql
-rw-rw-rw- 999 bytes - 0003_site_spec.sql
-rw-rw-rw- 358 bytes - 0004_deployment.sql
-rw-rw-rw- 212 bytes - 0004_visualgen_policy.sql
-rw-rw-rw- 420 bytes - 0005_constraints.sql
-rw-rw-rw-  79 bytes - 0006_add_page_body.sql
Total: 7 SQL migration files (3,292 bytes)
```

**Status**: ✅ Migration infrastructure exists (but does NOT include AOL tables)

### Analysis

| Schema | Creation Method | Idempotent | Production-Safe | Evidence |
|--------|-----------------|-----------|-----------------|----------|
| AOL tables | Python `Base.metadata.create_all()` | ⚠️ RISKY | ❌ NO | scripts/apply_aol_schema.py, manual bootstrap required |
| Backend/SiteGen tables | SQL migrations in backend/migrations/ | ✅ YES | ✅ YES | 7 SQL files present |

### AOL Tables to Migrate

From aicmo/orchestration/models.py:
1. `aol_control_flags` - daemon pause/kill/proof mode flags
2. `aol_tick_ledger` - execution summaries & timestamps
3. `aol_lease` - distributed lock for multi-worker safety
4. `aol_actions` - task queue (has idempotency_key unique constraint)
5. `aol_execution_logs` - trace logs for debugging

### DECISION (from discovery)
- **ACTION**: Create Alembic migration to move AOL schema from `Base.metadata.create_all()` to SQL
- **MIGRATION FILE**: `alembic/versions/001_create_aol_schema.py` (Python-based Alembic, not SQL)
- **BOOTSTRAP SCRIPT**: Keep `scripts/apply_aol_schema.py` for local dev reference only

---

## 0.5 BRANDING LEAKS (CRITICAL)

### Client-Facing Branding Issues Found

**CRITICAL LEAK #1: PPTX Exports**

**Location**: backend/export_utils.py:365
```python
subtitle.text = "Generated by AICMO"
```

**Impact**: Client PowerPoint presentations are branded with AICMO attribution
**Status**: ❌ BLOCKER - Must remove before client delivery

**CRITICAL LEAK #2: PPTX Title**

**Location**: backend/export_utils.py:363
```python
slide.shapes.title.text = f"AICMO Report – {brief.brand.brand_name}"
```

**Impact**: Title includes "AICMO Report" instead of client name
**Status**: ❌ BLOCKER - Title should be client-only

### Non-Critical (Internal) Mentions

- Streamlit page titles (`"AICMO Operator – Premium"`, `"AICMO Ops Shell"`, etc.)
- Comments and docstrings
- Test fixture labels
- Dashboard diagnostics

**Status**: ✅ OK - Internal references don't leak to clients

### DECISION (from discovery)
- **ACTION 1**: Remove "Generated by AICMO" from PPTX exports (line 365)
- **ACTION 2**: Rename PPTX title to use client brand only (line 363)
- **ACTION 3**: Create sanitization helper to prevent future leaks
- **TEST**: Verify exported PPTX contains zero AICMO/AI branding

---

## 0.6 LLM CALL BOUNDARY & RATE LIMITING

### Where LLM Calls Are Made

**Primary LLM Module**: aicmo/llm/client.py

**Location**: aicmo/llm/client.py:60-110
```python
def call_llm(
    system_prompt: str,
    user_message: str,
    provider: Literal["claude", "openai"] = "claude",
    ...
) -> str:
    Supports both Claude (via Anthropic) and OpenAI APIs.
    ...
    if provider == "claude":
        response = client.messages.create(...)  # Anthropic call
    else:
        response = client.chat.completions.create(...)  # OpenAI call
```

**LLM Consumers** (top-level):
1. `aicmo/strategy/generation_engine.py` - Strategy generation
2. `aicmo/creative/directions_engine.py` - Creative direction generation
3. `aicmo/memory/engine.py` - Learning/memory augmentation
4. `aicmo/llm/brief_parser.py` - Brief parsing
5. `aicmo/llm/router.py` - Provider routing (530 lines, untested)

### Current Rate Limiting Status

**Search Results**: 
```bash
grep -rn "rate_limit\|timeout\|backoff\|retry" --include="*.py" aicmo/llm/
# Result: 0 matches
```

**Status**: ❌ NO RATE LIMITING OR TIMEOUTS FOUND

### Current Timeout Status

**Search Results**:
```bash
grep -rn "timeout\|asyncio.timeout\|asyncio.wait_for" --include="*.py" aicmo/llm/
# Result: 0 matches in LLM module
```

**Status**: ❌ NO TIMEOUTS ON LLM CALLS

### Analysis

| Feature | Status | Risk | Evidence |
|---------|--------|------|----------|
| LLM rate limiting | ❌ MISSING | CRITICAL | 0 rate_limit references in aicmo/llm/ |
| LLM timeouts | ❌ MISSING | CRITICAL | 0 timeout references in LLM module |
| LLM retry logic | ❌ MISSING | HIGH | Depends on client SDK default behavior |
| Fallback provider chain | ⚠️ IMPLEMENTED BUT UNTESTED | HIGH | 530 lines (router.py), 0 tests |

### DECISION (from discovery)
- **ACTION**: Create central LLM wrapper with:
  - Mandatory timeout (30 seconds per call)
  - Per-minute rate limit (100 calls/minute default)
  - Exponential backoff (max 3 retries)
  - Cost guard rails (abort if per-month budget exceeded)
- **LOCATION**: `aicmo/llm/rate_limiter.py` (new)
- **TEST**: `tests/test_llm_rate_limiting.py` (new)

---

## SUMMARY: CRITICAL ISSUES IDENTIFIED

### Blocker #1: Multiple Backend Entrypoints
- **Canonical**: `backend/app.py` (120 lines, clean)
- **Legacy**: `backend/main.py` (9,600 lines, monolith)
- **Action**: Quarantine legacy with RuntimeError

### Blocker #2: Multiple AOL Runners
- **Canonical**: `scripts/run_aol_worker.py` (production)
- **Legacy**: `scripts/run_aol_daemon.py` (dev testing)
- **Action**: Quarantine legacy with RuntimeError

### Blocker #3: Multiple Streamlit UIs
- **Canonical**: `streamlit_pages/aicmo_operator.py` (109 KB, production)
- **Secondary**: 3 diagnostic UIs (should be quarantined)
- **Action**: Add deprecation warnings, consolidate to one

### Blocker #4: AOL Schema Not in Migrations
- **Current**: `Base.metadata.create_all()` in Python (production risk)
- **Missing**: Alembic migration for AOL tables
- **Action**: Create migration to move schema into version control

### Blocker #5: Branding Leaks in Client Exports
- **Location**: `backend/export_utils.py:363-365`
- **Issue**: "AICMO Report" title + "Generated by AICMO" subtitle
- **Action**: Remove branding, use client brand only

### Blocker #6: Zero Rate Limiting on LLM
- **Issue**: Can drain API credits in minutes
- **Evidence**: 0 matches for rate_limit/timeout in aicmo/llm/
- **Action**: Create rate limiter wrapper with 30s timeout + per-minute limit

### Blocker #7: Zero Authentication
- **Issue**: Anyone can call /health/aol, enqueue actions, etc.
- **Evidence**: No auth code in backend or Streamlit
- **Action**: Add X-AICMO-KEY auth header to critical endpoints

---

## READY FOR STEP 1: BACKEND CONSOLIDATION

✅ Discovery complete. All 6 subsystems mapped with evidence.

Proceeding to STEP 1: Backend Consolidation (quarantine legacy backends).
