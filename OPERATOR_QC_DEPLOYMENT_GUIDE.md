# Operator QC – Deployment & Testing Guide

**Date:** November 26, 2025  
**Status:** ✅ READY FOR DEPLOYMENT  
**Audience:** DevOps, QA Lead, Engineering Manager

---

## 📋 Pre-Deployment Checklist

### Code Quality
- [x] `operator_qc.py` created (800+ lines)
- [x] `proof_utils.py` created (250+ lines)
- [x] `aicmo_operator.py` modified (proof integration)
- [x] All files compile without syntax errors
- [x] No import errors detected
- [x] Follows AICMO code style

### Integration
- [x] Proof file generation wired to final output
- [x] Operator Mode toggle added to sidebar
- [x] Session state tracking implemented
- [x] Quick links to QC dashboard, proof folder, audit

### Testing
- [x] Proof file format verified
- [x] Quality gate checks implemented
- [x] WOW audit script integration verified
- [x] Pack health monitor logic verified

### Documentation
- [x] Complete interface documentation
- [x] Quick reference guide for operators
- [x] Architecture overview
- [x] Usage examples

---

## 🚀 Deployment Steps

### Step 1: Deploy Code Files

```bash
# Verify files exist
ls -la /workspaces/AICMO/streamlit_pages/operator_qc.py
ls -la /workspaces/AICMO/streamlit_pages/proof_utils.py

# Check integration in main file
grep -n "Operator Mode" /workspaces/AICMO/streamlit_pages/aicmo_operator.py
grep -n "generate_proof_file" /workspaces/AICMO/streamlit_pages/aicmo_operator.py
```

### Step 2: Verify Directory Structure

```bash
# Verify proof directory exists
mkdir -p .aicmo/proof/operator

# Verify audit script exists (for WOW Pack Health Monitor)
ls -la scripts/dev/aicmo_wow_end_to_end_check.py

# Verify quality gates module exists
ls -la backend/quality_gates.py
```

### Step 3: Verify Dependencies

Check that all imports are available:

```bash
# Check for streamlit
python -c "import streamlit; print('✅ Streamlit available')"

# Check for backend imports
python -c "from backend.quality_gates import is_report_learnable; print('✅ Quality gates available')"

# Check for subprocess (standard library)
python -c "import subprocess; print('✅ Subprocess available')"
```

### Step 4: Test Streamlit Launch

```bash
# In terminal where streamlit is running:
streamlit run operator_v2.py --server.port 8502 --server.headless true

# Then in browser:
# 1. Navigate to main dashboard
# 2. Look for "🛈 Operator Mode (QC)" toggle in sidebar
# 3. Toggle should be visible and clickable
# 4. When toggled ON, should show quick links
```

### Step 5: Run Smoke Test

```bash
# Test 1: Generate a simple report
# 1. In Streamlit: Select package
# 2. Fill brief with test data
# 3. Click "Generate draft report"
# 4. Check that proof file is created:
#    ls -la .aicmo/proof/operator/

# Test 2: Open QC Dashboard
# 1. Click "📊 QC Dashboard" link in sidebar
# 2. Should see 5 tabs: QA Panel, Proof Files, Quality Gates, Pack Health, Advanced
# 3. All tabs should load without errors

# Test 3: Run Quick QA
# 1. In QA Panel tab: Click "▶️ Run Quick QA"
# 2. Should complete in ~10 seconds
# 3. Should show status (OK or BAD)

# Test 4: View Proof File
# 1. Go to "Proof Files" tab
# 2. Should see dropdown with available proof files
# 3. Click "👁️ View Full Content"
# 4. Should display full proof file

# Test 5: Check Quality Gates
# 1. Go to "Quality Gates" tab
# 2. Should see all quality checks listed
# 3. Should show ✅ or ❌ for each check

# Test 6: View Pack Health
# 1. Go to "Pack Health" tab
# 2. Should see table with all 12 packages
# 3. Click "🔄 Run Audit Again"
# 4. Should execute WOW audit and show results
```

---

## 🧪 Functional Testing

### Test Suite 1: Proof File Generation

**Test Case 1.1: Proof file created on report output**
```
Setup: Fresh session
Steps:
1. Select package
2. Fill brief with valid data
3. Click "Generate draft report"
4. Wait for completion

Expected:
✅ Proof file created in .aicmo/proof/operator/
✅ File name follows pattern: <package_key>_<timestamp>.md
✅ File contains all required sections
✅ Session state captures proof file path
```

**Test Case 1.2: Proof file contains correct metadata**
```
Setup: Report just generated
Steps:
1. Open proof file
2. Check Executive Summary section
3. Verify Brief Metadata (JSON dump)
4. Check Quality Gate Results

Expected:
✅ Executive Summary shows correct brand, industry, geography
✅ Brief Metadata matches input brief
✅ Quality Gate Results populated
✅ File shows correct timestamp
```

