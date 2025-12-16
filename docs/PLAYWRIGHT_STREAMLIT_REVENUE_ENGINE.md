# Playwright E2E Tests for AICMO Revenue Marketing Engine

This document describes how to run end-to-end tests against the Streamlit operator dashboard to verify the Revenue Marketing Engine works correctly in database mode with proof-run safety.

## ⚠️ CRITICAL SAFETY RULES

1. **NO Real External Sends**: All tests run with `AICMO_PROOF_RUN=1` - NO emails, DMs, or posts are sent
2. **DB Mode Only**: Tests require `AICMO_PERSISTENCE_MODE=db`
3. **Deterministic Isolation**: Each test resets business tables (not schema) before execution
4. **No Breaking Existing Tests**: Pytest regression suite must pass after Playwright runs

## Prerequisites

### 1. Install Node.js Dependencies

```bash
cd /workspaces/AICMO
npm install
npm run playwright:install
```

### 2. Ensure Database Is Migrated

```bash
export AICMO_PERSISTENCE_MODE=db
alembic upgrade head
```

## Running E2E Tests

### Step 1: Start Streamlit in E2E Mode

In a terminal, run:

```bash
export AICMO_PERSISTENCE_MODE=db
export AICMO_E2E_MODE=1
export AICMO_E2E_DIAGNOSTICS=1
export AICMO_PROOF_RUN=1
streamlit run streamlit_app.py --server.port 8501 --server.headless true
```

**What these env vars do:**
- `AICMO_PERSISTENCE_MODE=db`: Use database persistence (required)
- `AICMO_E2E_MODE=1`: Enable E2E test mode (forces proof-run, disables background workers)
- `AICMO_E2E_DIAGNOSTICS=1`: Show E2E Diagnostics panel in Streamlit
- `AICMO_PROOF_RUN=1`: Force all distribution to proof-run mode (NO real sends)

**Wait for Streamlit to be ready:**

You should see output like:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### Step 2: Run Playwright Tests

In a **separate terminal**:

```bash
cd /workspaces/AICMO
npm run test:e2e
```

**Available test commands:**
- `npm run test:e2e`: Run all tests headless
- `npm run test:e2e:headed`: Run with browser visible (for debugging)
- `npm run test:e2e:debug`: Run in debug mode with Playwright Inspector

### Step 3: Verify Regression Suite

After Playwright tests complete, verify existing pytest tests still pass:

```bash
export AICMO_PERSISTENCE_MODE=db
pytest tests/core/test_preflight.py tests/cam/test_lead_ingestion.py tests/cam/test_template_system.py -v --tb=line
```

**Expected output:** All tests passing (30+ tests)

## Test Coverage

### Test 1: Campaign Lifecycle Gates Dispatch
- **Purpose**: Verify pause/resume/stop controls work
- **Actions**: Toggle system pause checkbox, verify blocked/allowed states
- **Assertions**: "System Paused" label appears/disappears, diagnostics updates

### Test 2: Lead Capture + Attribution + Dedupe
- **Purpose**: Verify leads can be added with UTM params and dedupe works
- **Status**: ⚠️ **TODO** - Requires lead capture UI in Streamlit
- **Expected UI**: Form with name, email, company, utm_source, utm_campaign fields
- **Assertions**: Lead count increases, duplicate email blocked, attribution fields persist

### Test 3: DNC / Unsubscribe Enforcement
- **Purpose**: Verify DNC leads are never contacted
- **Status**: ⚠️ **TODO** - Requires DNC toggle UI in Streamlit
- **Expected UI**: Checkbox to mark lead as DNC/unsubscribed
- **Assertions**: Outreach blocked, no SENT/PROOF_SENT jobs for DNC leads

### Test 4: Proof-Run Distribution Job Execution
- **Purpose**: Verify jobs can be enqueued and executed in proof-run mode
- **Status**: ⚠️ **TODO** - Requires job dispatch UI in Streamlit
- **Expected UI**: Button to enqueue job, button to run dispatcher
- **Assertions**: Job status = PROOF_SENT, outreach count increases, NO real sends

### Test 5: Artifacts Export Exists and Is Correct
- **Purpose**: Verify CSV exports and report generation work
- **Status**: ⚠️ **TODO** - Requires export UI in Streamlit
- **Expected UI**: Export CSV button, Generate Report button
- **Assertions**: Downloaded CSV has correct headers, report file exists with required sections

### Bonus Test: E2E Diagnostics Panel Functional
- **Purpose**: Verify diagnostics panel itself works
- **Actions**: Navigate to Dashboard, scroll to diagnostics
- **Assertions**: Warning banner visible, Hard Reset button works, metrics display correctly

## E2E Diagnostics Panel

