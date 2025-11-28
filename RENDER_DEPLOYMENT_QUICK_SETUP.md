# Render Deployment: AICMO Backend & Streamlit Configuration

## Quick Setup

### 1. Backend Service (aicmo-backend.onrender.com)

#### Environment Variables Required

```
OPENAI_API_KEY = sk-...your-key...
DATABASE_URL = postgresql://...
```

#### Verify Backend is Running

```bash
curl https://aicmo-backend.onrender.com/health
# Should return: {"status": "ok"}

curl https://aicmo-backend.onrender.com/docs
# Should return Swagger UI
```

### 2. Streamlit Service

#### Environment Variables Required

```
AICMO_BACKEND_URL = https://aicmo-backend.onrender.com
OPENAI_API_KEY = sk-...your-key...
```

#### Optional: `.streamlit/secrets.toml`

Already committed; Render will use environment variables instead.

### 3. Testing the Integration

#### Test 1: Backend Health Check
```bash
curl -s https://aicmo-backend.onrender.com/health | jq .
```

#### Test 2: Streamlit Can See Backend URL
In Streamlit app, click "Settings" (bottom left) → View deployed service logs

Should show no errors about missing AICMO_BACKEND_URL.

#### Test 3: Full Generation
1. Open Streamlit: https://aicmo-streamlit.onrender.com/
2. Fill in client brief
3. Click "Generate Full Report"
4. If backend fails, should see explicit error message
5. Check Render backend logs for detailed error

### Common Issues & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| ❌ Backend connection error: Connection refused | Backend not running or wrong URL | Check backend service status in Render |
| ❌ HTTP 502: LLM authentication error | Missing OPENAI_API_KEY on backend | Add OPENAI_API_KEY to backend environment |
| ❌ HTTP 429: Rate limited | Too many requests too fast | Wait 60 seconds, retry |
| ❌ HTTP 500: Unexpected error | Backend bug or data issue | Check backend logs in Render |
| ⚠️  AICMO_BACKEND_URL not configured | Missing environment variable | Add AICMO_BACKEND_URL to Streamlit environment |

### Render Dashboard: Setting Environment Variables

**For Backend Service:**
1. Go to https://dashboard.render.com → Backend service
2. Click "Settings" (gear icon)
3. Scroll to "Environment Variables"
4. Add or edit:
   - Key: `OPENAI_API_KEY`
   - Value: `sk-xxx...`
5. Click "Save"
6. Service will redeploy automatically

**For Streamlit Service:**
1. Go to https://dashboard.render.com → Streamlit service
2. Click "Settings" (gear icon)
3. Scroll to "Environment Variables"
4. Add:
   - Key: `AICMO_BACKEND_URL`
   - Value: `https://aicmo-backend.onrender.com`
5. Add (if not present):
   - Key: `OPENAI_API_KEY`
   - Value: `sk-xxx...`
6. Click "Save"
7. Service will redeploy automatically

### Monitoring Errors in Production

**Backend Logs:**
```bash
# In Render dashboard, click Backend service → Logs
# Look for:
# - "LLM authentication error" → Missing OPENAI_API_KEY
# - "LLM rate limit exceeded" → Hitting OpenAI rate limits
# - "LLM generation timed out" → Slow requests
# - Any "500 Internal Server Error" messages
```

**Streamlit Logs:**
```bash
# In Render dashboard, click Streamlit service → Logs
# Look for:
# - "Backend connection error" → Backend down
# - "HTTP 502" → Backend returned error
# - Any Python exceptions
```

### Deployment Checklist

- [ ] Backend deployed and health check passes
- [ ] Streamlit deployed and loads without errors
- [ ] OPENAI_API_KEY set on backend
- [ ] AICMO_BACKEND_URL set on Streamlit (value: backend URL)
- [ ] Test generation completes (or shows explicit error)
- [ ] Monitor logs for errors in first 24 hours

### After Deploying Streamlit Error Surfacing Patch

**What's New:**
- Streamlit no longer silently falls back to direct OpenAI
- All backend errors are displayed as explicit messages with HTTP status
- Operator sees exact error type (auth, rate limit, timeout, etc.)
- Backend errors logged with full context for debugging

**Testing After Deployment:**
1. Generate a report – should work if both services are running
2. Stop backend, try to generate – should see "Backend connection error"
3. Remove OPENAI_API_KEY, try to generate – should see "HTTP 502: LLM authentication error"
4. Monitor logs to confirm errors are surfaced properly

---

**Related Files:**
- Implementation guide: `STREAMLIT_ERROR_SURFACING_GUIDE.md`
- Backend code: `backend/main.py` line 3602+
- Streamlit code: `streamlit_pages/aicmo_operator.py` line 656-710
- LLM error handling: `backend/services/llm_client.py`
