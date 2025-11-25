# Phase L: Making Learning Persistent + Real

**Status:** Implementation complete (Code changes committed)
**Commit:** `0d04c1a`

---

## Overview

Phase L learning (memory/self-improvement) now works with **real, persistent databases** instead of temporary in-memory stores or `/tmp` paths. After each container restart, the learning database is preserved.

This guide covers:

1. **Backend (Render) configuration** – Point memory engine to real Postgres/Neon
2. **Streamlit Cloud configuration** – Enable Learn tab to read from persistent DB
3. **Code fixes** – JSON serialization for date handling
4. **Timeout improvements** – Better fallback behavior when backend is slow

---

## ✅ Code Changes (Already Committed)

### 1. JSON Date Serialization Fix

**Files modified:**
- `backend/llm_enhance.py`
- `backend/learning_usage.py`

**What was broken:**
```
[LLM Enhance] Error during enhancement: Object of type date is not JSON serializable
[Learning] Error recording output: Object of type date is not JSON serializable
```

**Fix applied:**
Added `_json_default()` helper function:
```python
import datetime as _dt

def _json_default(obj: Any) -> str:
    """JSON serialization fallback for non-standard types like datetime.date."""
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    return str(obj)
```

Patched all `json.dumps()` calls:
```python
# Before:
raw_text = json.dumps(output, indent=2)

# After:
raw_text = json.dumps(output, indent=2, default=_json_default)
```

**Impact:** Learning and LLM-enhance modules no longer crash on datetime fields.

---

### 2. Timeout & Generation Mode Tracking

**File modified:** `streamlit_pages/aicmo_operator.py`

**What changed:**

| Aspect | Before | After | Why |
|--------|--------|-------|-----|
| Timeout | `timeout=60` | `timeout=(10, 120)` | 60s too short for WOW reports; (10, 120) gives 10s to connect, 120s to read |
| Mode tracking | `aicmo_backend_mode` only | `generation_mode` added | More explicit UX tracking of which path was used |
| Error message | "Timed out..." | "Took too long... Using direct model fallback for this run" | Clearer user communication |

**Code example:**
```python
# HTTP backend call
resp = requests.post(
    base_url.rstrip("/") + "/api/aicmo/generate_report",
    json=payload,
    timeout=(10, 120),  # ← NEW: generous timeout for WOW generation
)
...
st.session_state["generation_mode"] = "http-backend"  # ← NEW tracking

# Fallback path
st.session_state["generation_mode"] = "local-openai"  # ← NEW tracking
```

**Impact:** 
- Backend slowness won't prematurely timeout
- Users see clearer "source" info (HTTP backend vs OpenAI fallback)
- Both paths are now equally valid and tracked

---

## 📋 Infrastructure Setup Required

### Step 1.1: Configure Render Backend

On **Render backend service settings**, add these environment variables:

```bash
# Use persistent Postgres/Neon for memory engine (NOT /tmp)
AICMO_MEMORY_DB="postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME"

# Make sure real embeddings are ON (not fake)
AICMO_FAKE_EMBEDDINGS="0"
```

**Where to get the Neon URL:**

If you already have a Neon database (e.g., for `aicmo_prod`), use that URL.

