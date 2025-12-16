# RUNBOOK: GO-LIVE BASELINE (P0/P1 HARDENING)

**Last Updated**: December 16, 2025  
**Status**: ✓ READY FOR ACTIVATION  
**Tested**: All P0 and P1 fixes verified with 17 passing tests + PostgreSQL integration

---

## EXECUTIVE SUMMARY

AICMO has been hardened with **3 critical P0 fixes** and **2 high P1 fixes**:

| Fix | Status | Impact |
|-----|--------|--------|
| **P0.1**: AOL tables migrated to DB | ✓ DONE | Daemon no longer crashes on startup |
| **P0.2**: LLM graceful degradation | ✓ DONE | System safe without OpenAI key |
| **P0.3**: AOL integrated into operator flow | ✓ DONE | Can enqueue and run actions via UI |
| **P1.4**: Deprecated entrypoints quarantined | ✓ DONE | Makefile points to canonical UI only |
| **P1.5**: Integration tests added | ✓ DONE | Real PostgreSQL tested successfully |

---

## DEFINITION OF DONE - VERIFICATION

### ✓ A) AOL Tables Migrated

**Command to verify**:
```bash
python scripts/db_list_tables.py
```

**Expected output**:
```
✓ All 5 AOL tables present
  - aol_control_flags
  - aol_tick_ledger
  - aol_lease
  - aol_actions
  - aol_execution_logs
```

### ✓ B) Daemon Runs 2 Ticks Without Crash

**Command to test**:
```bash
python scripts/run_aol_daemon.py --proof --ticks 2
```

**Expected output**:
```
[AOL] Database initialized: <DATABASE_URL>
[AOL] PROOF mode: True
[AOL] Max ticks: 2
[AOL Tick 0] SUCCESS | Actions: 0 attempted, 0 succeeded | Duration: 0.XXs
[AOL Tick 1] SUCCESS | Actions: 0 attempted, 0 succeeded | Duration: 0.XXs
```

### ✓ C) UI Boots Without OpenAI Key

**Test command**:
```bash
# Ensure key is NOT set
unset OPENAI_API_KEY

# Run UI (Ctrl+C to stop)
streamlit run streamlit_pages/aicmo_operator.py --server.port 8501

# In browser: http://localhost:8501
# Should show LLM status but NOT crash
```

**Expected in UI**:
- Loads successfully
- "Autonomy" tab visible
- LLM status shows "not configured" (not crash)
- Can still view/enqueue PROOF actions

### ✓ D) Operator Can Enqueue & View Actions

**Via UI**:
1. Navigate to "Autonomy" tab
2. Enable PROOF mode (toggle "Pause Daemon" button to show flags)
3. Fill "Enqueue Test Action" form:
   - Action Type: `POST_SOCIAL`
   - Payload: `{"platform":"twitter","message":"test"}`
4. Click "📤 Enqueue Action"
5. Should see success message + action ID

**Verification query**:
```bash
# If you have database access:
sqlite3 local.db "SELECT COUNT(*) FROM aol_actions WHERE status='PENDING';"
# Should return >= 1
```

### ✓ E) Deprecated Entrypoints Quarantined

**Verify Makefile**:
```bash
grep -A5 "^ui:" Makefile
```

**Expected output**:
```
ui:
    ... streamlit run streamlit_pages/aicmo_operator.py
```

**Verify deprecated files**:
```bash
head -20 app.py | grep DEPRECATED
head -20 streamlit_app.py | grep DEPRECATED
```

**Expected**: Both files contain "DEPRECATED" warning + reference to canonical UI

### ✓ F) Integration Tests Pass

**Run tests**:
```bash
# All new P0/P1 tests (SQLite-based, fast)
python -m pytest \
  tests/test_aol_schema_presence.py \
  tests/test_llm_graceful_degradation.py \
  tests/test_aol_loop_ticks.py \
  tests/test_canonical_ui_command.py \
  -v --tb=short

# PostgreSQL integration (requires AICMO_TEST_POSTGRES_URL set)
AICMO_TEST_POSTGRES_URL="$DATABASE_URL" \
python -m pytest tests/test_integration_postgres_aol.py -v --tb=short
```

**Expected**: All tests PASSED

### ✓ G) Full Test Suite Runs Green

**Command**:
```bash
python -m pytest -q
```

**Expected**: No new failures introduced by these changes

---

## QUICK START COMMANDS

### 1. Run Canonical UI

```bash
# Option A: Via Makefile
make ui

# Option B: Direct Streamlit
streamlit run streamlit_pages/aicmo_operator.py --server.port 8501

# Option C: Via wrapper script
streamlit run launch_operator.py

# Option D: Alternative ops shell
make ops-ui  # Runs on port 8510
```

