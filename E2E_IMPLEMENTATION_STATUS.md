# E2E Test Implementation Status

**Created**: 2025-01-XX  
**Status**: Infrastructure Complete, Tests Partially Implemented

## ✅ COMPLETED: E2E Infrastructure (100%)

### 1. Playwright Configuration
- **package.json**: Playwright dependencies, test scripts
- **playwright.config.ts**: workers=1 (serial), retries=0, baseURL=:8501
- **Node.js**: v20.19.6 installed via nvm
- **Chromium**: Playwright browser installed

### 2. E2E Helpers (`aicmo/core/e2e_helpers.py`)
- `is_e2e_mode()`: Check AICMO_E2E_MODE=1
- `is_e2e_diagnostics_enabled()`: Check AICMO_E2E_DIAGNOSTICS=1
- `hard_reset_test_data(session)`: Truncate business tables in FK-safe order
- `get_diagnostics_data(session, campaign_id)`: Return counts + recent events
- `get_campaign_status(session, campaign_id)`: Return campaign details
- **Safety**: Disables FK checks temporarily, never touches `alembic_version`

### 3. Streamlit E2E Diagnostics Panel (`streamlit_app.py` lines 916-1007)
- **Visibility**: Only when `AICMO_E2E_DIAGNOSTICS=1`
- **Location**: After "Control Tower" tab, before navigation section
- **Features**:
  - ⚠️ Warning banner (test mode indicator)
  - 🔄 Hard Reset button with deletion summary
  - 📊 Campaign selector dropdown
  - ✅ Campaign status (ID, name, active, mode)
  - 📈 4 metrics: Leads, Outreach Attempts, Templates, Import Batches
  - 📋 Recent Events table (last 10 outreach attempts)

### 4. Playwright Test File (`tests/playwright/revenue_engine.spec.ts`)
- **3 Helper Functions**:
  - `waitForStreamlitReady(page)`: Wait for sidebar + 1s settle
  - `hardResetTestData(page)`: Navigate to diagnostics, click reset
  - `getDiagnosticCounts(page)`: Extract metrics from diagnostics panel
- **beforeEach Hook**: Navigate + hard reset for deterministic isolation

### 5. Documentation
- **docs/PLAYWRIGHT_STREAMLIT_REVENUE_ENGINE.md**: Complete E2E testing guide
  - Prerequisites (Node.js, npm, Playwright)
  - Running tests (env vars, commands)
  - Safety guarantees (proof-run, DB isolation)
  - Test coverage (5 tests + 1 bonus)
  - Troubleshooting guide

## ✅ COMPLETED: Working Tests (2/6)

### Test 1: Campaign Lifecycle Gates Dispatch ✅
- **Status**: IMPLEMENTED
- **Actions**: 
  - Click pause checkbox → verify "System Paused" label
  - Resume → verify label disappears
  - Stop → verify label reappears
- **Assertions**: Label visibility, diagnostic counts defined
- **Result**: PASS (basic implementation)

### Bonus Test: E2E Diagnostics Panel Functional ✅
- **Status**: IMPLEMENTED
- **Actions**:
  - Navigate to Dashboard
  - Scroll to diagnostics section
  - Verify warning banner visible
  - Verify Hard Reset button visible
  - Extract diagnostic counts
- **Assertions**: Metrics readable, counts >= 0
- **Result**: PASS

## ⚠️ PENDING: Tests Blocked by Missing UI (4/6)

### Test 2: Lead Capture + Attribution + Dedupe ⚠️
- **Status**: TODO (placeholder)
- **Missing UI**: Lead capture form
- **Required UI Components**:
  - Navigation item: "Leads"
  - Form fields: name, email, company, utm_source, utm_campaign
  - Submit button with deduplication logic
  - Lead table display
  - `data-testid` attributes for Playwright