If not, create a small dedicated Neon project:
1. Go to [neon.tech](https://neon.tech)
2. Create a new project (or use existing)
3. Copy the **Postgres connection string** from the dashboard
4. Paste into Render environment as `AICMO_MEMORY_DB`

**Example URL:**
```
postgresql+psycopg2://neon_user:neon_password@ep-something.us-east-1.neon.tech:5432/aicmo_learning
```

**Verify:**
After setting the env var, restart the Render backend service. You should see this log on first start:

```
Phase L: Using Postgres memory engine for learning
```

Instead of:

```
Phase L: AICMO_MEMORY_DB=db/aicmo_memory.db – temporary directory may lose data on reboot
```

---

### Step 1.2: Configure Streamlit Cloud

On **Streamlit Cloud deployment secrets**, add:

```bash
# Point Learn tab to persistent database
DB_URL="postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME"
DATABASE_URL="postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME"
```

Use the **same Neon URL** as step 1.1 (or a different one if you prefer separate databases).

**Why both `DB_URL` and `DATABASE_URL`?**
The Streamlit app checks both environment variables for backward compatibility.

**Verify:**
1. Go to **Streamlit Cloud app** (e.g., `https://aicmo-operator.streamlit.app`)
2. Navigate to **Learn** tab
3. Expand **Memory Database Stats**
4. You should see non-zero counts (if learning items were recorded)
5. After app restart, counts should persist (not reset to 0)

---

## 🔍 Verification Checklist

### Backend (Render)

- [ ] **AICMO_MEMORY_DB** set to Postgres URL (not `/tmp`)
- [ ] **AICMO_FAKE_EMBEDDINGS** set to `"0"` (real embeddings)
- [ ] Render service restarted after env var changes
- [ ] Backend logs show: `Phase L: Using Postgres memory engine for learning`
- [ ] `/api/learn/debug/summary` returns non-zero `total_items` (if any learning stored)

**Quick test:**
```bash
curl https://your-backend.onrender.com/api/learn/debug/summary
```

Should return:
```json
{
  "total_items": 5,
  "per_kind": {
    "strategy_deck": 2,
    "full_report": 3
  }
}
```

### Streamlit (Streamlit Cloud)

- [ ] **DB_URL** and **DATABASE_URL** set to Postgres URL
- [ ] Streamlit app redeployed after secrets changed
- [ ] **Learn** tab → **Memory Database Stats** shows counts
- [ ] Wait 5 minutes, refresh the page → counts still there (persistence check)

---

## 🚨 Troubleshooting

### Issue: "Using fake embeddings (AICMO_FAKE_EMBEDDINGS=1)"

**Cause:** `AICMO_FAKE_EMBEDDINGS` is still set to `"1"` on Render

**Fix:**
1. Render service → Environment
2. Find `AICMO_FAKE_EMBEDDINGS`
3. Delete it or set to `"0"`
4. Restart service

---

### Issue: Learn tab shows 0 items after restart

**Cause:** `DB_URL` not set on Streamlit Cloud, or using wrong database

**Check:**
1. Streamlit Cloud dashboard → Secrets
2. Verify `DB_URL` and `DATABASE_URL` are set
3. Verify they point to the same Postgres as backend's `AICMO_MEMORY_DB`
4. Rerun the Streamlit app: `cmd+r` (Mac) or `ctrl+r` (Windows)

---

### Issue: Backend returns HTTP 500 on learn endpoints

**Cause:** Postgres connection string is wrong, or table doesn't exist

**Fix:**
1. Check the exact error in Render logs
2. Verify `AICMO_MEMORY_DB` URL is correct (test with `psql` command-line if possible)
3. Restart Render service to trigger table creation (idempotent)

---

## 📊 Expected Behavior After Setup

### Scenario: Generate a report, then restart backend

1. **Before setup (without persistent DB):**
   - Generate report → Learn records it (to `/tmp/aicmo_memory.db`)
   - Restart Render container
   - `/tmp` is wiped → learning is lost
   - Learn tab shows 0 items

2. **After setup (with Neon):**
   - Generate report → Learn records it (to Neon Postgres)
   - Restart Render container
   - Neon DB persists
   - Learn tab still shows the item
   - Backend's `/api/learn/debug/summary` still returns it

### WOW + Agency-Grade

- ✅ No changes needed – already enforced in `call_backend_generate()`
- ✅ `wow_enabled=True` and `wow_package_key="strategy_campaign_standard"` always set
- ✅ Backend maps to full 17-section report
- ✅ All services force-enabled: marketing_plan, campaign_blueprint, social_calendar, creatives, include_agency_grade

---

## 🔧 Technical Details

### Memory Engine Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Streamlit App (aicmo_operator.py)                           │
│ - Learn tab reads from DB_URL                               │
│ - Displays Memory Database Stats                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ (reads items)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Render Backend (backend/main.py)                            │
│ - /api/learn/debug/summary → queries Postgres               │
│ - /api/aicmo/generate_report → calls aicmo_generate()       │
│   ↓ (calls learning_record_learning_from_output())          │
│   └──→ Inserts into Postgres (AICMO_MEMORY_DB)              │
└──────────────────────┬──────────────────────────────────────┘
                       │ (writes items)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Neon Postgres Database (AICMO_MEMORY_DB)                    │
│ - Persists across container restarts                        │
│ - Shared by both backend and Streamlit                      │
└─────────────────────────────────────────────────────────────┘
```

### JSON Serialization Fix

**Why it matters:**

The learning system stores outputs as JSON. Some outputs include `datetime.date` objects (e.g., from metadata or scheduling info). Python's `json` module doesn't know how to serialize dates by default.

Before fix:
```python
json.dumps({"created": datetime.date(2025, 11, 25)})
# ❌ TypeError: Object of type date is not JSON serializable
```

After fix:
```python
json.dumps(
    {"created": datetime.date(2025, 11, 25)},
    default=_json_default
)
# ✅ {"created": "2025-11-25"}  # ISO format
```

---

## 📝 Summary

| Task | Status | Commit |
|------|--------|--------|
| 2️⃣ Fix JSON date serialization | ✅ Done | `0d04c1a` |
| 3️⃣ Verify WOW + agency-grade | ✅ Confirmed | (no code changes needed) |
| 4️⃣ Improve timeout handling | ✅ Done | `0d04c1a` |
| 1️⃣ Configure persistent memory DB | 🔄 Manual setup required | (see **Infrastructure Setup** above) |

**Next steps for you:**

1. **On Render backend service:**
   - Add `AICMO_MEMORY_DB` env var (Postgres URL)
   - Set `AICMO_FAKE_EMBEDDINGS=0`
   - Restart service

2. **On Streamlit Cloud:**
   - Add `DB_URL` and `DATABASE_URL` secrets (same Postgres URL)
   - Rerun the app

3. **Test:**
   - Generate a report in Streamlit
   - Check `/api/learn/debug/summary` on backend
   - Restart both services
   - Verify learning items persist

---

## 🎯 Benefits

After setup, Phase L delivers:

1. **Persistent learning** – Reports don't disappear after container restart
2. **Real embeddings** – Using OpenAI's actual embedding model (not fake)
3. **Shared memory** – Both backend and Streamlit read from same DB
4. **Reliable generation** – 120s timeout handles even large WOW reports
5. **Better diagnostics** – `generation_mode` tracking shows which path was used
6. **No date crashes** – JSON serialization handles all data types

---

**Questions?** Check the logs:

```bash
# Backend logs
curl https://your-backend.onrender.com/api/health

# Streamlit logs
# (visible in Streamlit Cloud dashboard)

# Direct memory query (if you have psql)
psql "postgresql+psycopg2://..." -c "SELECT COUNT(*) FROM learning_examples;"
```
