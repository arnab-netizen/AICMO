# RUNBOOK: Render + Streamlit Deployment

## Overview

AICMO is deployed with a split architecture:
- **Backend (FastAPI)**: Hosted on Render as a Web Service
- **UI (Streamlit)**: Deployed separately on Streamlit Cloud
- **AOL Worker**: Runs continuously on Render as a Background Worker (or Cron job)

This runbook covers operational procedures for the production deployment.

---

## 1. Backend (FastAPI) - Render Web Service

### Local Development

```bash
# Start backend server
cd /workspaces/AICMO
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# Verify health
curl http://localhost:8000/health
curl http://localhost:8000/health/aol
```

### Render Deployment

**Service Type**: Web Service

**Build Command**:
```bash
pip install -r requirements.txt
```

**Start Command**:
```bash
uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```

**Required Environment Variables**:
```
DATABASE_URL=postgresql://...         # Neon Postgres connection string
OPENAI_API_KEY=sk-...                 # OpenAI API key (if using LLM features)
AICMO_ENABLE_DANGEROUS_UI_OPS=0       # Never enable in production
```

**Health Checks**:
- Path: `/health`
- Interval: 30s
- Timeout: 5s

---

## 2. Streamlit UI - Streamlit Cloud (or Render)

### Local Development

```bash
# Launch Streamlit operator UI
streamlit run streamlit_pages/aicmo_operator.py

# Or use the launch script
./scripts/launch_operator_ui.sh
```

### Streamlit Cloud Deployment

**Main File**: `streamlit_pages/aicmo_operator.py`

**Required Environment Variables**:
```
AICMO_BACKEND_URL=https://aicmo-backend.onrender.com   # Backend API base URL
AICMO_ENABLE_DANGEROUS_UI_OPS=0                        # MUST be 0 in production
```

**Optional Variables**:
```
DATABASE_URL=postgresql://...   # Only if backend endpoint unavailable (not recommended)
```

**Safety Notes**:
- ⚠️ **NEVER** set `AICMO_ENABLE_DANGEROUS_UI_OPS=1` in production
- UI should consume `/health/aol` endpoint from backend (no direct DB access)
- If backend is unreachable, UI shows read-only error state

---

## 3. AOL Worker - Render Background Worker

### What is the AOL Worker?

The **Autonomy Orchestration Layer (AOL)** worker runs continuously in the background, executing scheduled marketing tasks from a queue.

**Safety features**:
- Distributed lease prevents multiple workers from running simultaneously
- Respects control flags (pause, kill, proof mode)
- Writes tick ledger every iteration for monitoring
- Does NOT require OpenAI at import time (crash-safe)

### Render Worker Deployment

**Service Type**: Background Worker

**Build Command**:
```bash
pip install -r requirements.txt
```

**Start Command**:
```bash
python scripts/run_aol_worker.py
```

**Required Environment Variables**:
```
DATABASE_URL=postgresql://...                # Neon Postgres (required)
AOL_TICK_INTERVAL_SECONDS=30                 # Time between ticks (default: 30)
AOL_MAX_ACTIONS_PER_TICK=3                   # Max actions per iteration (default: 3)
AOL_MAX_TICK_SECONDS=20                      # Tick timeout (default: 20)
AOL_PROOF_MODE=true                          # true=artifacts only, false=real execution
```

**Optional Variables**:
```
OPENAI_API_KEY=sk-...          # Only needed if LLM-based actions are enabled
```

### Render Cron Fallback

If Render Background Worker is not available, use **Cron Job** instead:

**Schedule**: `*/5 * * * *` (every 5 minutes)

**Command**:
```bash
python scripts/run_aol_worker.py --max-ticks=1
```

**Note**: Add `--max-ticks=1` flag to run single iteration and exit (cron-safe).

---

## 4. AOL Health Monitoring

### Check Worker Status

```bash
# From command line (requires DATABASE_URL)
python scripts/aol_health_cli.py

# Via backend API
curl https://aicmo-backend.onrender.com/health/aol | jq
```

### Health Indicators

**Last Tick Age**:
- ✅ < 60 seconds: Worker is active
- ⚠️ 60-300 seconds: Worker may be slow or paused
- ❌ > 300 seconds: Worker is likely stuck or dead

**Lease Status**:
- ✅ Valid lease with TTL > 0: Worker is running
- ⚠️ Expired lease: Worker crashed without cleanup
- ✅ No lease: Worker is idle (OK if paused)

**Control Flags**:
- `paused=true`: Worker is intentionally stopped (holds lease, does no work)
- `killed=true`: Worker will exit on next tick
- `proof_mode=true`: **REQUIRED for production** (no real outbound actions)

---

## 5. Common Operations

### Pause the Worker

```bash
# Set pause flag in database
psql $DATABASE_URL -c "UPDATE aol_control_flags SET paused = true WHERE id = 1;"
```

Worker will:
- Stop processing actions
- Keep holding lease (prevents other workers from starting)
- Sleep and check flags every 5 seconds
- Resume when `paused=false`

### Resume the Worker

```bash
psql $DATABASE_URL -c "UPDATE aol_control_flags SET paused = false WHERE id = 1;"
```

### Kill the Worker (Graceful Exit)

```bash
psql $DATABASE_URL -c "UPDATE aol_control_flags SET killed = true WHERE id = 1;"
```

Worker will:
- Finish current tick
- Release lease
- Exit with code 0

### Enable PROOF Mode (Required for Production)

```bash
psql $DATABASE_URL -c "UPDATE aol_control_flags SET proof_mode = true WHERE id = 1;"
```

**CRITICAL**: PROOF mode must ALWAYS be enabled in production. This prevents:
- Real social media posts
- Real email sends
- Real API calls to external services

