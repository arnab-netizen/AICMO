# 🛡️ Operator QC Quick Start – 2 Minutes

**Get started with Operator QC Dashboard in 2 minutes**

---

## 1️⃣ Enable Operator Mode (30 seconds)

In the **AICMO Operator Dashboard** sidebar:
1. Scroll down to "🛡️ Operator Mode (QC)"
2. Click the toggle to turn it **ON** ✅
3. See the quick links appear:
   - 📊 QC Dashboard
   - 📁 Proof Files
   - 🧪 WOW Audit

---

## 2️⃣ Navigate to QC Dashboard (30 seconds)

**Option A: From Sidebar Link (Fastest)**
- Sidebar toggle → Click "📊 [QC Dashboard](/operator_qc)"

**Option B: From Main Navigation**
- Sidebar → Click "🛡️ Operator QC" in the radio buttons
- Or just scroll to that option in the nav

---

## 3️⃣ Explore the 5 QC Tabs (60 seconds)

### Tab 1: 📋 **Internal QA Panel**
- **Quick QA button** → Run immediate validation on current report
- **Full WOW Audit button** → Run 12-pack system health check
- **Open Proof Folder button** → Open `.aicmo/proof/` in file explorer
- **Learning controls** → Toggle ML features on/off for testing

### Tab 2: 📁 **Proof File Viewer**
- Dropdown at top → Select recent proof file
- Displays: Metadata, brief snapshot (JSON), full report markdown
- **Download button** → Save proof as .md file
- **Copy button** → Copy markdown to clipboard for sharing

### Tab 3: ⚙️ **Quality Gate Inspector**
- Report length validation
- Forbidden pattern detection (checks for placeholder text, incomplete sections)
- Learnability score
- Side-by-side sanitization diff viewer

### Tab 4: 🧪 **WOW Pack Health Monitor**
- Table of all 12 AI/Humanization packages
- Status: ✅ OK or ❌ BAD
- Last run timestamp
- "Run Audit Again" button

### Tab 5: 🎛️ **Report Generation Controls**
- `enable_learning` toggle
- `force_skip_learning` toggle
- `show_raw_output` toggle
- `show_sanitization_diff` toggle
- Useful for debugging learning pipeline issues

---

## 🎯 Common Tasks

### Task: Verify a report was properly generated
1. Generate report in "Workshop" tab
2. Go to "Final Output" tab
3. Scroll down to "Proof File Info (Operator Mode)" expander
4. ✅ Should show green checkmark + file path

### Task: Review all proof files
1. Navigate to "🛡️ Operator QC"
2. Click "Proof File Viewer" tab
3. Dropdown shows all recent proofs
4. Click file → preview markdown

### Task: Check system health
1. Navigate to "🛡️ Operator QC"
2. Click "WOW Pack Health Monitor" tab
3. Look at status column (✅ all green = healthy)
4. If any ❌, click "Run Audit Again" to diagnose

### Task: Debug why a report isn't "learnable"
1. Generate report
2. Navigate to "🛡️ Operator QC"
3. Click "Quality Gate Inspector" tab
4. Look at "Learnability" section
5. See rejection reasons if learnable = false
6. Review "Sanitization Diff" to see what was changed

---

## ✨ Pro Tips

**Tip 1: Proof Files Are Your Audit Trail**
- Every report generates a proof file automatically
- Stored in `.aicmo/proof/<timestamp>/`
- Shows exactly what was generated, when, and for whom
- Great for compliance/auditing

**Tip 2: Quick QA Before Export**
- Always run "Quick QA" before exporting to client
- Check: Report length, forbidden patterns, learnability
- Takes 2-3 seconds

**Tip 3: WOW Health Check Weekly**
- Run "Full WOW Audit" once a week to ensure system health
- All 12 packages should be ✅ OK
- If any ❌ BAD, the system needs maintenance

**Tip 4: Use Proof Files for Training**
- New operators? Show them proof files
- They see: Brand → Brief → Placeholders → Final Report flow
- Perfect for onboarding

**Tip 5: Copy Proofs to Slack**
- Use "Copy to Clipboard" button
- Paste in Slack for peer review
- Helps catch issues early

---

## 🔧 Troubleshooting

**Q: "🛡️ Operator QC" tab not appearing**
- A: Refresh the page (Ctrl+R or Cmd+R)
- If still not there: Check with admin that operator_qc is deployed

**Q: Proof files not being generated**
- A: Check "Proof File Info" expander in "Final Output" tab
- If empty: Report generation may have failed
- See admin for debug logs

**Q: "Quality gates failed" error**
- A: This is expected! It means:
  - Report length too short or too long
  - Forbidden patterns detected (incomplete sections)
  - Report not ready for learning
- Fix the issues and try again

**Q: WOW Audit shows ❌ BAD status**
- A: This means a package is not functioning
- Click "Run Audit Again" to get detailed error
- Contact admin with error details

---

## 📊 Understanding the UI

### Color Coding
- 🟢 **Green** = OK, healthy, passed
- 🔴 **Red** = Error, failed, not healthy
- 🟡 **Yellow** = Warning, needs attention
- 🔵 **Blue** = Info, neutral status

### Icons
- ✅ = Success, check passed
- ❌ = Error, check failed
- ℹ️ = Information
- ⚠️ = Warning
- 📋 = Document/Report
- 📁 = Folder/Directory
- 🧪 = Test/Audit
- 🛡️ = Operator/Security
- ⚙️ = Configuration/Settings
- 🎛️ = Controls
- 📊 = Dashboard/Analytics

---

## 📞 Getting Help

**In Dashboard:**
- Hover over any metric for help text
- Click "Settings & Diagnostics" → "Ping backend /health" to test connectivity

**For Operators:**
- Ask Slack channel `#aicmo-operators`
- Check wiki: OPERATOR_QC_QUICK_REFERENCE.md

**For Admins/Developers:**
- See full technical docs: OPERATOR_QC_TECHNICAL_SUMMARY.md
- Review implementation: OPERATOR_QC_INTERFACE_COMPLETE.md
- Deployment guide: OPERATOR_QC_DEPLOYMENT_GUIDE.md

---

**🎉 You're ready! Open AICMO Dashboard → Enable Operator Mode → Navigate to QC Tab**

