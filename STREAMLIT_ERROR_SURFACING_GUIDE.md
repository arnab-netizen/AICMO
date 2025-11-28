# AICMO Backend Error Surfacing & Streamlit Integration Guide

**Date:** November 28, 2025  
**Status:** ✅ Implemented and Deployed  
**Commit:** `ffdefe6` pushed to `main`

---

## Summary

This patch implements **strict backend error surfacing** in the Streamlit operator, eliminating silent fallbacks that hide real production issues. When the backend fails, the operator now displays the exact HTTP status code and error response body instead of silently switching to direct OpenAI.

### Key Changes

1. **Removed auto-fallback to direct OpenAI** – If backend fails, it's now a hard error, not a hidden workaround
2. **Added explicit error messages** – HTTP status codes, response bodies, and JSON parsing errors all visible
3. **Streamlit secrets support** – `AICMO_BACKEND_URL` can be set via `.streamlit/secrets.toml` in addition to environment variables
4. **Backend error handling** – Already in place, converting LLM errors into readable JSON responses

---

## Architecture Overview

### Error Flow

```
Streamlit Operator (UI)
  ↓
  POST /api/aicmo/generate_report
  ↓
Backend Endpoint (FastAPI)
  ↓
  LLMClient.generate() (wrapped with error handlers)
  ↓
  OpenAI API
```

### Error Handling Layers

| Layer | Responsibility | Status |
|-------|----------------|--------|
| **Streamlit Frontend** | Display errors from backend; no fallbacks | ✅ Implemented (this patch) |
| **Backend Endpoint** | Catch all exceptions; return HTTPException with status code | ✅ Implemented |
| **LLMClient** | Handle OpenAI-specific errors; convert to HTTPException | ✅ Implemented |

---

## Configuration

### 1. Backend URL Configuration

The Streamlit operator supports **multiple configuration methods** (in priority order):

```python
# Priority 1: Streamlit secrets
AICMO_BACKEND_URL = st.secrets.get("AICMO_BACKEND_URL")

# Priority 2: Environment variable (AICMO_BACKEND_URL)
AICMO_BACKEND_URL = os.environ.get("AICMO_BACKEND_URL")

# Priority 3: Environment variable (BACKEND_URL)
AICMO_BACKEND_URL = os.environ.get("BACKEND_URL")

# Priority 4: Error – not configured
```

### 2. Setting Backend URL

#### **Local Development**

Add to `.streamlit/secrets.toml`:
```toml
AICMO_BACKEND_URL = "http://localhost:8000"
```

Or set environment variable:
```bash
export AICMO_BACKEND_URL="http://localhost:8000"
streamlit run streamlit_pages/aicmo_operator.py
```

#### **Render Deployment**

In Render environment variables:
```
AICMO_BACKEND_URL = https://aicmo-backend.onrender.com
```

Or in Render dashboard: Settings → Environment Variables → Add:
- Key: `AICMO_BACKEND_URL`
- Value: `https://aicmo-backend.onrender.com`

#### **Verification**

Check if Streamlit sees the URL:
```python
# In Python/Streamlit
import os
import streamlit as st

backend_url = (
    st.secrets.get("AICMO_BACKEND_URL")
    if hasattr(st, "secrets") and "AICMO_BACKEND_URL" in st.secrets
    else os.environ.get("AICMO_BACKEND_URL") or os.environ.get("BACKEND_URL") or ""
)

print(f"Backend URL: {backend_url}")
```

---

## Error Handling Details

### Streamlit Operator (`streamlit_pages/aicmo_operator.py`)

**Before (Old Code with Auto-Fallback):**
```python
try:
    resp = requests.post(...)
    resp.raise_for_status()
    data = resp.json()
    return data["report_markdown"]
except requests.exceptions.RequestException as e:
    st.warning(f"Backend HTTP error: {e}. Falling back to direct model.")
    # Silently calls direct OpenAI ← PROBLEM: User doesn't know backend failed
```

