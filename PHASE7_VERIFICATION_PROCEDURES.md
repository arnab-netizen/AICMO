# Phase 7 Verification Procedures

**Objective:** Validate 4 critical workflows before enabling client access  
**Estimated Time:** 4 hours total  
**Team Required:** 1 developer (UAT lead) + 1 non-technical operator

---

## Test 1: UI Integration Test (1 hour)

### Setup
```bash
# Terminal 1: Start backend API
cd /workspaces/AICMO
source .venv-1/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit frontend
cd /workspaces/AICMO
source .venv-1/bin/activate
streamlit run streamlit_app.py
```

### Verification Steps

**1. File Upload** (10 min)
- [ ] Open Streamlit UI (http://localhost:8501)
- [ ] Locate "Input" tab
- [ ] Click file upload widget
- [ ] Upload any PDF (test file: `/workspaces/AICMO/docs/external-connections.md` converted to PDF, or any sample)
- [ ] Expected: File appears in UI, no errors in console

**2. Industry Selection** (5 min)
- [ ] Look for industry dropdown/selector
- [ ] Verify all 4 industries visible:
  - [ ] b2b_saas
  - [ ] ecom_d2c
  - [ ] local_service
  - [ ] coaching
- [ ] Select one industry
- [ ] Expected: Dropdown shows selection, no errors

**3. Deliverables Selection** (5 min)
- [ ] Look for output type checkboxes/toggles
- [ ] Check at least 2 deliverables (e.g., "Report", "Slides")
- [ ] Expected: Selections persist, no errors

**4. Generate Report** (20 min)
- [ ] Click "Generate Report" button
- [ ] Wait for completion (may take 30-60 sec)
- [ ] Expected:
  - [ ] No "Coming Soon" message
  - [ ] No traceback errors
  - [ ] Report appears in "Workshop" tab
  - [ ] Structure looks like agency deck (sections, text, no lorem ipsum)

**5. Export Function** (15 min)
- [ ] In output section, look for export buttons
- [ ] Click "Export as PDF"
- [ ] Expected: File downloads, no errors
- [ ] Click "Export as DOCX" (if available)
- [ ] Expected: File downloads, no errors
- [ ] Check downloaded files:
  - [ ] PDF opens in viewer
  - [ ] DOCX opens in Word/LibreOffice
  - [ ] No corrupted content

**6. Browser Console Check** (5 min)
- [ ] Press F12 (Developer Tools)
- [ ] Check Console tab
- [ ] Expected: No red errors, no warnings about API keys

### Pass Criteria
✅ All 6 steps complete without crashes  
✅ No error messages shown to user  
✅ Export files are valid/openable  
✅ No sensitive data in console

---

## Test 2: Button Audit (30 min)

### Setup
Same Streamlit UI running from Test 1

### Verification Steps

**For Each Visible Button:**

```
Button Name: ________________
Location: ________________
Visible: YES / NO / HIDDEN
Status: WORKS / DEAD / DISABLED
Action: ________________

Pass criteria: Button either:
☐ Works (clear action happens)
☐ Disabled with clear state (greyed out)
☐ Doesn't exist (removed from UI)

FAIL if:
☒ Button visible but unresponsive
☒ Button says "Coming Soon"
☒ Silent failure (button click → nothing)
☒ Cryptic error message
```

**Common buttons to check:**
- [ ] Upload file
- [ ] Select industry dropdown
- [ ] Generate report
- [ ] Export PDF
- [ ] Export DOCX
- [ ] Request revision (if in UI)
- [ ] Settings / Options (if present)

**For any error:**
- [ ] Note the exact error message
- [ ] Check browser console (F12)
- [ ] Expected: User-friendly message, not traceback

### Pass Criteria
✅ Every visible button either works or is clearly disabled  
✅ No "Coming Soon" buttons visible  
✅ No dead click handlers  
✅ All error messages are user-friendly (no tracebacks)

---

## Test 3: Operator UAT (2 hours)

### Setup
- Have a non-technical team member available
- Streamlit UI running
- Backend API running
- **Do not help them** - let them discover UX issues

### Scenario: End-to-End Client Project

**Instructions to operator (read exactly):**

> Your task is to complete one client project in AICMO without asking for developer help.
> 
> Steps:
> 1. Upload the client's brief PDF (file provided)
> 2. Select which industries apply to this client
> 3. Choose what outputs you want (report, slides, etc.)
> 4. Generate the report
> 5. Review the draft
> 6. Request one revision (change something about the output)
> 7. Export the final report as PDF
> 
> Tell me when you complete each step and if anything confuses you.

### Observation Points

As they work, note:
- [ ] Can they find the upload button?
- [ ] Do they understand which industries to select?
- [ ] Are output options clear?
- [ ] Do they click the right button to generate?
- [ ] Does output appear where they expect?
- [ ] Can they find the revision/edit flow?
- [ ] Are export options clear?

### Data to Collect

| Step | Time (sec) | Confusion? | Issues? | Notes |
|------|-----------|-----------|---------|-------|
| Upload | ___ | Y/N | | |
| Industry selection | ___ | Y/N | | |
| Output selection | ___ | Y/N | | |
| Generate | ___ | Y/N | | |
| Review | ___ | Y/N | | |
| Revision | ___ | Y/N | | |
| Export | ___ | Y/N | | |
| **Total** | **___** | | | |

### Questions to Ask

1. "What was confusing?" → Note feedback
2. "What would you change?" → UX improvements
3. "Did you feel lost at any point?" → Navigation issues
4. "Would a client be happy with this output?" → Quality check

### Pass Criteria
✅ Operator completes all steps solo  
✅ No blockers (UI issues that stopped progress)  
✅ Operator able to generate viable output  
✅ Operator would recommend to others  

### Fail Criteria
❌ Operator stuck without dev help  
❌ Critical UI confusion (can't find buttons)  
❌ Output quality embarrassing (lorem ipsum, crashes)  
❌ Export doesn't work

---

## Test 4: Error Handling (30 min)

### Setup
- Backend API running
- Browser ready with Streamlit UI

### Test 4A: Invalid API Key (10 min)

**Step 1: Set invalid key**
```bash
# Stop backend, set invalid key
export OPENAI_API_KEY="sk-invalid-key-for-testing"
# Restart backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Step 2: Generate report with invalid key**
- [ ] Upload PDF
- [ ] Select industry
- [ ] Click Generate
- [ ] Expected: Clear message like:
  ```
  "Unable to enhance report (API error). 
   Using default output.
   Contact support if issue persists."
  ```
- [ ] NOT expected:
  ```
  Traceback: AuthenticationError...
  Invalid API key sk-invalid-key...
  ```

**Step 3: Check console**
- [ ] Press F12, check Console tab
- [ ] Expected: No API key shown, no technical error
- [ ] NOT expected: `OPENAI_API_KEY=sk-invalid-key` printed

### Test 4B: Network Timeout (10 min)

**Step 1: Simulate network failure**
```bash
# Option A: Block outbound traffic (requires sudo)
# Option B: Set fake LLM endpoint
export OPENAI_API_BASE="http://localhost:9999"  # Port that doesn't respond
```

**Step 2: Generate report**
- [ ] Upload PDF
- [ ] Select industry
- [ ] Click Generate
- [ ] Expected: Message like:
  ```
  "Service temporarily unavailable. 
   Using cached output.
   Please try again in a moment."
  ```

### Test 4C: Console Check (10 min)

**With backend still running:**
- [ ] Open browser developer tools (F12)
- [ ] Go to Console tab
- [ ] Generate a report
- [ ] Expected: No errors, no warnings about secrets
- [ ] Check Network tab
- [ ] Expected: API calls made cleanly (no auth errors visible)

### Pass Criteria
✅ Invalid API key → clear user message  
✅ Network timeout → clear user message  
✅ No technical errors shown to user  
✅ No secrets/keys logged to console  
✅ No Python tracebacks visible

---

## Failure Resolution Guide

### If Test 1 Fails (UI Integration)

**Symptom: File upload doesn't work**
- [ ] Check Streamlit error logs (Terminal 2)
- [ ] Verify backend API running (curl http://localhost:8000/health)
- [ ] Check CORS configuration
- **Fix:** Update streamlit_app.py file upload handler

**Symptom: Export doesn't work**
- [ ] Check if export endpoints exist (/aicmo/export)
- [ ] Verify PDF/DOCX generation library (python-pptx, etc.)
- **Fix:** Implement export endpoint if missing

**Symptom: Report shows lorem ipsum**
- [ ] Check backend/main.py line ~645 (generation logic)
- [ ] Verify stub mode is producing real content
- **Fix:** Review generation output in `/aicmo/generate`

### If Test 2 Fails (Button Audit)

**Symptom: Button visible but unresponsive**
- [ ] Check streamlit_app.py for button handler
- [ ] Verify callback function exists
- [ ] Check browser console for JS errors
- **Fix:** Add missing handler or wire to endpoint

**Symptom: Dead buttons (no action)**
- [ ] Search streamlit_app.py for `st.button("name")`
- [ ] Add `if button_name_clicked:` block
- **Fix:** Implement callback

**Symptom: "Coming Soon" visible**
- [ ] Conditional rendering issue
- [ ] Remove/hide if not ready
- **Fix:** Comment out or delete button

### If Test 3 Fails (Operator UAT)

**Symptom: Operator confused by UX**
- Collect specific feedback
- **Fix:** Add helper text, rearrange UI, add tooltips

**Symptom: Output is low quality**
- Check generation logic
- Verify industries are being used
- **Fix:** Improve prompt/template

**Symptom: Operator can't find export**
- Make export button more prominent
- **Fix:** Rearrange Streamlit layout

### If Test 4 Fails (Error Handling)

**Symptom: User sees traceback**
- [ ] Wrap endpoint in try/except
- [ ] Return HTTP 500 with user-friendly message
- **Fix:** backend/main.py error handling

**Symptom: API key leaked in console**
- [ ] Remove `print(api_key)` statements
- [ ] Check logging configuration
- **Fix:** Use logger.debug() instead of print()

**Symptom: No fallback on API failure**
- [ ] Add fallback to stub output
- [ ] Verify LLM_USE_LLM feature flag
- **Fix:** backend/llm_enhance.py

---

## Sign-Off

When all 4 tests pass, update this checklist:

```
✅ Test 1: UI Integration - PASS
   Date: ________  Tester: ________

✅ Test 2: Button Audit - PASS
   Date: ________  Tester: ________

✅ Test 3: Operator UAT - PASS
   Date: ________  Tester: ________
   Feedback: _______________

✅ Test 4: Error Handling - PASS
   Date: ________  Tester: ________

🟢 OVERALL: APPROVED FOR CLIENT LAUNCH
   Approved by: ________________  Date: ________
```

---

## Rollback Procedure

If any test fails critically:

```bash
# Revert to last known-good commit
git revert HEAD
git push origin main

# Notify team
echo "Critical failure detected. Reverting to e64bfdc"
```

---

**Document Version:** 1.0  
**Created:** 2025-11-21  
**Last Updated:** 2025-11-21
