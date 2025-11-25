# Phase L Persistence – Quick Action Items

**All code changes complete.** Infrastructure setup is manual (by you, on Render/Streamlit Cloud).

---

## ✅ Code Commits (Done)

```
94ec7b7 - docs: Add comprehensive Phase L persistence guide with setup instructions
0d04c1a - fix: Add JSON date serialization & improve timeout handling with generation_mode tracking
```

### What was fixed:

1. **JSON serialization** ✅
   - Added `_json_default()` helper in `backend/llm_enhance.py` and `backend/learning_usage.py`
   - Prevents crashes on datetime fields: `Object of type date is not JSON serializable`

2. **Timeout handling** ✅
   - Changed from `timeout=60` to `timeout=(10, 120)` in Streamlit's `call_backend_generate()`
   - Better fallback behavior when backend is slow
   - Added `generation_mode` tracking for clearer UX (http-backend vs local-openai)

3. **WOW enforcement** ✅
   - Confirmed: Already enforced in `call_backend_generate()`
   - No changes needed – all service flags force-enabled

---

## 🔧 Manual Setup Required (For You)

### On Render Backend

In your Render service environment variables, add:

```
AICMO_MEMORY_DB = postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME
AICMO_FAKE_EMBEDDINGS = 0
```

Get the Postgres URL from your Neon project or create a new one at [neon.tech](https://neon.tech).

**Then:** Restart the Render service.

---

### On Streamlit Cloud

In your deployment secrets, add:

```
DB_URL = postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME
DATABASE_URL = postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME
```

Use the **same Postgres URL** as Render (or a different one if you prefer).

**Then:** Rerun the app (or redeploy).

---

## ✔️ Verify It Works

### Backend health check:

```bash
curl https://your-backend.onrender.com/api/learn/debug/summary
```

Should return something like:
```json
{
  "total_items": 5,
  "per_kind": {"full_report": 5}
}
```

### Streamlit (in app):

1. Go to **Learn** tab
2. Expand **Memory Database Stats**
3. Should show non-zero counts (if any learning was recorded)
4. Restart the app → counts should still be there

---

## 📋 Complete Checklist

| Task | Status | Owner | Done? |
|------|--------|-------|-------|
| Fix JSON serialization crash | ✅ Code change | Copilot | ✅ |
| Fix timeout (60→120s) | ✅ Code change | Copilot | ✅ |
| Add generation_mode tracking | ✅ Code change | Copilot | ✅ |
| Set AICMO_MEMORY_DB on Render | 🔄 Manual | You | ⏳ |
| Set AICMO_FAKE_EMBEDDINGS=0 on Render | 🔄 Manual | You | ⏳ |
| Restart Render service | 🔄 Manual | You | ⏳ |
| Set DB_URL on Streamlit Cloud | 🔄 Manual | You | ⏳ |
| Set DATABASE_URL on Streamlit Cloud | 🔄 Manual | You | ⏳ |
| Verify backend /api/learn/debug/summary | 🔄 Manual | You | ⏳ |
| Verify Streamlit Learn tab | 🔄 Manual | You | ⏳ |

---

## 🎯 What You Get After Setup

✅ **Learning persists** – Reports saved even after container restarts  
✅ **Real embeddings** – OpenAI embeddings (not fake)  
✅ **Reliable generation** – WOW reports complete within 120s timeout  
✅ **Better diagnostics** – See which backend path was used (HTTP vs OpenAI)  
✅ **No crashes** – Date serialization fixed in learning/LLM modules  

---

## 📖 Full Details

See `PHASE_L_PERSISTENCE_GUIDE.md` for:
- Architecture diagram
- Troubleshooting guide
- Technical deep-dive
- Testing procedures

---

**Time estimate for setup:** ~5 minutes (just environment variable changes + restarts)