**After (New Code with Explicit Errors):**
```python
try:
    resp = requests.post(url, json=payload, timeout=(10, 300))
except requests.RequestException as e:
    st.error(f"❌ Backend connection error: {e}")
    st.error("Cannot reach backend. Check AICMO_BACKEND_URL and network.")
    return None

# Show exact HTTP error
if resp.status_code != 200:
    st.error(
        f"❌ Backend returned HTTP {resp.status_code}\n\n"
        f"**Raw response (first 2000 chars):**\n```\n{resp.text[:2000]}\n```"
    )
    return None

# Validate JSON structure
try:
    data = resp.json()
except Exception:
    st.error(
        f"❌ Backend returned non-JSON response.\n\n"
        f"**Raw body (first 1000 chars):**\n```\n{resp.text[:1000]}\n```"
    )
    return None

# Check for required fields
if isinstance(data, dict) and "report_markdown" in data:
    st.success("✅ Report generated using backend with Phase-L learning.")
    return data["report_markdown"]
else:
    st.error(f"❌ Missing 'report_markdown' key. Got: {list(data.keys())}")
    return None
```

### Backend LLM Client (`backend/services/llm_client.py`)

7 specific exception handlers, each converted to HTTPException:

```python
async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
    for attempt in range(3):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=25,
            )
            return response.content[0].text

        # 1. Authentication error
        except AuthenticationError as e:
            logger.error("LLM authentication error: %s", e)
            raise HTTPException(
                status_code=502, 
                detail="LLM authentication error – check OPENAI_API_KEY"
            )

        # 2. Rate limit error
        except RateLimitError as e:
            logger.warning("LLM rate limit exceeded: %s", e)
            raise HTTPException(
                status_code=429, 
                detail="LLM rate limit exceeded – please retry later"
            )

        # 3. API status error
        except APIStatusError as e:
            logger.error("LLM API status error: %s", e)
            raise HTTPException(
                status_code=502, 
                detail="LLM API error – please retry"
            )

        # 4. Connection error
        except APIConnectionError as e:
            logger.error("LLM connection error: %s", e)
            raise HTTPException(
                status_code=502, 
                detail="LLM connection error – please retry"
            )

        # 5. Timeout error (with retry)
        except asyncio.TimeoutError:
            if attempt == 2:
                logger.error("LLM generation timed out after 3 attempts")
                raise HTTPException(
                    status_code=504, 
                    detail="LLM generation timed out – please retry"
                )
            logger.warning("LLM timeout on attempt %d, retrying...", attempt + 1)
            await asyncio.sleep(1)

        # 6. Already-handled HTTPException
        except HTTPException:
            raise

        # 7. Generic exception
        except Exception as e:
            if attempt == 2:
                logger.exception("Unexpected LLM error after retries")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Unexpected LLM error: {type(e).__name__}"
                )
            logger.warning("Error on attempt %d: %s, retrying...", attempt + 1, e)
            await asyncio.sleep(1)
```

### Backend Endpoint (`backend/main.py` line 3602+)

```python
@app.post("/api/aicmo/generate_report")
async def api_aicmo_generate_report(payload: dict) -> dict:
    try:
        # ... 200+ lines of generation logic ...
        return {
            "report_markdown": report_markdown,
            "status": "success",
        }
    except HTTPException:
        # Already handled (from llm_client), just re-raise
        raise
    except Exception as e:
        logger.exception("Unhandled error in /api/aicmo/generate_report: %s", type(e).__name__)
        raise HTTPException(
            status_code=500, 
            detail=f"Report generation failed: {type(e).__name__}: {str(e)[:100]}"
        )
```

---

## Error Response Examples

### Scenario 1: Missing API Key

**Backend generates:**
```json
{
  "detail": "LLM authentication error – check OPENAI_API_KEY"
}
```

**Streamlit shows:**
```
❌ Backend returned HTTP 502 for /api/aicmo/generate_report

**Raw response (first 2000 chars):**
```
{"detail": "LLM authentication error – check OPENAI_API_KEY"}
```
```

**Action:** Add `OPENAI_API_KEY` to backend environment on Render.

---

### Scenario 2: Rate Limited

**Backend generates:**
```json
{
  "detail": "LLM rate limit exceeded – please retry later"
}
```

**Streamlit shows:**
```
❌ Backend returned HTTP 429 for /api/aicmo/generate_report

**Raw response:**
{"detail": "LLM rate limit exceeded – please retry later"}
```

**Action:** Wait a few minutes before retrying.

