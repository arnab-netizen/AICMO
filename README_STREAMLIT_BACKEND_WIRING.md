# AICMO Streamlit ↔ Backend Wiring - Complete Implementation Package

**Status**: ✅ Infrastructure Phase Complete | ⏳ Integration Phase Ready  
**Session Date**: 2025-12-17  
**Token Budget**: Optimized for implementation continuation

---

## Quick Start

### Phase 1: Infrastructure (✅ DONE)

Infrastructure files created and tested. All syntax valid, zero import errors.

```bash
cd /workspaces/AICMO

# 1. Verify infrastructure files exist
ls -lh backend/schemas_deliverables.py streamlit_backend_client.py tools/smoke_generate.py

# 2. Run syntax checks
python -m py_compile backend/schemas_deliverables.py streamlit_backend_client.py tools/smoke_generate.py

# 3. Start backend (in terminal 1)
export BACKEND_URL=http://localhost:8000
export OPENAI_API_KEY=sk-...  # Add your key
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 4. Run smoke test (in terminal 2)
python tools/smoke_generate.py

# 5. Check result
echo $?  # Should be 0
```

### Phase 2: Integration (⏳ READY)

Follow [OPERATOR_INTEGRATION_GUIDE.md](./OPERATOR_INTEGRATION_GUIDE.md) to:
1. Add imports to operator_v2.py
2. Update 9 runner functions
3. Implement draft-amend-approve-export in render_*_tab functions

Estimated time: 2-3 hours

---

## File Manifest

### Created Files (Phase 1)

#### 1. **backend/schemas_deliverables.py** (8.7 KB)
Canonical deliverable envelope schema for all generate responses.
- `DeliverablesEnvelope` - Main response container
- `Deliverable` - Individual deliverable with content_markdown (required)
- `ResponseMeta` - Metadata (timestamp, provider, model, cost, tokens, trace_id)
- `ResponseError` - Error details (type, message, trace_id)
- `validate_deliverables_envelope()` - Contract validator
- `create_success_envelope()`, `create_failed_envelope()` - Builders

**Key Rule**: If status=SUCCESS, deliverables must be non-empty and each must have non-empty content_markdown.

**Import**:
```python
from backend.schemas_deliverables import (
    DeliverablesEnvelope,
    validate_deliverables_envelope,
    create_success_envelope,
    create_failed_envelope,
)
```

---

#### 2. **streamlit_backend_client.py** (7.9 KB)
HTTP client for Streamlit to call backend with safe instrumentation.
- `get_backend_url()` - Reads BACKEND_URL or AICMO_BACKEND_URL env vars
- `backend_post_json(path, payload, timeout_s)` - HTTP POST with trace ID
- `validate_response(resp)` - Contract validation
- `BackendResponse` - Parsed response dataclass

**Features**:
- ✅ No secrets printed (env var names only)
- ✅ Trace ID for request correlation
- ✅ Safe error handling
- ✅ Contract validation before return

**Import**:
```python
from streamlit_backend_client import (
    get_backend_url,
    backend_post_json,
    validate_response,
)
```

**Usage**:
```python
response = backend_post_json("/api/v1/campaigns/generate", payload)
is_valid, error = validate_response(response)
if is_valid:
    for deliv in response.deliverables:
        print(deliv["title"], deliv["content_markdown"])
```

---

#### 3. **tools/smoke_generate.py** (7.2 KB)
Integration smoke test for end-to-end wiring verification.

**5 Tests**:
1. Backend URL configuration
2. Provider configuration (names only)
3. Endpoint availability (POST /api/v1/campaigns/generate)
4. Response envelope validation (contract check)
5. Response summary (deliverables count, content lengths)

**Exit Codes**:
- 0 = Success ✅
- 1 = Configuration error
- 2 = Endpoint error
- 3 = Contract validation error
- 4 = Unexpected error

**Run**:
```bash
python tools/smoke_generate.py
```

**Expected Output**:
```
================================================================================
✅ ALL TESTS PASSED
================================================================================
```

---

#### 4. **docs/STREAMLIT_BACKEND_WIRING_PROOF.md** (22 KB)
Complete documentation of end-to-end wiring.

**Sections**:
- Architecture diagram (HTTP flow)
- Environment variables (required + optional)
- Files involved (Streamlit, Backend, Testing)
- Deliverable envelope schema with contract rules
- Streamlit backend client usage examples
- Backend endpoint implementation template
- CreativeService ProviderChain integration (before/after)
- Streamlit runner example (before/after)
- Testing instructions
- Verification checklist
- Troubleshooting guide
- Production deployment checklist

---

#### 5. **IMPLEMENTATION_STATUS_SESSION.md** (This Session)
Session progress tracking and next steps.

---

#### 6. **OPERATOR_INTEGRATION_GUIDE.md** (Detailed Guide)
Step-by-step integration instructions for operator_v2.py.

