# Production LLM Launch Checklist 🚀

**Document Version:** 1.0  
**Last Updated:** December 6, 2025  
**Status:** Ready for Render + Streamlit Cloud Deployment  

---

## 📋 Overview

This checklist ensures AICMO is properly configured for production deployment with **real LLM usage** (no stubs) and **quality enforcement** for all generated content.

### Key Guarantees
- ✅ **No stub content** when LLM keys are configured
- ✅ **Quality checks enforced** for all shipped packs
- ✅ **LLM fallback chain** (OpenAI → Perplexity → structured error)
- ✅ **Live verification tools** to prove real LLM usage
- ✅ **Error transparency** with actionable diagnostics

---

## 🔐 Required Environment Variables

### Production Deployments (Render + Streamlit Cloud)

#### **REQUIRED** - LLM Provider Keys

At least **one** of the following must be set:

```bash
# Primary LLM Provider (recommended)
OPENAI_API_KEY=sk-proj-...

# Fallback Provider (recommended for redundancy)
PERPLEXITY_API_KEY=pplx-...

# Alternative Provider (optional)
ANTHROPIC_API_KEY=sk-ant-...
```

#### **REQUIRED** - Stub Control

```bash
# CRITICAL: Must be empty or "false" in production
# This is auto-enforced when LLM keys exist
AICMO_ALLOW_STUBS=false
```

#### **OPTIONAL** - Admin Features

```bash
# For admin panels in Streamlit (smoke tests, live checks)
AICMO_ADMIN_KEY=your-secure-admin-password

# If not set, default password "admin123" is used (change in production!)
```

#### **OPTIONAL** - Feature Flags

```bash
# Cache control (default: enabled)
AICMO_CACHE_ENABLED=true

# HTTP learning (default: disabled)
AICMO_ENABLE_HTTP_LEARNING=0

# LLM usage (default: auto-enabled when keys exist)
AICMO_USE_LLM=1
```

---

## 🔍 Pre-Deployment Verification

### Step 1: Local Test Suite

Run the full test suite locally **without** LLM keys (tests should skip gracefully):

```bash
# Core stub protection tests (4 tests)
pytest -q backend/tests/test_no_stub_in_production_config.py --tb=short

# LLM health check endpoint tests (5 tests)
pytest -q backend/tests/test_llm_healthcheck.py --tb=short

# Response schema tests
pytest -q backend/tests/test_api_endpoint_integration.py::test_standardized_response_schema --tb=short

# Quality gate simulation (10 tests - will skip without keys)
pytest -q backend/tests/test_all_packs_simulation.py::test_pack_meets_benchmark -v
```

**Expected Results:**
- All tests should pass or skip gracefully
- No test failures
- Warnings about missing LLM keys are expected locally

### Step 2: Set Production Keys Locally

For **optional** local verification with real LLMs:

```bash
# Export production keys (DO NOT commit these!)
export OPENAI_API_KEY=sk-proj-...
export PERPLEXITY_API_KEY=pplx-...

# Verify keys are detected
python -c "from backend.utils.config import is_production_llm_ready; print('LLM Ready:', is_production_llm_ready())"
# Expected: LLM Ready: True
```

### Step 3: Run Live LLM Verification

With production keys set, test real LLM generation:

```bash
# Run live verification CLI (exits 0 if all pass)
python scripts/check_llm_live.py

# Expected output:
# ✅ All tests PASSED
# - stub_used: False
# - quality_passed: True
# Exit code: 0
```

### Step 4: Test Health Check Endpoint

Start backend locally and test the health endpoint:

```bash
# Start backend (if not already running)
# python backend/main.py

# Test health check
curl http://localhost:8000/health/llm | python -m json.tool

# Expected response:
# {
#   "ok": true,
#   "llm_ready": true,
#   "used_stub": false,
#   "quality_passed": true,
#   "pack_key": "quick_social_basic",
#   "debug_hint": "Health check completed successfully"
# }
```

---

## 🚀 Deployment Steps

### Render (Backend API)