The diagnostics panel is only visible when `AICMO_E2E_DIAGNOSTICS=1` is set.

**Location**: Dashboard → Scroll to bottom → "E2E Diagnostics (Test Mode)"

**Features:**
1. **Hard Reset Test Data**: Deletes all business tables (leads, campaigns, jobs, templates) but keeps schema/migrations
2. **Campaign Selector**: Choose which campaign to inspect
3. **Counts**: Real-time metrics for leads, outreach attempts, templates, import batches
4. **Recent Events**: Last 10 outreach attempts with timestamps and statuses

**Safety:**
- Hard Reset only deletes business data, NOT `alembic_version` or schema
- Safe to call even when tables are empty
- Uses `PRAGMA foreign_keys = OFF` temporarily to avoid FK constraint issues

## How Tests Avoid Real Sends

### 1. Proof-Run Mode Enforcement
- `AICMO_PROOF_RUN=1` environment variable
- All distribution adapters check this flag
- Proof-run mode: Job marked as `PROOF_SENT`, NO external API calls

### 2. E2E Mode Disables Background Workers
- `AICMO_E2E_MODE=1` disables always-on scheduler loops
- Only manual dispatch via UI (controlled by tests)
- Ensures deterministic execution

### 3. Test Database Isolation
- Each test calls `hardResetTestData()` before execution
- Truncates business tables deterministically
- No cross-test contamination

## Artifacts Storage

**Campaign Reports**: `/workspaces/AICMO/artifacts/campaign_<id>/`

Expected files:
- `report_<timestamp>.md`: Campaign report with sections
- `leads_<timestamp>.csv`: Lead export with attribution
- `summary_<timestamp>.txt`: Executive summary

**Report Required Sections:**
- Executive Summary
- Attribution
- Next Actions

## Troubleshooting

### Streamlit Won't Start
```bash
# Check if port 8501 is already in use
lsof -i :8501

# Kill existing process if needed
kill -9 <PID>

# Restart Streamlit
streamlit run streamlit_app.py --server.port 8501 --server.headless true
```

### Playwright Tests Timeout
- Increase timeout in `playwright.config.ts` (currently 60s per test)
- Check Streamlit logs for errors
- Verify E2E_DIAGNOSTICS=1 is set (diagnostics panel must be visible)

### "Hard Reset" Button Not Found
- Verify `AICMO_E2E_DIAGNOSTICS=1` is set in Streamlit terminal
- Refresh browser/page
- Check Streamlit logs for errors in `aicmo/core/e2e_helpers.py`

### Tests Fail with "TODO" Messages
- Some tests are placeholders waiting for UI implementation
- See test comments for required UI components
- Implement missing UI, then re-run tests

### Regression Tests Fail After Playwright
- This should NOT happen (tests are isolated)
- Check if `hard_reset_test_data()` is working correctly
- Verify `alembic_version` table was NOT deleted
- Re-run migrations: `alembic upgrade head`

## Development Workflow

### Adding New E2E Tests

1. Add test to `tests/playwright/revenue_engine.spec.ts`
2. Use `data-testid` attributes in Streamlit components
3. Call `hardResetTestData()` in `beforeEach` hook
4. Verify DB state via diagnostics panel
5. Run test: `npm run test:e2e`

### Adding UI for Tests

If a test has a "TODO" comment:

1. Add the UI component to `streamlit_app.py`
2. Add `data-testid` or `key` attribute for stable selectors
3. Update the Playwright test to use the new UI
4. Remove "TODO" comment
5. Run full test suite to verify

Example:
```python
# In streamlit_app.py
st.button("Add Lead", key="add_lead_button")

# In Playwright test
await page.click('[data-testid="stButton"]:has-text("Add Lead")');
```

## Exit Criteria

Tests are considered **PASSING** only if:

1. ✅ All 5+ Playwright tests pass twice back-to-back
2. ✅ NO real external sends occurred (proof-run logs confirm)
3. ✅ Regression pytest suite remains green (30+ tests)
4. ✅ Diagnostics shows correct DB counts and events

If any test fails:
- Fix the underlying bug (don't add retries)
- Use deterministic selectors (data-testid)
- Document why if retries are unavoidable

## Next Steps

### Currently Implemented:
- ✅ Playwright config
- ✅ E2E diagnostics panel in Streamlit
- ✅ Hard reset test data function
- ✅ Test 1: Campaign lifecycle (basic)
- ✅ Bonus test: Diagnostics panel functional

### TODO (Requires UI Implementation):
- ⚠️ Lead capture form with UTM params
- ⚠️ DNC toggle UI
- ⚠️ Job dispatch UI (enqueue + run dispatcher)
- ⚠️ Export CSV + Generate Report UI

**Priority**: Implement job dispatch UI first (Test 4) as it's most critical for revenue operations.