**Contains**:
- Exact import statements to add
- Helper function to add
- Pattern for all 9 runners
- Specific examples for runners 1-3
- Draft-Amend-Approve-Export code for each tab
- Verification steps (5 total)
- Backend endpoints reference

---

### Documentation Files

1. **[STREAMLIT_BACKEND_WIRING_PROOF.md](docs/STREAMLIT_BACKEND_WIRING_PROOF.md)** - Complete wiring documentation
2. **[OPERATOR_INTEGRATION_GUIDE.md](OPERATOR_INTEGRATION_GUIDE.md)** - Step-by-step integration
3. **[IMPLEMENTATION_STATUS_SESSION.md](IMPLEMENTATION_STATUS_SESSION.md)** - Session status

---

## Architecture

```
┌─────────────────────────────────┐
│ STREAMLIT UI (operator_v2.py)  │
│                                │
│  [Tab] → Inputs → [Generate]   │
│           ↓                    │
│  backend_post_json()           │
│  (streamlit_backend_client)    │
│           ↓                    │
│   HTTP POST + X-Trace-ID       │
└──────────────────┬──────────────┘
                   │ HTTP
                   ↓
┌──────────────────────────────────┐
│ BACKEND FASTAPI (main.py)       │
│                                 │
│  POST /api/v1/campaigns/generate │
│         ↓                        │
│  Validate inputs               │
│  Call service (CreativeService) │
│  via ProviderChain             │
│         ↓                        │
│  Build deliverables[]          │
│  Return DeliverablesEnvelope   │
│         ↓                        │
│  JSON with: status, run_id,    │
│  meta (provider, model),       │
│  deliverables[], error         │
└──────────────────┬──────────────┘
                   │ JSON
                   ↓
┌──────────────────────────────────┐
│ STREAMLIT UI (operator_v2.py)   │
│                                 │
│  validate_response()            │
│  Store → session_state draft   │
│         ↓                        │
│  Render → Draft → Amend        │
│         → Approve → Export      │
│         ↓                        │
│  Download .md/.json            │
└──────────────────────────────────┘
```

---

## Environment Variables

**Required**:
```bash
export BACKEND_URL=http://localhost:8000
# OR
export AICMO_BACKEND_URL=http://localhost:8000

export OPENAI_API_KEY=sk-...
```

**Optional**:
```bash
export AICMO_DEV_STUBS=1  # Enable stubs for testing (default: OFF)
export AICMO_LLM_PRIMARY_PROVIDER=openai
export AICMO_LLM_FALLBACK_PROVIDERS=anthropic,groq
```

---

## Deliverable Contract

**All responses must match**:
```json
{
  "status": "SUCCESS|FAILED|PARTIAL",
  "run_id": "uuid-string",
  "module": "campaigns|...",
  "meta": {
    "timestamp": "2025-12-17T10:30:00",
    "provider": "openai|anthropic|groq",
    "model": "gpt-4o|claude-3-5-sonnet|...",
    "cost_usd": 0.05,
    "tokens_used": 1200,
    "warnings": [],
    "trace_id": "uuid-string"
  },
  "deliverables": [
    {
      "id": "unique-id",
      "kind": "campaign_brief|linkedin_post|email_copy|...",
      "title": "Deliverable Title",
      "content_markdown": "# Markdown content here (REQUIRED, never empty)",
      "platform": "linkedin|email|twitter|...",
      "hashtags": ["#tag1", "#tag2"],
      "assets": {
        "image_url": "optional",
        "image_base64": "optional"
      }
    }
  ],
  "raw": {},
  "error": null
}
```

**Enforcement Rules**:
1. ✅ If status=SUCCESS: deliverables must be non-empty
2. ✅ Each deliverable must have content_markdown with actual content
3. ✅ Manifest-only responses (IDs without content) NOT acceptable

---

## Integration Checklist

### Phase 1: Infrastructure ✅ COMPLETE
- [x] Create canonical schema (schemas_deliverables.py)
- [x] Create HTTP client (streamlit_backend_client.py)
- [x] Create smoke test (tools/smoke_generate.py)
- [x] Create documentation (STREAMLIT_BACKEND_WIRING_PROOF.md)
- [x] Syntax checks pass
- [x] No import errors

### Phase 2: Integration ⏳ READY
- [ ] Add imports to operator_v2.py
- [ ] Update 9 runner functions
- [ ] Add draft-amend-approve-export UI
- [ ] Verify syntax (py_compile)
- [ ] Run smoke test (exit code 0)
- [ ] Manual UI test (Generate → Draft → Amend → Approve → Export)
- [ ] Check backend endpoints return envelope format
- [ ] CreativeService routes via ProviderChain
- [ ] Feature flag (AICMO_DEV_STUBS=1) implemented
- [ ] All grep checks pass (no remaining stubs)

---

## How to Proceed

### Step 1: Review Infrastructure (5 min)
```bash
cd /workspaces/AICMO

# Review key files
head -50 backend/schemas_deliverables.py
head -50 streamlit_backend_client.py
head -50 tools/smoke_generate.py

# Verify imports are available
python -c "from backend.schemas_deliverables import DeliverablesEnvelope; print('✅ Imports work')"
python -c "from streamlit_backend_client import backend_post_json; print('✅ Imports work')"
```

