# E2E Quick Start Guide

## 🚀 Running E2E Tests (Quick Reference)

### Terminal 1: Start Streamlit
```bash
export AICMO_PERSISTENCE_MODE=db
export AICMO_E2E_MODE=1
export AICMO_E2E_DIAGNOSTICS=1
export AICMO_PROOF_RUN=1
streamlit run streamlit_app.py --server.port 8501 --server.headless true
```

Wait for: `You can now view your Streamlit app in your browser.`

### Terminal 2: Run Tests
```bash
cd /workspaces/AICMO
npm run test:e2e
```

---

## ✅ Current Test Status

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Campaign Lifecycle | ✅ PASS | Pause/resume/stop controls work |
| Test 2: Lead Capture | ⚠️ TODO | Needs lead form UI |
| Test 3: DNC Enforcement | ⚠️ TODO | Needs DNC toggle UI |
| Test 4: Job Dispatch | ⚠️ TODO | Needs dispatch buttons UI |
| Test 5: Artifacts Export | ⚠️ TODO | Needs export buttons UI |
| Bonus: Diagnostics Panel | ✅ PASS | Hard reset + metrics work |

**Working Tests**: 2/6 (33%)  
**Regression Suite**: ✅ 30/30 passing

---

## 🔍 View Diagnostics Panel

1. Open http://localhost:8501
2. Navigate to "Dashboard"
3. Scroll to bottom → "E2E Diagnostics (Test Mode)"
4. Click "Hard Reset Test Data" to clean DB
5. View metrics: Leads, Outreach, Templates, Batches

---

## 📚 Full Documentation

- **Complete Guide**: [docs/PLAYWRIGHT_STREAMLIT_REVENUE_ENGINE.md](docs/PLAYWRIGHT_STREAMLIT_REVENUE_ENGINE.md)
- **Detailed Status**: [E2E_IMPLEMENTATION_STATUS.md](E2E_IMPLEMENTATION_STATUS.md)
- **Infrastructure Report**: [E2E_INFRASTRUCTURE_COMPLETE.md](E2E_INFRASTRUCTURE_COMPLETE.md)

---

## ⚡ Quick Commands

### Run tests with browser visible
```bash
npm run test:e2e:headed
```

### Debug tests with Playwright Inspector
```bash
npm run test:e2e:debug
```

### Verify regression suite
```bash
export AICMO_PERSISTENCE_MODE=db
pytest tests/core/test_preflight.py tests/cam/test_lead_ingestion.py tests/cam/test_template_system.py -v
```

### Install/update dependencies
```bash
npm install
npm run playwright:install
```

---

## 🛠️ Troubleshooting

### Diagnostics panel not visible?
- Check `AICMO_E2E_DIAGNOSTICS=1` is set in Terminal 1
- Restart Streamlit with correct env vars

### Tests timeout?
- Verify Streamlit is running on port 8501
- Check Streamlit logs for errors

### Hard Reset button not found?
- Scroll to bottom of Dashboard page
- Verify diagnostics panel is visible (warning banner)

---

## 🎯 Next Steps

1. **Add Job Dispatch UI** (Test 4) - Highest priority
2. **Add Lead Capture Form** (Test 2)
3. **Add DNC Toggle** (Test 3)
4. **Add Export Buttons** (Test 5)
5. **Update Playwright tests** (remove TODOs)
6. **Full verification** (all 6 tests pass twice)

**Estimated Time**: 4-6 hours for complete E2E suite