### 2. Migrate Schema (if not already done)

```bash
# Apply AOL tables to database
python scripts/apply_aol_schema.py

# Verify tables created
python scripts/db_list_tables.py
```

### 3. Run Daemon (Local Testing)

```bash
# Run 2 ticks in PROOF mode (no real execution)
python scripts/run_aol_daemon.py --proof --ticks 2

# Run 5 ticks in PROOF mode
python scripts/run_aol_daemon.py --proof --ticks 5

# Run continuously (Ctrl+C to stop)
python scripts/run_aol_daemon.py --proof
```

### 4. Enqueue an Action via CLI

```python
python3 << 'EOF'
import os
import json
from aicmo.orchestration.queue import ActionQueue
from aicmo.orchestration.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get database URL (uses same config as everywhere else)
db_url = os.getenv('DATABASE_URL', 'sqlite:///local.db')

# Connect
engine = create_engine(db_url, future=True)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Enqueue action
action = ActionQueue.enqueue_action(
    session=session,
    action_type="POST_SOCIAL",
    payload={
        "platform": "twitter",
        "message": "Test message from CLI"
    },
    idempotency_key="cli_test_001"
)

print(f"✓ Action enqueued: {action.idempotency_key}")
session.close()
EOF
```

---

## CONFIGURATION

### Environment Variables (Optional)

```bash
# Database URL (required for real operations)
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# LLM Configuration (optional - system degrades gracefully without)
export OPENAI_API_KEY="sk-..."
export AICMO_OPENAI_MODEL="gpt-4o-mini"  # default

# Daemon PROOF mode (prevent real execution during testing)
export AOL_PROOF_MODE="1"  # or "0"

# Feature flags
export AICMO_USE_LLM="1"  # enable/disable LLM features
```

### Database Requirements

**PostgreSQL** (Production):
- Must be accessible via DATABASE_URL
- AOL tables auto-created by `scripts/apply_aol_schema.py`
- Test database: `AICMO_TEST_POSTGRES_URL` for integration tests

**SQLite** (Local Development):
- Default: `sqlite:///local.db`
- Works for local testing of daemon
- All tests compatible

---

## REAL MODE vs PROOF MODE

### PROOF Mode (Safe Testing)
```bash
# Recommended for testing
AOL_PROOF_MODE=1 python scripts/run_aol_daemon.py --ticks 2

# Actions execute logic but write artifacts only
# No real social media posts, no real emails sent
# Safe for development and validation
```

### REAL Mode (Production Use)
```bash
# ⚠️  Use only in production with proper credentials/approvals
python scripts/run_aol_daemon.py

# Actions execute actual integrations:
# - POST_SOCIAL: Actually posts to social media
# - SEND_EMAIL: Actually sends emails
# - etc.

# Requires:
# - Valid provider credentials (Twitter API key, etc.)
# - Proper authorization
# - Monitoring/alerting in place
```

**Current Status**: REAL mode blocked by default (not fully wired into UI)

---

## KNOWN LIMITATIONS & FUTURE WORK

### Still TODO (Not in P0/P1 scope)

- [ ] **Client intake workflow**: No way for external clients to submit briefs
- [ ] **Billing system**: No pricing tier or payment integration
- [ ] **Strategy/Creative engines**: Not implemented
- [ ] **Review workflow**: No human-in-loop QA
- [ ] **Provider chain abstraction**: Locked into OpenAI

### Monitoring Recommendations

- [ ] Set up Datadog/New Relic monitoring for daemon ticks
- [ ] Alert on failed actions (DLQ > 0)
- [ ] Monitor lease expiration/renewal cycles
- [ ] Track action success rate (actions_succeeded / actions_attempted)

---

## TROUBLESHOOTING

### "no such table: aol_lease" Error

**Cause**: AOL tables not migrated  
**Fix**:
```bash
python scripts/apply_aol_schema.py
python scripts/db_list_tables.py  # verify
```

### "OPENAI_API_KEY not set" Error

**Cause**: LLM-dependent feature called without key  
**Fix**: Either set the key OR check `llm_enabled()` before calling LLM functions  
```bash
export OPENAI_API_KEY="sk-..."
```

### Daemon exits immediately with no logs

**Cause**: Lease manager failing (tables missing or DB issue)  
**Checklist**:
1. Run `python scripts/db_list_tables.py` - verify AOL tables exist
2. Run `python scripts/apply_aol_schema.py` if missing
3. Check DATABASE_URL is set correctly
4. Check database is accessible: `psql $DATABASE_URL -c "SELECT 1"`

### UI "Autonomy features require database connection"

**Cause**: Database session unavailable  
**Fix**: Ensure DATABASE_URL is set and database is accessible

### Action stuck in PENDING status forever