### Step 2: Set Up Backend (10 min)
```bash
# Terminal 1
cd /workspaces/AICMO
export BACKEND_URL=http://localhost:8000
export OPENAI_API_KEY=sk-your-key
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Verify Smoke Test (5 min)
```bash
# Terminal 2
cd /workspaces/AICMO
python tools/smoke_generate.py

# Should show:
# ✅ ALL TESTS PASSED
# echo $?  → should be 0
```

### Step 4: Integrate operator_v2.py (2-3 hours)
Follow **[OPERATOR_INTEGRATION_GUIDE.md](./OPERATOR_INTEGRATION_GUIDE.md)**:
1. Add imports
2. Update runners (9 functions)
3. Add draft-amend-approve-export UI
4. Verify syntax
5. Run smoke test again

### Step 5: Manual UI Test (30 min)
```bash
# Terminal 3
cd /workspaces/AICMO
streamlit run operator_v2.py
```

**Expected Flow**:
1. Open http://localhost:8501
2. Select tab
3. Fill inputs
4. Click Generate
5. See deliverables in draft
6. Edit text
7. Approve
8. Export (.md/.json)

---

## Verification Commands

Run these in sequence to verify each phase:

```bash
# Phase 1: Infrastructure
cd /workspaces/AICMO
python -m py_compile backend/schemas_deliverables.py
python -m py_compile streamlit_backend_client.py
python -m py_compile tools/smoke_generate.py
echo "✅ Phase 1: All syntax checks pass"

# Phase 2: Integration (after updating operator_v2.py)
python -m py_compile operator_v2.py
echo "✅ Operator syntax valid"

# Phase 2: Grep checks (find remaining stubs)
grep -RIn "In production\|Stub:" operator_v2.py backend | wc -l
# Should be 0 or very small number

# Phase 2: Smoke test
python tools/smoke_generate.py
echo "Exit code: $?"
# Should be 0

# Phase 2: Manual UI
streamlit run operator_v2.py
# Generate → Draft → Amend → Approve → Export workflow
```

---

## Troubleshooting

### "BACKEND_URL not configured"
```bash
export BACKEND_URL=http://localhost:8000
```

### "Cannot connect to backend"
```bash
# Verify backend is running
curl http://localhost:8000/docs

# Or start backend:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### "Response validation failed"
```bash
# Check backend returns proper envelope:
curl -X POST http://localhost:8000/api/v1/campaigns/generate \
  -H "Content-Type: application/json" \
  -d '{"campaign_name":"test"}' | jq .

# Must have: status, run_id, meta, deliverables, error
```

### "content_markdown is empty"
```bash
# Backend must return content in deliverables:
{
  "deliverables": [{
    "content_markdown": "ACTUAL CONTENT HERE"  # Never empty
  }]
}
```

---

## Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| backend/schemas_deliverables.py | Canonical envelope schema | ✅ Created |
| streamlit_backend_client.py | HTTP client for Streamlit | ✅ Created |
| tools/smoke_generate.py | Integration smoke test | ✅ Created |
| docs/STREAMLIT_BACKEND_WIRING_PROOF.md | Complete documentation | ✅ Created |
| OPERATOR_INTEGRATION_GUIDE.md | Step-by-step integration | ✅ Created |
| operator_v2.py | Streamlit UI (TO UPDATE) | ⏳ Ready |
| backend/main.py | FastAPI app (VERIFY ENDPOINTS) | ⏳ Ready |
| backend/services/creative_service.py | LLM service (ROUTE VIA PROVIDERCHAIN) | ⏳ Ready |

---

## Success Criteria

**Infrastructure Phase** ✅:
- [x] All files created and syntax valid
- [x] Imports work without errors
- [x] Type hints present throughout
- [x] Safe logging (no secrets)

**Integration Phase** (Pending):
- [ ] operator_v2.py runners updated (9 functions)
- [ ] Draft-Amend-Approve-Export working
- [ ] Smoke test passes (exit code 0)
- [ ] UI generates real deliverables
- [ ] Export downloads working
- [ ] CreativeService via ProviderChain
- [ ] All stubs removed (or behind AICMO_DEV_STUBS=1)

---

## Support

For detailed information:
1. **Architecture**: See [STREAMLIT_BACKEND_WIRING_PROOF.md](docs/STREAMLIT_BACKEND_WIRING_PROOF.md)
2. **Integration Steps**: See [OPERATOR_INTEGRATION_GUIDE.md](./OPERATOR_INTEGRATION_GUIDE.md)
3. **Session Status**: See [IMPLEMENTATION_STATUS_SESSION.md](./IMPLEMENTATION_STATUS_SESSION.md)

---

**Status**: ✅ Infrastructure Phase Complete  
**Next Phase**: Integration (2-3 hours)  
**Ready to Proceed**: YES ✅