1. **Set Environment Variables** in Render Dashboard:
   ```
   OPENAI_API_KEY = sk-proj-...
   PERPLEXITY_API_KEY = pplx-...
   AICMO_ALLOW_STUBS = false
   AICMO_ADMIN_KEY = <secure-password>
   ```

2. **Deploy** and wait for build to complete

3. **Verify Health Check:**
   ```bash
   curl https://your-render-app.onrender.com/health/llm | python -m json.tool
   
   # Expected:
   # - ok: true
   # - llm_ready: true
   # - used_stub: false
   ```

4. **Monitor Logs** for first request:
   ```
   Look for: AICMO_RUNTIME | stub_used=False | quality_passed=True
   AVOID: error=stub_in_production_forbidden
   ```

### Streamlit Cloud (Frontend UI)

1. **Set Secrets** in Streamlit Cloud Settings:
   ```toml
   # .streamlit/secrets.toml or Cloud UI
   OPENAI_API_KEY = "sk-proj-..."
   PERPLEXITY_API_KEY = "pplx-..."
   AICMO_ALLOW_STUBS = "false"
   AICMO_ADMIN_KEY = "<secure-password>"
   ```

2. **Deploy** and wait for app to restart

3. **Check Sidebar:**
   - Should show: **"LLM Mode: PRODUCTION"**
   - Should show: ✅ Real LLM keys configured (no stubs)

4. **Test "Check LLM Health" Button:**
   - Click button in sidebar (only visible in production mode)
   - Expected:
     - ✅ Overall: HEALTHY
     - LLM Ready: True
     - Used Stub: False
     - Quality Passed: True

5. **Test Admin Panels** (Settings page):
   - **"Run Live LLM Check"** button:
     - Should complete in ~30-60 seconds
     - Should show: ✅ All live LLM tests PASSED
   - **"Run Full Smoke Test"** button:
     - Requires admin password
     - Tests all 10+ packs end-to-end
     - Should complete in ~3-5 minutes

---

## ✅ Acceptance Criteria

### Critical Requirements

Before marking production deployment as **complete**, verify all of the following:

#### 1. **No Stub Content in Production** ✅
```bash
# Test any pack via API
curl -X POST https://your-render-app.onrender.com/api/aicmo/generate_report \
  -H "Content-Type: application/json" \
  -d '{
    "pack_key": "quick_social_basic",
    "client_brief": {
      "brand_name": "Test Brand",
      "industry": "Test",
      "primary_goal": "Test",
      "product_service": "Test",
      "target_audience": "Test"
    },
    "stage": "strategy",
    "services": {"social_content": true}
  }' | jq '.stub_used'

# Expected: false
# NEVER: true
```

#### 2. **Quality Checks Enforce Benchmarks** ✅
```bash
# Same request as above, check quality_passed
curl ... | jq '.quality_passed'

# Expected: true (for packs with quality gates)
# If false, check error_type for runtime_quality_failed
```

#### 3. **Health Endpoint Operational** ✅
```bash
curl https://your-render-app.onrender.com/health/llm | jq '.ok'

# Expected: true
# If false, check error_type and debug_hint
```

#### 4. **Streamlit UI Shows Production Mode** ✅
- Open Streamlit app
- Check sidebar
- Must show: **"LLM Mode: PRODUCTION"**
- Must show: ✅ Real LLM keys configured (no stubs)

#### 5. **Live Verification Tools Work** ✅
- In Streamlit Settings page:
- Click **"Run Live LLM Check"**
- Expected: ✅ All live LLM tests PASSED
- Exit code: 0

#### 6. **Error Handling is Transparent** ✅
- If LLM providers are down, system should:
  - Return `error_type: "llm_chain_failed"`
  - Include `debug_hint` with provider info
  - NEVER return stub content
  - Log: `AICMO_RUNTIME | error=llm_chain_failed`

---

## 🔧 Troubleshooting

### Issue: Health check returns `ok: false`

**Diagnosis:**
```bash
curl https://your-app.onrender.com/health/llm | jq '.error_type, .debug_hint'
```