All actions write proof artifacts to disk instead.

### Enable REAL Mode (Dev/Staging Only)

```bash
# ⚠️ DANGER: Only in development/staging environments
psql $DATABASE_URL -c "UPDATE aol_control_flags SET proof_mode = false WHERE id = 1;"
```

**NEVER enable REAL mode in production without explicit approval and monitoring.**

---

## 6. Troubleshooting

### Worker is Not Running Ticks

**Check 1: Is lease held?**
```bash
python scripts/aol_health_cli.py | grep -A 5 "LEASE"
```

**Check 2: Is worker paused?**
```bash
python scripts/aol_health_cli.py | grep -A 5 "CONTROL FLAGS"
```

**Check 3: Check Render logs**
```bash
# Via Render dashboard > Logs
# Look for "FATAL" or "ERROR" messages
```

**Common causes**:
- Database connection timeout → Check DATABASE_URL
- Lease is stuck (expired but not released) → Manually delete lease row
- Worker crashed → Check Render logs for Python traceback

### Lease is Stuck

If lease is expired but worker is not releasing it:

```bash
# Force release lease (DANGER: only if worker is confirmed dead)
psql $DATABASE_URL -c "DELETE FROM aol_lease;"
```

Worker will reacquire lease on next tick.

### Queue is Backing Up (Many Pending Actions)

**Check DLQ** (Dead Letter Queue):
```bash
python scripts/aol_health_cli.py | grep -A 5 "ACTION QUEUE"
```

**Clear DLQ** (if actions are invalid):
```bash
psql $DATABASE_URL -c "UPDATE aol_actions SET status = 'CANCELLED' WHERE status = 'DLQ';"
```

**Increase tick rate** (process more actions):
```bash
# On Render, set environment variable:
AOL_MAX_ACTIONS_PER_TICK=10
# Then restart worker
```

### Streamlit Shows "Backend Unavailable"

**Check 1: Is backend running?**
```bash
curl https://aicmo-backend.onrender.com/health
```

**Check 2: Correct backend URL in Streamlit?**
```bash
# Streamlit environment must have:
AICMO_BACKEND_URL=https://aicmo-backend.onrender.com
```

**Check 3: CORS enabled on backend?**
- Verify backend allows requests from Streamlit Cloud domain

### Worker Crashes on Startup

**Check 1: DATABASE_URL set?**
```bash
# In Render dashboard > Environment
# Verify DATABASE_URL is present and starts with postgresql://
```

**Check 2: Check for import errors**
```bash
# Locally, test import without OpenAI key:
unset OPENAI_API_KEY
python -c "import scripts.run_aol_worker; print('OK')"
```

---

## 7. Emergency Stop

### Full System Shutdown

1. **Pause worker**:
   ```bash
   psql $DATABASE_URL -c "UPDATE aol_control_flags SET paused = true WHERE id = 1;"
   ```

2. **Stop backend** (Render dashboard):
   - Navigate to Web Service
   - Click "Suspend"

3. **Stop Streamlit** (Streamlit Cloud dashboard):
   - Navigate to app settings
   - Click "Stop app"

### Resume from Emergency Stop

1. **Resume worker**:
   ```bash
   psql $DATABASE_URL -c "UPDATE aol_control_flags SET paused = false WHERE id = 1;"
   ```

2. **Start backend** (Render):
   - Click "Resume"

3. **Start Streamlit**:
   - Click "Reboot app"

---

## 8. Monitoring Checklist

**Daily**:
- [ ] Check last tick age < 5 minutes
- [ ] Verify no DLQ growth
- [ ] Confirm `proof_mode=true` in production

**Weekly**:
- [ ] Review execution logs for errors
- [ ] Check database disk usage
- [ ] Verify lease is not stuck

**On Deploy**:
- [ ] Run smoke tests: `pytest -m smoke -q`
- [ ] Verify `/health` and `/health/aol` endpoints
- [ ] Confirm worker acquires lease within 60s
- [ ] Test pause/resume cycle

---

## 9. Environment Variable Reference

### Backend (Required)
| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | Neon Postgres connection |
| `PORT` | `8000` | Render auto-sets this |

### Backend (Optional)
| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | `(none)` | Only if LLM features enabled |
| `DB_STARTUP_RETRY_SECS` | `30` | DB connection retry timeout |

### AOL Worker (Required)
| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...` | Same as backend |
| `AOL_TICK_INTERVAL_SECONDS` | `30` | Time between ticks |
| `AOL_MAX_ACTIONS_PER_TICK` | `3` | Max actions per tick |
| `AOL_MAX_TICK_SECONDS` | `20` | Tick timeout |
| `AOL_PROOF_MODE` | `true` | **MUST be true in production** |

### Streamlit UI (Required)
| Variable | Example | Description |
|----------|---------|-------------|
| `AICMO_BACKEND_URL` | `https://aicmo-backend.onrender.com` | Backend API base URL |
| `AICMO_ENABLE_DANGEROUS_UI_OPS` | `0` | **MUST be 0 in production** |

---

## 10. Support Contacts

**Repository**: `/workspaces/AICMO`

**Key Files**:
- Worker: `scripts/run_aol_worker.py`
- Health CLI: `scripts/aol_health_cli.py`
- Backend: `backend/app.py`
- Streamlit: `streamlit_pages/aicmo_operator.py`

**Database Schema**:
- `aol_control_flags`: Pause/kill/proof mode flags
- `aol_tick_ledger`: Tick execution history
- `aol_lease`: Distributed lock
- `aol_actions`: Task queue
- `aol_execution_logs`: Detailed action logs

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-16  
**Deployment Topology**: Render (Backend + Worker) + Streamlit Cloud (UI)