**Test Case 1.3: Multiple proof files in sequence**
```
Setup: Fresh session
Steps:
1. Generate report 1 (package A)
2. Generate report 2 (package B)
3. Generate report 3 (package A again)
4. Check proof directory

Expected:
✅ 3 separate files created
✅ Each has unique timestamp
✅ Dropdown shows all 3 files
✅ Timestamps in descending order (newest first)
```

---

### Test Suite 2: QA Panel Controls

**Test Case 2.1: Run Quick QA button**
```
Setup: Report generated
Steps:
1. Go to QA Panel tab
2. Click "▶️ Run Quick QA"
3. Wait for completion

Expected:
✅ Runs in ~10 seconds
✅ Shows status result (OK or BAD)
✅ No crashes or errors
✅ Output shows brief validation
```

**Test Case 2.2: Run Full WOW Audit button**
```
Setup: System in normal state
Steps:
1. Go to QA Panel tab
2. Click "🧪 Run Full WOW Audit"
3. Wait for completion (~30 seconds)

Expected:
✅ Runs all 12 packages
✅ Output shows "X OK, Y BAD, Z ERROR"
✅ No crashes
✅ Result file created (if generating new audit proof)
```

**Test Case 2.3: Enable Learning toggle**
```
Setup: Report generated with bad content
Steps:
1. Go to QA Panel tab
2. Toggle "Enable Learning for This Report Only" ON
3. In Quality Gates tab, check learnable status
4. Toggle OFF
5. Check status again

Expected:
✅ Toggle changes session state
✅ Learning status affected by toggle
✅ Can toggle multiple times
```

---

### Test Suite 3: Proof File Viewer

**Test Case 3.1: Proof file dropdown**
```
Setup: Multiple reports generated
Steps:
1. Go to Proof Files tab
2. Click dropdown

Expected:
✅ Lists all proof files with timestamps
✅ Most recent file appears first
✅ Timestamps formatted readably
✅ File sizes shown in KB
```

**Test Case 3.2: View Full Content**
```
Setup: Proof file selected
Steps:
1. Go to Proof Files tab
2. Select a proof file
3. Click "👁️ View Full Content"

Expected:
✅ Shows first 2000 chars with "View Full" expander
✅ Expander opens to show complete file
✅ Formatting preserved (markdown)
✅ All sections visible (summary, metadata, results, report)
```

**Test Case 3.3: Download button**
```
Setup: Proof file selected
Steps:
1. Go to Proof Files tab
2. Select a proof file
3. Click "⬇️ Download"

Expected:
✅ Browser initiates download
✅ File saved as markdown (.md)
✅ File name matches proof file
✅ Downloaded file is readable
```

---

### Test Suite 4: Quality Gate Inspector

**Test Case 4.1: All checks display**
```
Setup: Report with passing checks
Steps:
1. Go to Quality Gates tab
2. Observe displayed checks

Expected:
✅ Learnability section visible
✅ Report Length check shown
✅ Forbidden Pattern Scan listed (8 checks)
✅ Brief Integrity section shown (5 checks)
✅ Generator Integrity section shown
✅ All show ✅ or ❌ indicator
```

**Test Case 4.2: Failed check highlighting**
```
Setup: Generate report with known issue (e.g., placeholder leak)
Steps:
1. Go to Quality Gates tab
2. Observe checks

Expected:
✅ Failed checks show ❌ indicator
✅ Description of failure shown
✅ Error message is clear and actionable
```

---

### Test Suite 5: WOW Pack Health Monitor

**Test Case 5.1: Pack table displays**
```
Setup: System initialized, audit proofs available
Steps:
1. Go to Pack Health tab
2. Observe table

Expected:
✅ Shows all 12 WOW packages
✅ Each pack shows Status (✅ or ❌)
✅ Each pack shows Size in KB
✅ Table is sortable/readable
```

**Test Case 5.2: Run Audit Again button**
```
Setup: Pack Health tab open
Steps:
1. Click "🔄 Run Audit Again"
2. Wait ~30 seconds
3. Observe results

Expected:
✅ Audit script executes
✅ Results updated in table
✅ No crashes or errors
✅ Summary metrics (Total, Healthy, Issues) updated
```

---

### Test Suite 6: Advanced Features

**Test Case 6.1: Sanitization Diff displays**
```
Setup: Report with errors (placeholder leaks, etc.)
Steps:
1. Go to Advanced Features tab
2. Expand "Sanitization Diff" section

Expected:
✅ Shows "Raw Output" section
✅ Shows "Sanitized Output" section
✅ Differences are highlighted
✅ Easily identifies what was cleaned
```

**Test Case 6.2: Placeholder Table displays**
```
Setup: Report generated with placeholders filled
Steps:
1. Go to Advanced Features tab
2. Expand "Placeholder Table" section

Expected:
✅ Shows table with columns: Placeholder, Value, Status
✅ All {{placeholders}} listed
✅ Filled values shown
✅ Status shows ✅ Filled or ❌ Missing
```