**Common Causes:**
- `llm_ready: false` → LLM keys not configured or invalid
- `used_stub: true` → Stub content generated (CRITICAL - should never happen in prod)
- `error_type: "llm_chain_failed"` → All LLM providers exhausted (check provider status)

**Resolution:**
1. Verify environment variables are set correctly
2. Check LLM provider API status (OpenAI, Perplexity)
3. Review backend logs for detailed error messages
4. Test with `python scripts/check_llm_live.py` for detailed diagnostics

### Issue: Streamlit shows "LLM Mode: DEV/LOCAL"

**Diagnosis:**
- Secrets not configured in Streamlit Cloud
- Or secrets not yet propagated after deployment

**Resolution:**
1. Open Streamlit Cloud → App Settings → Secrets
2. Verify `OPENAI_API_KEY` and/or `PERPLEXITY_API_KEY` are set
3. Click "Save" and wait for app to restart (~30 seconds)
4. Refresh browser

### Issue: Generation returns `stub_used: true` in production

**Diagnosis:**
This is a **CRITICAL ERROR** - stub content should NEVER reach production.

**Resolution:**
1. Check backend logs for: `error=stub_in_production_forbidden`
2. Verify `AICMO_ALLOW_STUBS` is set to `"false"` or not set at all
3. Confirm LLM keys are valid and not expired
4. Test health endpoint: `curl https://your-app/health/llm`
5. If issue persists, check backend/main.py:8732-8750 for final guard logic

### Issue: Quality checks fail (`runtime_quality_failed`)

**Diagnosis:**
Generated content doesn't meet benchmark criteria.

**Resolution:**
1. Check error response for `quality_issues` field
2. Review:
   - `missing_terms`: Required terms not found in content
   - `forbidden_terms`: Forbidden terms present in content
   - `brand_mentions`: Brand name mentioned too few times
3. This is **expected behavior** - quality enforcement working correctly
4. If persistent, review pack definition in `backend/main.py` PACK_SECTION_WHITELIST

### Issue: Live LLM check fails (exit code 1)

**Diagnosis:**
```bash
python scripts/check_llm_live.py 2>&1 | tail -20
```

**Common Causes:**
- No LLM keys configured (expected in dev)
- LLM provider API errors (check provider status)
- Network connectivity issues

**Resolution:**
1. Verify LLM keys are set and valid
2. Check OpenAI/Perplexity API status pages
3. Review detailed error output from script
4. Test individual endpoint: `curl https://your-app/api/aicmo/generate_report ...`

---

## 📊 Monitoring & Observability

### Key Metrics to Track

#### Backend Logs (Render)
Search for these patterns:

```bash
# Success metrics
"AICMO_RUNTIME | stub_used=False | quality_passed=True"
"✅ [HTTP ENDPOINT] generate_report successful"

# Error metrics
"error=stub_in_production_forbidden"  # CRITICAL - should NEVER appear
"error=llm_chain_failed"              # LLM providers unavailable
"error=runtime_quality_failed"        # Quality benchmark not met
"LLM_FALLBACK | provider=perplexity"  # Fallback chain activated
```

#### Streamlit Logs (Streamlit Cloud)
Monitor for:

```bash
# User activity
"🔄 Generating report..."
"✅ LLM Status: REAL"

# Errors
"❌ LLM Status: STUB"  # CRITICAL - investigate immediately
"⚠️ Quality Check Failed"
```

### Recommended Alerts

Set up alerts for these conditions:

1. **CRITICAL: Stub in Production**
   - Pattern: `error=stub_in_production_forbidden`
   - Action: Page on-call engineer immediately
   - SLA: Investigate within 5 minutes

2. **HIGH: LLM Chain Failed**
   - Pattern: `error=llm_chain_failed`
   - Action: Check LLM provider status
   - SLA: Investigate within 15 minutes

3. **MEDIUM: Quality Gate Failures Spike**
   - Pattern: `error=runtime_quality_failed`
   - Threshold: >20% of requests
   - Action: Review pack definitions and benchmarks

