# Operator QC – Quick Reference Guide

**For:** Agency Operators, QA Leads, and Quality Inspectors  
**Status:** ✅ Production Ready

---

## 🚀 Quick Start (3 Steps)

### 1. Enable Operator Mode
```
Main Dashboard → Left Sidebar → Toggle "🛈 Operator Mode (QC)"
```

### 2. Generate a Report
```
Select Package → Fill Brief → Click "Generate draft report"
→ System auto-generates proof file
→ See proof info on Final Output tab
```

### 3. Access QC Dashboard
```
Sidebar → "📊 QC Dashboard" link → Operator QC opens in new tab
```

---

## 📊 Dashboard Layout (5 Tabs)

### Tab 1: QA Panel
**What:** Control center for audits and learning

**Buttons:**
- ▶️ **Run Quick QA** – Brief validation (10 sec)
- 🧪 **Run Full WOW Audit** – All 12 packs (30 sec)
- 📁 **Open Proof Folder** – Browse `.aicmo/proof/`

**Controls:**
- ☑ Enable Learning for This Report Only
- ☑ Force Skip Learning
- ☑ Show Raw Model Output

**Status Display:**
```
Total Packs: 12  |  ✅ OK: 12  |  ❌ BAD: 0
```

---

### Tab 2: Proof Files
**What:** Inspect every report's generation artifacts

**How to Use:**
1. **Select File** – Dropdown with latest proof files + timestamps
2. **View Metadata** – File name, size KB, generated time
3. **Action Buttons:**
   - 👁️ View Full Content (expand full file)
   - ⬇️ Download (save as markdown)
   - 📋 Copy to Clipboard

**Proof File Contains:**
- Executive summary (brand, geography, learnable status)
- Brief metadata (complete input)
- Quality gate results (all checks)
- Placeholder injection table
- Sanitization diff (what was removed)
- Final sanitized report

---

### Tab 3: Quality Gates
**What:** Live quality checks with problem highlighting

**Key Metrics:**

| Check | What It Does | Pass Indicator |
|-------|-------------|----------------|
| **Learnability** | Can learning system use this? | ✅ Eligible |
| **Report Length** | Long enough (min 500 chars)? | ✅ OK |
| **Forbidden Patterns** | No errors/placeholders leaked? | ✅ 8/8 Pass |
| **Brief Integrity** | All required fields present? | ✅ 5/5 Fields |

**Problems Show Like:**
```
❌ Placeholder Leak: '{{offer}}' still in output
❌ Error Marker: '[Error generating messaging]'
❌ Missing Field: 'industry' not in brief
```

---

### Tab 4: Pack Health
**What:** Dashboard of all 12 WOW packages

**Display:**
```
Total: 12  |  Healthy ✅: 12  |  Issues ❌: 0

Pack Name                      Status    Size
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
quick_social_basic             ✅ OK     1.3 KB
strategy_campaign_standard     ✅ OK     1.7 KB
full_funnel_growth_suite       ✅ OK     2.4 KB
launch_gtm_pack                ✅ OK     1.2 KB
... (12 total)
```

**Button:**
- 🔄 Run Audit Again – Re-test all 12 packs

---

### Tab 5: Advanced Features
**What:** Power tools for operators

**Sanitization Diff**
- Shows: Raw output vs Sanitized output
- Use: Verify what was cleaned up

**Placeholder Table**
- Shows: Every `{{placeholder}}` and its filled value
- Use: Verify all fields populated

**Regenerate Section**
- Select: Failed section from dropdown
- Click: 🔄 Regenerate This Section
- Result: Re-run single section (fast retry)

---

## 🎯 Common Workflows

### Workflow 1: Generate & Verify a Report
```
1. Select package (e.g., "Launch GTM Pack")
2. Fill brief (brand, industry, geography, audience, goals)
3. Click "Generate draft report"
4. System generates proof file automatically ✅
5. On Final Output tab: See "📋 Proof File Info (Operator Mode)"
6. Optional: Click "📊 View QC Dashboard"
7. On Quality Gates tab: Verify all checks pass ✅
8. Ready to send to client
```

### Workflow 2: Investigate a Problem Report
```
1. Open QC Dashboard
2. Go to "Quality Gates" tab
3. Find which check failed (see ❌ indicator)
4. Go to "Proof Files" tab
5. Select problem report from dropdown
6. Click "👁️ View Full Content"
7. Examine brief, placeholders, error markers
8. Identify root cause
9. Go to "Advanced Features" tab
10. Click "🔄 Regenerate This Section"
11. Re-test with quick QA
```

### Workflow 3: Audit All Packages Daily
```
1. Open QC Dashboard
2. Go to "Pack Health" tab
3. Click "🔄 Run Audit Again"
4. Wait 30 seconds for full test
5. Check: All 12 show ✅ OK
6. If any ❌ BAD, click that row for proof file
7. Investigate + regenerate
```