- **Expected Test Flow**:
  1. Navigate to Leads page
  2. Fill form with name, email, company, UTM params
  3. Submit → verify lead count = 1
  4. Submit duplicate email → verify lead count still = 1 (dedupe worked)
  5. Verify attribution fields persisted (utm_source, utm_campaign)
- **Current Implementation**: `console.log` with TODO message, placeholder assertion

### Test 3: DNC / Unsubscribe Enforcement ⚠️
- **Status**: TODO (placeholder)
- **Missing UI**: DNC toggle
- **Required UI Components**:
  - Lead table with checkbox/toggle column
  - `data-testid="lead-dnc-toggle"` attribute
  - Updates `consent_status` to "DNC" on click
- **Expected Test Flow**:
  1. Add lead via capture form
  2. Mark lead as DNC via toggle
  3. Attempt to create outreach job for lead
  4. Verify outreach count = 0 (blocked by DNC)
  5. Verify job not created or marked as BLOCKED
- **Current Implementation**: `console.log` with TODO message, placeholder assertion

### Test 4: Proof-Run Distribution Job Execution ⚠️
- **Status**: TODO (placeholder)
- **Missing UI**: Job dispatch buttons
- **Required UI Components**:
  - Navigation item: "Distribution"
  - "Enqueue Job" button (campaign, template, leads selector)
  - "Run Dispatcher" button (executes jobs in proof mode)
  - Job status table (id, lead_id, status, created_at)
  - `data-testid="enqueue-job"`, `data-testid="run-dispatcher"`
- **Expected Test Flow**:
  1. Navigate to Distribution page
  2. Select campaign, template, lead
  3. Click "Enqueue Job" → verify job created
  4. Click "Run Dispatcher" → verify job status = PROOF_SENT
  5. Verify outreach attempt count increased
  6. Verify NO real sends (check logs for proof-run confirmation)
- **Current Implementation**: `console.log` with TODO message, placeholder assertion
- **Priority**: HIGH (most critical for revenue operations)

### Test 5: Artifacts Export Exists and Is Correct ⚠️
- **Status**: TODO (placeholder)
- **Missing UI**: Export buttons
- **Required UI Components**:
  - "Export Leads CSV" button (downloads leads with attribution)
  - "Generate Report" button (creates report.md in artifacts/)
  - `data-testid="export-csv"`, `data-testid="generate-report"`
- **Expected Test Flow**:
  1. Navigate to Dashboard or Export page
  2. Click "Export Leads CSV" → download completes
  3. Verify CSV headers: name, email, company, utm_source, utm_campaign
  4. Click "Generate Report" → verify file exists
  5. Verify report sections: Executive Summary, Attribution, Next Actions
- **Current Implementation**: `console.log` with TODO message, placeholder assertion

## 📋 NEXT STEPS

### Priority 1: Implement UI for Test 4 (Job Dispatch)
**Estimated Time**: 1-2 hours

1. **Add "Distribution" navigation item** in streamlit_app.py
   - New tab or section after Control Tower
   - Key: `distribution_tab`

2. **Create Job Enqueue UI**:
   ```python
   # Campaign selector
   campaign = st.selectbox("Select Campaign", campaigns, key="job_campaign")
   
   # Template selector
   template = st.selectbox("Select Template", templates, key="job_template")
   
   # Lead selector (multi-select)
   leads = st.multiselect("Select Leads", all_leads, key="job_leads")
   
   # Enqueue button
   if st.button("Enqueue Job", key="enqueue_job"):
       # Create OutreachAttemptDB records with status=PENDING
       st.success(f"Enqueued {len(leads)} jobs")
   ```

3. **Create Dispatcher UI**:
   ```python
   if st.button("Run Dispatcher", key="run_dispatcher"):
       # Fetch PENDING jobs
       # For each job:
       #   - Render template
       #   - Execute in proof-run mode
       #   - Mark as PROOF_SENT
       st.success(f"Dispatched {count} jobs in proof-run mode")
   ```