4. **INFO: Perplexity Fallback Activated**
   - Pattern: `LLM_FALLBACK | provider=perplexity`
   - Action: Monitor OpenAI availability
   - Note: Expected behavior, not an error

---

## 🧪 Continuous Verification

### Daily Health Checks

Automate these checks in CI/CD or monitoring:

```bash
#!/bin/bash
# health_check.sh

# 1. Check backend health
HEALTH=$(curl -s https://your-app.onrender.com/health/llm | jq '.ok')
if [ "$HEALTH" != "true" ]; then
  echo "❌ Backend health check failed"
  exit 1
fi

# 2. Test quick social pack
RESPONSE=$(curl -s -X POST https://your-app/api/aicmo/generate_report \
  -H "Content-Type: application/json" \
  -d '{"pack_key":"quick_social_basic","client_brief":{"brand_name":"Health Check","industry":"Test","primary_goal":"Test","product_service":"Test","target_audience":"Test"},"stage":"strategy","services":{"social_content":true}}')

STUB_USED=$(echo $RESPONSE | jq '.stub_used')
if [ "$STUB_USED" = "true" ]; then
  echo "❌ Stub content detected in production!"
  exit 1
fi

QUALITY=$(echo $RESPONSE | jq '.quality_passed')
if [ "$QUALITY" = "false" ]; then
  echo "⚠️  Quality check failed"
  # Log but don't fail - may be expected
fi

echo "✅ All health checks passed"
```

### Weekly Deep Tests

Run full test suite in production-like environment:

```bash
# 1. Run all pack simulations
pytest -q backend/tests/test_all_packs_simulation.py::test_pack_meets_benchmark -v

# 2. Run live LLM verification
python scripts/check_llm_live.py

# 3. Run smoke tests for all packs
python scripts/smoke_run_all_packs.py
```

---

## 🌙 Nightly Regression Testing

### Automated CI/CD Pipeline

AICMO includes a **GitHub Actions workflow** that runs comprehensive LLM regression tests every night at **01:00 IST (19:30 UTC)**.

**Workflow File:** `.github/workflows/nightly_llm_regression.yml`

### What It Tests

1. **Pack Benchmark Simulation** (10+ packs)
   ```bash
   pytest -q backend/tests/test_all_packs_simulation.py::test_pack_meets_benchmark -v
   ```
   - Tests all production packs with real LLM calls
   - Enforces quality benchmarks
   - Verifies no stub content (`stub_used=false`)
   - Validates brand mentions, word counts, required terms

2. **Live LLM Verification**
   ```bash
   python scripts/check_llm_live.py
   ```
   - End-to-end generation with realistic briefs
   - Confirms `stub_used=false` and `quality_passed=true`
   - Tests OpenAI → Perplexity fallback chain
   - Exit code 0 only if all tests pass

### Configuration

The workflow uses **GitHub repository secrets**:

```yaml
secrets:
  OPENAI_API_KEY: sk-proj-...
  PERPLEXITY_API_KEY: pplx-...
```

Environment is configured for strict production mode:

```yaml
AICMO_ALLOW_STUBS=false      # No stub fallback
AICMO_CACHE_ENABLED=false    # Fresh generation each time
```

### How to Set Up

1. **Add secrets** to GitHub repository:
   - Go to: `Settings → Secrets and variables → Actions`
   - Add: `OPENAI_API_KEY` (value: `sk-proj-...`)
   - Add: `PERPLEXITY_API_KEY` (value: `pplx-...`)

2. **Workflow runs automatically** every night at 01:00 IST

3. **Manual trigger** also available:
   - Go to: `Actions → Nightly LLM Regression Tests`
   - Click: `Run workflow`

### Monitoring Results

#### ✅ Success Path

When all tests pass:
- Workflow shows green checkmark ✅
- Artifacts uploaded: `llm-regression-success-{run_number}`
- Contains: `pytest-output.txt`, `llm-live-check.txt`
- Artifacts retained for 7 days

#### ❌ Failure Path