**Test Case 6.3: Regenerate Section**
```
Setup: Report with failing section
Steps:
1. Go to Advanced Features tab
2. Expand "Regenerate Section"
3. Select failed section from dropdown
4. Click "🔄 Regenerate This Section"

Expected:
✅ Section dropdown shows available sections
✅ Regeneration executes
✅ Completes in ~5 seconds
✅ New proof file created
✅ Quality gate re-checks section
```

---

## 📊 Performance Benchmarks

### Expected Performance Metrics

| Operation | Expected Time | Alert Threshold |
|-----------|---------------|-----------------|
| Generate proof file | < 500 ms | > 2 sec |
| Load proof files list | < 200 ms | > 1 sec |
| Run Quick QA | ~10 sec | > 30 sec |
| Run Full WOW Audit | ~30 sec | > 60 sec |
| Render QC dashboard | < 2 sec | > 5 sec |
| Quality gates scan | < 1 sec | > 3 sec |

---

## 🔍 Troubleshooting

### Issue: Operator Mode toggle not visible

**Diagnosis:**
```bash
grep -n "Operator Mode" streamlit_pages/aicmo_operator.py
```

**Fix:**
- Verify aicmo_operator.py was modified
- Check for syntax errors: `python -m py_compile streamlit_pages/aicmo_operator.py`
- Restart Streamlit app

### Issue: Proof files not being created

**Diagnosis:**
```bash
ls -la .aicmo/proof/operator/
```

**Fix:**
- Check that directory exists: `mkdir -p .aicmo/proof/operator`
- Verify proof_utils.py exists: `ls -la streamlit_pages/proof_utils.py`
- Check Streamlit console for import errors
- Verify brief_dict being passed to generate_proof_file()

### Issue: Quality gates showing all ❌ BAD

**Diagnosis:**
- Check that quality_gates.py exists
- Verify proof file contains valid brief data

**Fix:**
```bash
python -c "from backend.quality_gates import is_report_learnable, sanitize_final_report_text; print('✅ Quality gates module OK')"
```

### Issue: WOW Audit shows no packages

**Diagnosis:**
```bash
ls -la scripts/dev/aicmo_wow_end_to_end_check.py
ls -la .aicmo/proof/wow_end_to_end/
```

**Fix:**
- Run audit script manually: `python scripts/dev/aicmo_wow_end_to_end_check.py`
- Check that proof files generated in `.aicmo/proof/wow_end_to_end/`

### Issue: QC Dashboard crashes on open

**Diagnosis:**
- Check Streamlit error console
- Look for import errors

**Fix:**
```bash
python -m py_compile streamlit_pages/operator_qc.py
```

---

## ✅ Production Sign-Off Checklist

### Code Quality
- [ ] All files compile without errors
- [ ] No import errors
- [ ] Follows AICMO code style
- [ ] Code reviewed by tech lead

### Integration
- [ ] Operator Mode toggle working
- [ ] Proof files auto-generating
- [ ] Quick links displayed
- [ ] Session state tracking

### Testing
- [ ] Smoke tests pass (6 tests)
- [ ] Functional tests pass (Test Suites 1-6)
- [ ] Performance benchmarks met
- [ ] No regressions in main dashboard

### Documentation
- [ ] Complete documentation written
- [ ] Quick reference guide complete
- [ ] Operator training conducted
- [ ] Support runbook created

### Deployment
- [ ] Code deployed to staging
- [ ] Staging tests pass
- [ ] Code deployed to production
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented

---

## 📞 Support Escalation

### Level 1: Self-Service (Operators)
- Refer to OPERATOR_QC_QUICK_REFERENCE.md
- Check dashboard hints/help text
- Review proof files for context

### Level 2: QA Lead
- Run diagnostic scripts
- Check logs for errors
- Review code changes

### Level 3: Engineering
- Debug backend integration
- Fix quality gates issues
- Investigate performance issues

---

## 📈 Post-Deployment Monitoring

### Daily Checks (First 2 Weeks)
- [ ] No crashes in logs
- [ ] Proof files being generated correctly
- [ ] Quality gates working as expected
- [ ] Operators using interface successfully

### Weekly Checks
- [ ] Performance metrics stable
- [ ] No error patterns detected
- [ ] Operator feedback positive
- [ ] No data quality issues

### Monthly Review
- [ ] ROI of operator QC interface
- [ ] Usage statistics
- [ ] Bug count and severity
- [ ] Feature requests

---

**Ready for Deployment:** ✅ YES  
**Deployment Date:** [To be scheduled]  
**Deployed By:** [DevOps/Engineering]  
**Verified By:** [QA Lead]  
**Documentation:** ✅ Complete