4. **Add Job Status Table**:
   ```python
   jobs_df = session.query(OutreachAttemptDB).all()
   st.dataframe(jobs_df)
   ```

5. **Update Playwright Test**:
   - Remove TODO placeholder
   - Implement actual clicks and assertions
   - Verify DB state via diagnostics

### Priority 2: Implement UI for Test 2 (Lead Capture)
**Estimated Time**: 1 hour

1. **Add "Leads" navigation item**
2. **Create Lead Capture Form** (see Test 2 details above)
3. **Add Lead Table Display**
4. **Update Playwright Test**

### Priority 3: Implement UI for Test 3 (DNC Toggle)
**Estimated Time**: 30 minutes

1. **Add DNC column to lead table**
2. **Implement toggle with consent_status update**
3. **Update Playwright Test**

### Priority 4: Implement UI for Test 5 (Exports)
**Estimated Time**: 1 hour

1. **Add Export CSV button**
2. **Add Generate Report button**
3. **Update Playwright Test**

### Priority 5: Full Test Execution
**Estimated Time**: 30 minutes

1. **Start Streamlit with E2E env vars**:
   ```bash
   export AICMO_PERSISTENCE_MODE=db
   export AICMO_E2E_MODE=1
   export AICMO_E2E_DIAGNOSTICS=1
   export AICMO_PROOF_RUN=1
   streamlit run streamlit_app.py --server.port 8501 --server.headless true
   ```

2. **Run Playwright tests twice**:
   ```bash
   npm run test:e2e
   npm run test:e2e  # Second run for reliability
   ```

3. **Verify regression suite**:
   ```bash
   pytest tests/core/test_preflight.py tests/cam/test_lead_ingestion.py tests/cam/test_template_system.py -v
   ```

4. **Document results** in E2E_EXECUTION_RESULTS.md

## 🎯 EXIT CRITERIA

- ✅ All 6 Playwright tests pass twice back-to-back
- ✅ NO real external sends (proof-run logs confirm)
- ✅ Regression pytest suite remains green (30+ tests)
- ✅ Diagnostics shows correct DB counts after each test
- ✅ Documentation complete

## 📊 CURRENT METRICS

| Category | Status | Count | Percentage |
|----------|--------|-------|------------|
| **Infrastructure** | ✅ Complete | 5/5 | 100% |
| **Working Tests** | ✅ Implemented | 2/6 | 33% |
| **Blocked Tests** | ⚠️ TODO | 4/6 | 67% |
| **Missing UI** | ❌ Pending | 4 components | - |
| **Documentation** | ✅ Complete | 2 files | 100% |

## 🚀 ESTIMATED COMPLETION TIME

- **Infrastructure**: ✅ DONE
- **UI Implementation**: 3-5 hours
- **Test Implementation**: 1-2 hours
- **Verification**: 30 minutes
- **TOTAL**: 4.5-7.5 hours

## 🔧 TROUBLESHOOTING

### If Tests Fail with "TODO" Messages
- This is expected! Tests 2-5 are placeholders waiting for UI
- See "PENDING" section above for required UI components
- Implement UI, then re-run tests

### If Diagnostics Panel Not Visible
- Verify `AICMO_E2E_DIAGNOSTICS=1` is set
- Restart Streamlit with correct env vars
- Check for errors in Streamlit logs

### If Hard Reset Fails
- Check FK constraint order in `e2e_helpers.py`
- Verify database is migrated (`alembic upgrade head`)
- Check if `alembic_version` is still present (should NOT be deleted)

## 📝 NOTES

- **Design Decision**: Tests 2-5 are placeholders to allow infrastructure completion
- **Rationale**: Enables parallel work (infrastructure + UI development)
- **Next Session**: Focus on UI implementation for blocked tests
- **Testing Philosophy**: Fix bugs, don't add retries; deterministic isolation via hard reset