---

### Scenario 3: Validation Error in Payload

**Backend generates:**
```json
{
  "detail": "Report generation failed: KeyError: 'package_name'"
}
```

**Streamlit shows:**
```
❌ Backend returned HTTP 500 for /api/aicmo/generate_report

**Raw response:**
{"detail": "Report generation failed: KeyError: 'package_name'"}
```

**Action:** Check payload structure; missing required field.

---

### Scenario 4: Connection Timeout

**Streamlit detects:**
```
❌ Backend connection error: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))

Cannot reach backend. Check AICMO_BACKEND_URL and network.
```

**Action:** Verify backend is running and `AICMO_BACKEND_URL` is correct.

---

## Testing the Integration

### Local Testing (Development)

1. **Start backend:**
   ```bash
   cd /workspaces/AICMO
   python -m backend.main
   ```
   Backend runs on `http://localhost:8000`

2. **Set environment:**
   ```bash
   export AICMO_BACKEND_URL="http://localhost:8000"
   export OPENAI_API_KEY="sk-..."
   ```

3. **Start Streamlit:**
   ```bash
   streamlit run streamlit_pages/aicmo_operator.py
   ```

4. **Test a generation:**
   - Fill in client brief
   - Click "Generate Full Report"
   - If backend is running and has API key, should see report
   - If backend is down or API key missing, see explicit error

### Testing Error Scenarios

**Test 1: Missing Backend URL**
```python
# In Python terminal
import os
os.environ.pop("AICMO_BACKEND_URL", None)
os.environ.pop("BACKEND_URL", None)
# Reload Streamlit – should show error
```

**Test 2: Backend Down**
```bash
# Stop the backend, try to generate in Streamlit
# Should see: "❌ Backend connection error: [connection refused]"
```

**Test 3: Missing API Key**
```bash
# Backend running but OPENAI_API_KEY not set
# Try to generate in Streamlit
# Should see: "❌ Backend returned HTTP 502... LLM authentication error"
```

---

## Render Deployment Checklist

- [ ] Backend deployed on Render (e.g., `https://aicmo-backend.onrender.com`)
- [ ] `OPENAI_API_KEY` set in backend environment variables
- [ ] `AICMO_BACKEND_URL` set in Streamlit app environment (value: backend URL)
- [ ] Test generation in Streamlit UI
- [ ] Verify errors are displayed (not hidden) if backend fails

---

## Code Locations

| File | Lines | Purpose |
|------|-------|---------|
| `streamlit_pages/aicmo_operator.py` | 656–710 | Strict error reporting, no fallback |
| `backend/services/llm_client.py` | 1–95 | 7 exception handlers, HTTPException conversion |
| `backend/main.py` | 3602–3838 | Endpoint wrapper, generic exception handler |
| `.streamlit/secrets.toml` | — | Backend URL configuration (dev) |

---

## Summary of Improvements

### Before This Patch ❌
- Backend HTTP error → Silently fallback to direct OpenAI
- Streamlit shows "Falling back to direct model" (no details)
- Operator can't tell if backend is down, auth failed, or other issue
- Production bugs hidden from operator view
- No error diagnostics in UI

### After This Patch ✅
- Backend HTTP error → Show exact status code and response body
- Streamlit displays full error message with actionable next steps
- Operator sees: "HTTP 502: LLM authentication error – check OPENAI_API_KEY"
- All errors logged on backend for debugging
- Clear JSON responses for all failure modes

---

## Next Steps

1. **Deploy to Render:**
   - Backend: Ensure `OPENAI_API_KEY` is set
   - Streamlit: Set `AICMO_BACKEND_URL` to backend URL

2. **Monitor errors:**
   - Check Render logs for error patterns
   - Use Streamlit error messages to guide fixes
   - Report detailed errors instead of "generation failed"

3. **Optional enhancements:**
   - Add retry logic with exponential backoff in Streamlit
   - Add telemetry/metrics for error rates
   - Create runbook for common errors

---

**Commit ID:** `ffdefe6`  
**Files Changed:** 2 (streamlit_pages/aicmo_operator.py, .streamlit/secrets.toml)  
**Insertions:** 54  
**Deletions:** 62  
**Status:** ✅ All hooks passed, deployed to main
