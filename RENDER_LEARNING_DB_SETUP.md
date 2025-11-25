# Render Backend: Enable Real Learning with Persistent Database

**Status:** Code complete. Awaiting environment variable configuration on Render.
**Commit:** `faac591`

---

## What's Needed

Your Render backend is currently logging:

```
aicmo.memory.engine | AICMO_MEMORY: Using fake embeddings (AICMO_FAKE_EMBEDDINGS=1).
aicmo.learn | Phase L: DB not found at /tmp/aicmo_memory.db (no learning yet)
```

This means:
- ❌ Learning DB is in `/tmp` (lost on container restart)
- ❌ Fake embeddings enabled (no real OpenAI embedding model calls)

**To fix:** Add two environment variables to your Render service.

---

## Step-by-Step Setup

### 1. Get Your Postgres Connection String

You need a Postgres URL. Options:

**Option A: Use existing Neon database**
- If you already have a Neon project for AICMO (e.g., `aicmo_prod`)
- Go to [neon.tech](https://neon.tech) → Dashboard → Your project
- Click "Connection string" → Copy the `postgresql://...` URL

**Option B: Create a new Neon project for learning**
- Go to [neon.tech](https://neon.tech) → Create new project
- Give it a name like `aicmo_memory` or `aicmo_learning`
- Once created, copy the connection string from "Connection" tab

**Example string:**
```
postgresql+psycopg2://user:password@ep-xyz.us-east-1.neon.tech:5432/aicmo_memory
```

### 2. Go to Render Dashboard

1. Open [render.com](https://render.com) → Your services
2. Click on your **AICMO backend service** (e.g., `aicmo-backend`)
3. Click **Environment** tab (left sidebar)

### 3. Add Environment Variables

In the **Environment** tab, add these two variables:

| Key | Value |
|-----|-------|
| `AICMO_MEMORY_DB` | Your Postgres URL from step 1 |
| `AICMO_FAKE_EMBEDDINGS` | `0` |

**Example:**
```
AICMO_MEMORY_DB = postgresql+psycopg2://user:password@ep-xyz.us-east-1.neon.tech:5432/aicmo_memory
AICMO_FAKE_EMBEDDINGS = 0
```

### 4. Restart the Service

After adding the variables:
1. Click the **... (menu)** button on your service
2. Select **Restart service** (or wait for auto-redeployment if you updated from GitHub)

### 5. Verify in Logs

Wait 30 seconds, then check the service logs:

**Before:**
```
[aicmo.memory.engine] Phase L: DB not found at /tmp/aicmo_memory.db (no learning yet)
```

**After:**
```
[aicmo.memory.engine] Phase L: Using Postgres memory engine at postgresql+psycopg2://...
```

If you see this, you're good! Learning is now persistent.

---

## What This Does

| Variable | Effect |
|----------|--------|
| `AICMO_MEMORY_DB` | Points the learning database from `/tmp` (ephemeral) to Neon (persistent) |
| `AICMO_FAKE_EMBEDDINGS=0` | Tells the system to use real OpenAI embeddings instead of fake ones |

**Result:**
- ✅ Every generated report is now learned and persisted to Neon
- ✅ Learning survives container restarts
- ✅ Real embeddings enable relevance-based learning retrieval
- ✅ Streamlit's Learn tab shows actual stored items (not fake)

---

## Troubleshooting

### Issue: "Cannot connect to database" error in logs

**Cause:** Connection string is wrong or DB is unreachable

**Fix:**
1. Copy the exact connection string again from Neon dashboard
2. Ensure it's in this format: `postgresql+psycopg2://...` (not just `postgresql://...`)
3. Check that Neon project hasn't been deleted
4. Restart the service

### Issue: "AICMO_MEMORY_DB" is not set – using default path

**Cause:** Environment variable not actually added to Render

**Fix:**
1. Go to Render dashboard → Service → Environment
2. Verify `AICMO_MEMORY_DB` appears in the list
3. If not, add it again
4. **Important:** Wait for service restart (might take 1-2 minutes)

### Issue: Logs still show fake embeddings

**Cause:** `AICMO_FAKE_EMBEDDINGS` is still `1` or not set to `0`

**Fix:**
1. Go to Render dashboard → Service → Environment
2. Find `AICMO_FAKE_EMBEDDINGS`
3. Set it to exactly `0` (not blank, not `false`)
4. Restart service

---

## Verification Checklist

After restarting:

- [ ] Logs show: `Phase L: Using Postgres memory engine at postgresql+psycopg2://...`
- [ ] Logs show: `AICMO_MEMORY: Using real embeddings` (or no message about fake embeddings)
- [ ] Generate a test report in Streamlit
- [ ] Backend logs show: `🔥 [LEARNING RECORDED] Report learned and stored in memory engine`
- [ ] Go to Streamlit → Learn tab → Memory Database Stats → See non-zero counts
- [ ] Restart Render service again
- [ ] Counts are still there (didn't reset to 0)

---

## Architecture After Setup

```
┌─────────────────────────────────────────────────────────┐
│ Streamlit App (streamlit_pages/aicmo_operator.py)      │
│ - call_backend_generate() sends payload to backend      │
│ - Falls back to OpenAI if backend times out            │
│ - generation_mode = "http-backend" or "direct-openai-fallback"
└──────────────────────┬──────────────────────────────────┘
                       │ (HTTP POST /api/aicmo/generate_report)
                       ↓
┌─────────────────────────────────────────────────────────┐
│ Render Backend (backend/main.py)                        │
│ - Receives payload via HTTP                             │
│ - Calls aicmo_generate() for main report                │
│ - Calls enhance_with_llm() for enhancement (optional)   │
│ - Calls record_learning_from_output() to store in DB    │
│   (learning_usage.py uses json_safe_dumps)              │
└──────────────────────┬──────────────────────────────────┘
                       │ (INSERT into aicmo_learn_items)
                       ↓
┌─────────────────────────────────────────────────────────┐
│ Neon Postgres (AICMO_MEMORY_DB)                         │
│ - aicmo_learn_items table stores all learned examples   │
│ - Persists across container restarts                    │
│ - Shared by backend and Streamlit Learn tab             │
└─────────────────────────────────────────────────────────┘
```

---

## Expected Behavior

### Scenario: Generate, restart, verify

1. **Streamlit:**
   - Enter brief → Click "Generate draft report"
   - `generation_mode` set to "http-backend"
   - Report appears with caption: ✅ Source: AICMO backend (WOW presets + learning...)

2. **Backend logs:**
   - `🔥 [LEARNING RECORDED] Report learned and stored in memory engine`

3. **Neon DB:**
   - New row in `aicmo_learn_items` table with the full report

4. **Restart Render:**
   - Service restarts → `/tmp` is wiped
   - Container loads `AICMO_MEMORY_DB` env var
   - Connects to Neon
   - Learning items are still there

5. **Streamlit Learn tab:**
   - Click "Memory Database Stats"
   - Shows: `Total memory items: 1` (the report from step 1)
   - Even after restart → still shows `1`

---

## What's New in This Version

**Part A: Robust Backend Calls**
- Timeout increased to `(10, 300)` – waits up to 5 minutes for backend
- Better error handling separates `ReadTimeout` from other failures
- Cleaner fallback to OpenAI without debug noise

**Part B: Clear Generation Mode**
- Every report shows where it came from
- `generation_mode` tracked in session state
- Final Output tab displays source clearly

**Part C: JSON-Safe Serialization**
- New utility `aicmo/utils/json_safe.py` for future use
- Handles dates, datetimes, Decimals in JSON
- Already used in `backend/learning_usage.py` and `backend/llm_enhance.py`
- Prevents "Object of type date is not JSON serializable" crashes

---

## Next Steps

1. **Right now:**
   - Copy your Neon connection string
   - Add `AICMO_MEMORY_DB` and `AICMO_FAKE_EMBEDDINGS=0` to Render Environment
   - Restart the service
   - Verify in logs and Streamlit

2. **After verification:**
   - Test generation with Streamlit
   - Restart Render again
   - Confirm learning persists

3. **Going forward:**
   - Every report is now learned automatically
   - Memory grows as more reports are generated
   - Future reports can reference past ones for relevance

---

## Quick Command Reference (if using Render CLI)

```bash
# Set environment variables via CLI (if you prefer):
render env set AICMO_MEMORY_DB "postgresql+psycopg2://user:pass@host/db"
render env set AICMO_FAKE_EMBEDDINGS "0"

# Restart service:
render service restart <service-id>

# View logs:
render service logs <service-id>
```

Check Render CLI docs if you need help: https://render.com/docs/cli

---

**Questions?** Check the logs for exact error messages. They usually indicate what's missing or misconfigured.