When tests fail:
- Workflow shows red X ❌
- **GitHub Issue automatically created** with:
  - Title: `🚨 Nightly LLM Regression Failed - YYYY-MM-DD`
  - Labels: `regression`, `llm`, `ci`
  - Details: Exit codes, workflow run link, troubleshooting steps
- Artifacts uploaded: `llm-regression-failure-{run_number}`
- Contains:
  - `pytest-output.txt` (detailed test results)
  - `pytest-results.xml` (JUnit format)
  - `llm-live-check.txt` (live verification output)
  - `reports/ALL_PACKS_GOLDEN_SIMULATION_LATEST.md` (if present)
- Artifacts retained for 30 days

### Where to Check

**GitHub Actions Tab:**
1. Go to: `https://github.com/arnab-netizen/AICMO/actions`
2. Click: `Nightly LLM Regression Tests`
3. View recent runs and their status

**Issues Tab (on failure):**
1. Go to: `https://github.com/arnab-netizen/AICMO/issues`
2. Filter by labels: `regression`, `llm`
3. Review automatically created failure reports

### Interpreting Results

#### Common Failure Scenarios

**Scenario 1: LLM Provider Outage**
```
Error: llm_chain_failed
Cause: All providers (OpenAI, Perplexity) unavailable
Action: Check provider status pages, wait for service restoration
```

**Scenario 2: Quality Benchmark Regression**
```
Error: runtime_quality_failed
Cause: Generated content doesn't meet quality criteria
Action: Review failing pack, check for model behavior changes
```

**Scenario 3: Stub Content Detected**
```
Error: stub_in_production_forbidden
Cause: System tried to generate stub despite LLM keys
Action: CRITICAL - investigate immediately, check LLM integration
```

**Scenario 4: API Rate Limiting**
```
Error: 429 Too Many Requests
Cause: Exceeded LLM provider rate limits
Action: Review rate limits, consider spreading tests across time
```

### Response Procedures

**For Critical Failures** (`stub_in_production_forbidden`):
1. ⏱️ Respond within 5 minutes
2. Check workflow artifacts for detailed logs
3. Verify LLM keys are valid and not expired
4. Test locally: `python scripts/check_llm_live.py`
5. Review backend/main.py:8732-8750 (final guard logic)

**For Provider Outages** (`llm_chain_failed`):
1. ⏱️ Respond within 15 minutes
2. Check provider status pages:
   - OpenAI: https://status.openai.com/
   - Perplexity: https://status.perplexity.ai/
3. If outage confirmed, add comment to GitHub issue
4. Re-run workflow manually after service restoration

**For Quality Regressions** (`runtime_quality_failed`):
1. ⏱️ Respond within 1 hour
2. Download artifacts and review `pytest-output.txt`
3. Identify which pack(s) failed
4. Check for:
   - Missing required terms
   - Forbidden terms present
   - Insufficient brand mentions
   - Content length below threshold
5. Run failing pack locally to reproduce
6. Adjust benchmarks if model behavior changed legitimately

### Local Debugging

To reproduce nightly regression failures locally:

```bash
# 1. Set environment (use production keys)
export OPENAI_API_KEY=sk-proj-...
export PERPLEXITY_API_KEY=pplx-...
export AICMO_ALLOW_STUBS=false
export AICMO_CACHE_ENABLED=false

# 2. Run exact same tests
pytest -q backend/tests/test_all_packs_simulation.py::test_pack_meets_benchmark -v
python scripts/check_llm_live.py

# 3. Review output
# Compare with artifacts from failed workflow run
```

### Performance Metrics

**Typical Runtime:**
- Pack benchmark tests: ~3-5 minutes (10 packs)
- Live LLM verification: ~30-60 seconds (2 packs)
- Total workflow: ~5-7 minutes

**Cost Estimation:**
- OpenAI API calls: ~$0.10-0.50 per night
- GitHub Actions minutes: Free tier (2000 min/month)

### Maintenance

**Monthly Tasks:**
- Review artifact storage usage (30-day retention on failures)
- Archive or close resolved regression issues
- Update LLM provider API keys if rotated

**Quarterly Tasks:**
- Review workflow performance and adjust pack selection
- Update quality benchmarks if model behavior changes
- Audit LLM provider costs and rate limits