### Workflow 4: Download Proof for Client Dispute
```
1. QC Dashboard → "Proof Files" tab
2. Select report in question
3. Click "👁️ View Full Content"
4. Click "⬇️ Download" button
5. Save as markdown
6. Send to client with explanation
```

---

## ⚠️ Common Issues & Fixes

### Issue: Report shows "❌ Not Learnable"
**Reason:** Quality gates detected error/placeholder leak  
**Fix:**
1. Go to "Quality Gates" tab
2. Find ❌ indicator (e.g., "Placeholder Leak")
3. Go to "Advanced Features" → "Sanitization Diff"
4. See what's broken
5. Go to "Advanced Features" → "Regenerate Section"
6. Select broken section, click regenerate
7. Re-test with "▶️ Run Quick QA"

### Issue: Specific section keeps failing
**Reason:** Generator bug or brief data issue  
**Fix:**
1. Check "Proof Files" → view full proof
2. Look at "Brief Metadata" section
3. Verify all required fields present
4. If brief is bad: Go back, re-enter brief
5. If brief is good: Contact engineering team
6. For now: "Advanced Features" → "Regenerate Section"

### Issue: "Total Packs: 12, But BAD: 2"
**Reason:** One or more packages failing WOW audit  
**Fix:**
1. Go to "Pack Health" tab
2. Look for ❌ BAD indicators in table
3. Click that pack row
4. View proof file for that pack
5. See which quality check failed
6. Contact engineering team with proof file

---

## 🔑 Key Controls

| Control | Purpose | Location |
|---------|---------|----------|
| **Operator Mode Toggle** | Enable/disable QC interface | Main Dashboard Sidebar |
| **Run Quick QA** | Fast validation (10 sec) | QA Panel Tab |
| **Run Full WOW Audit** | Test all 12 packs (30 sec) | QA Panel Tab |
| **Enable Learning Toggle** | Learn from this report only | QA Panel Tab |
| **Force Skip Learning** | Prevent learning this time | QA Panel Tab |
| **Show Raw Output** | Debug raw model output | QA Panel Tab |
| **Proof Files Dropdown** | Select report to inspect | Proof Files Tab |
| **View Full Content** | Expand full proof file | Proof Files Tab |
| **Quality Gates Display** | See all 8 checks + results | Quality Gates Tab |
| **Pack Health Table** | See all 12 packs + status | Pack Health Tab |
| **Sanitization Diff** | Raw vs Sanitized comparison | Advanced Features Tab |
| **Regenerate Section** | Re-run single failed section | Advanced Features Tab |

---

## 📁 Proof File Location

All proof files stored in:
```
.aicmo/proof/operator/
```

Format: `<package_key>_<timestamp>.md`

Example:
```
launch_gtm_pack_20251126_161234.md
quick_social_basic_20251126_162100.md
strategy_campaign_standard_20251126_163000.md
```

---

## ✅ Pre-Send Checklist

Before sending report to client:

- [ ] ✅ All Quality Gates pass (Quality Gates tab)
- [ ] ✅ Report length > 500 chars (shown in QA Panel)
- [ ] ✅ No placeholder leaks (Sanitization Diff)
- [ ] ✅ All brief fields filled (Proof Files)
- [ ] ✅ No error markers in final report (Proof Files)
- [ ] ✅ Learnable status = ✅ Eligible (Quality Gates)

---

## 🎓 Training Links

- **Full Documentation:** `OPERATOR_QC_INTERFACE_COMPLETE.md`
- **Architecture Diagram:** (See OPERATOR_QC_INTERFACE_COMPLETE.md)
- **Quality Gates Details:** (See OPERATOR_QC_INTERFACE_COMPLETE.md → Module 3)
- **Proof File Format:** (See OPERATOR_QC_INTERFACE_COMPLETE.md → Module 2)

---

## 📞 Support

**Question:** How do I enable Operator Mode?  
**Answer:** Main Dashboard → Sidebar → Toggle "🛈 Operator Mode (QC)"

**Question:** Where are proof files stored?  
**Answer:** `.aicmo/proof/operator/` (auto-generated when report is output)

**Question:** What if a report fails quality gates?  
**Answer:** Go to Quality Gates tab, find ❌ indicator, use Advanced Features to regenerate

**Question:** How do I audit all 12 packs?  
**Answer:** QC Dashboard → Pack Health tab → "🔄 Run Audit Again" button

**Question:** Can I download a proof file?  
**Answer:** Yes! Proof Files tab → Select report → "⬇️ Download" button

---

**Version:** 1.0  
**Status:** ✅ Production Ready  
**Last Updated:** November 26, 2025