**Cause**: Daemon not running or action adapter failed  
**Checklist**:
1. Is daemon running? `ps aux | grep aol_daemon`
2. Check daemon logs for errors
3. If adapter fails consistently, action goes to RETRY/DLQ
4. View execution logs in Autonomy tab for details

---

## ROLLBACK INSTRUCTIONS

If needed to rollback these changes:

```bash
# 1. Stop daemon
pkill -f run_aol_daemon

# 2. Stop UI
pkill -f streamlit

# 3. Revert code
git reset --hard HEAD~1  # or specific commit

# 4. Database NOTE: AOL tables will remain (safe to keep)
# To remove them (NOT recommended):
# DROP TABLE IF EXISTS aol_execution_logs, aol_actions, 
#   aol_tick_ledger, aol_lease, aol_control_flags;
```

---

## GETTING HELP

### Check Status

```bash
# Database connectivity
python scripts/db_list_tables.py

# LLM configuration
python3 -c "from aicmo.core.llm.runtime import safe_llm_status; import json; print(json.dumps(safe_llm_status(), indent=2))"

# Daemon health (requires running daemon)
# Check UI Autonomy tab for lease status, tick summary, logs
```

### Run Tests

```bash
# Quick smoke tests (< 5 seconds)
python -m pytest tests/test_aol_schema_presence.py -v

# Full test suite
python -m pytest -v

# Specific test
python -m pytest tests/test_llm_graceful_degradation.py::test_require_llm_raises_with_clear_message -v
```

### Logs

- **Daemon**: Printed to stdout, includes tick summaries
- **UI**: Streamlit logs to console + shows errors in browser
- **Database**: Check `aol_execution_logs` table for detailed action traces

---

## SUPPORT & ESCALATION

**For issues not covered above**:

1. Check `tests/` for examples of correct usage
2. Search code for `require_llm()` calls (shows how LLM gating works)
3. Review `aicmo/orchestration/daemon.py` for daemon logic
4. Check `streamlit_pages/aicmo_operator.py` for UI integration

---

## FILES ADDED/MODIFIED (Summary)

### New Scripts
- `scripts/db_list_tables.py` - List database tables (verify migrations)
- `scripts/apply_aol_schema.py` - Apply AOL schema to database

### New Tests (17 total)
- `tests/test_aol_schema_presence.py` - Verify tables exist (5 tests)
- `tests/test_llm_graceful_degradation.py` - LLM without key (5 tests)
- `tests/test_aol_loop_ticks.py` - Daemon ticks (3 tests)
- `tests/test_canonical_ui_command.py` - UI command verification (4 tests)
- `tests/test_integration_postgres_aol.py` - Real PostgreSQL integration (4 tests)

### Modified Core Files
- `aicmo/llm/brief_parser.py` - Added `require_llm()` gating
- `aicmo/llm/client.py` - Added graceful degradation when LLM disabled
- `streamlit_pages/aicmo_operator.py` - Added AOL action enqueuing UI section

### Already Present (Verified Correct)
- `scripts/run_aol_daemon.py` - Already correct, initializes DB
- `scripts/bootstrap_db_schema.py` - Already correct, runs migrations
- `app.py`, `streamlit_app.py` - Already have deprecation warnings
- `Makefile` - Already points `ui` target to canonical path

---

## DEPLOYMENT CHECKLIST

Before going live:

- [ ] All 17 tests pass: `pytest tests/test_aol*.py tests/test_llm*.py tests/test_canonical*.py -q`
- [ ] Database tables verified: `python scripts/db_list_tables.py`
- [ ] UI boots: `streamlit run streamlit_pages/aicmo_operator.py`
- [ ] Daemon runs 2 ticks: `python scripts/run_aol_daemon.py --proof --ticks 2`
- [ ] No OpenAI key required: `unset OPENAI_API_KEY && streamlit ...`
- [ ] Makefile `ui` target is canonical: `grep streamlit_pages/aicmo_operator.py Makefile`
- [ ] Integration tests pass (if PostgreSQL available): `AICMO_TEST_POSTGRES_URL=$DB pytest tests/test_integration*.py -q`

---

## ACTIVATION PROCEDURE

1. **Backup database** (if production)
2. **Run schema migration**: `python scripts/apply_aol_schema.py`
3. **Verify tables**: `python scripts/db_list_tables.py`
4. **Run tests**: `pytest -q`
5. **Start UI**: `make ui` or `streamlit run streamlit_pages/aicmo_operator.py`
6. **Test action enqueuing** via Autonomy tab (PROOF mode)
7. **Monitor logs** for any issues
8. **Deploy to staging** first, then production

---

**Document prepared**: December 16, 2025  
**For questions**: See troubleshooting section above or review test files for examples.