---

## 📖 Reference

### Key Files

| File | Purpose |
|------|---------|
| `backend/main.py:8732-8750` | Final guard preventing stubs in production |
| `backend/main.py:397-476` | `/health/llm` endpoint implementation |
| `backend/utils/config.py` | `is_production_llm_ready()`, `allow_stubs_in_current_env()` |
| `backend/response_schema.py` | Standardized response format with error types |
| `backend/quality_runtime.py` | Runtime quality enforcement for all packs |
| `backend/client/aicmo_api_client.py` | Thin client for Streamlit/CLI |
| `scripts/check_llm_live.py` | Live LLM verification CLI tool |
| `streamlit_app.py:422-451` | Sidebar LLM health check button |
| `streamlit_app.py:1083-1122` | Admin live LLM verification panel |

### Error Types Reference

| Error Type | Cause | Resolution |
|-----------|-------|------------|
| `stub_in_production_forbidden` | Stub generated with prod keys (CRITICAL) | Check LLM provider status, verify keys |
| `llm_chain_failed` | All providers exhausted | Wait/retry, check provider status |
| `llm_failure` | Single provider failed | System auto-fallbacks, retry if persists |
| `runtime_quality_failed` | Content failed benchmarks | Review missing/forbidden terms |
| `llm_unavailable` | No providers configured | Set environment variables |
| `unexpected_error` | System error | Review logs, report to engineering |

### Test Commands Quick Reference

```bash
# Unit tests
pytest -q backend/tests/test_no_stub_in_production_config.py --tb=short
pytest -q backend/tests/test_llm_healthcheck.py --tb=short

# Integration tests
pytest -q backend/tests/test_api_endpoint_integration.py --tb=short

# Live verification
python scripts/check_llm_live.py

# Smoke tests (requires LLM keys)
python scripts/smoke_run_all_packs.py

# Health check
curl https://your-app/health/llm | python -m json.tool
```

---

## ✅ Deployment Completion Checklist

- [ ] Environment variables set in Render (OPENAI_API_KEY, PERPLEXITY_API_KEY)
- [ ] Environment variables set in Streamlit Cloud (same as above)
- [ ] `AICMO_ALLOW_STUBS` set to `"false"` or not set (auto-enforced)
- [ ] Backend `/health/llm` returns `ok: true`
- [ ] Streamlit sidebar shows "LLM Mode: PRODUCTION"
- [ ] Streamlit "Check LLM Health" button works
- [ ] Sample generation request returns `stub_used: false`
- [ ] Sample generation request returns `quality_passed: true` (for packs with gates)
- [ ] Admin "Run Live LLM Check" button passes all tests
- [ ] Backend logs show: `AICMO_RUNTIME | stub_used=False`
- [ ] No logs showing: `error=stub_in_production_forbidden`
- [ ] Monitoring/alerts configured for critical errors
- [ ] Team trained on troubleshooting procedures

---

## 🎉 Success Criteria

**Production deployment is successful when:**

1. ✅ Backend health check returns `ok: true`
2. ✅ All generated content has `stub_used: false`
3. ✅ Quality checks enforce benchmarks (`quality_passed: true` for relevant packs)
4. ✅ Streamlit UI shows "LLM Mode: PRODUCTION"
5. ✅ Live verification tools confirm real LLM usage
6. ✅ Error handling provides transparent, actionable diagnostics
7. ✅ No `stub_in_production_forbidden` errors in logs
8. ✅ LLM fallback chain works (OpenAI → Perplexity → error)

---

**Status:** ✅ AICMO is production-ready for Render + Streamlit Cloud deployment with real LLM usage and quality enforcement.

**Next Steps:**
1. Deploy to Render with production keys
2. Deploy to Streamlit Cloud with production keys
3. Run health checks and verify all acceptance criteria
4. Monitor logs for first 24 hours
5. Set up automated daily health checks

**Support:** See troubleshooting section above or review `reports/AICMO_PRODUCTION_READINESS.md` for additional technical details.
