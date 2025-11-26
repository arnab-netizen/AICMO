# AICMO Operator QC – Proof-Driven QA Interface

**Date:** November 26, 2025  
**Status:** ✅ **PRODUCTION READY**  
**Purpose:** Transform AICMO into a transparent, auditable system where every report is backed by proof

---

## Overview

The **Operator QC Interface** provides agency-grade report lifecycle tracking with four integrated modules:

1. **Internal QA Panel** – Control center for audits, learning, and quality gates
2. **Proof File Viewer** – One-click inspection of report generation artifacts
3. **Quality Gate Inspector** – Live quality checks and problem highlighting
4. **WOW Pack Health Monitor** – Continuous health dashboard for all 12 WOW packages

### Key Features

✅ **Transparency** – Operators see exactly how reports are constructed  
✅ **Auditability** – Every report has a complete proof file (black box flight recorder)  
✅ **Safety** – Learning only happens on verified clean outputs  
✅ **Quality Control** – Diagnose and repair issues in seconds  
✅ **Scalability** – Easy to proof 100s of client outputs  
✅ **Compliance** – Enterprise-grade audit trail for disputes/rollback  

---

## Architecture

### File Structure

```
streamlit_pages/
├── operator_qc.py          # Main QC interface (5 tabs)
├── proof_utils.py          # Proof file utilities
└── aicmo_operator.py       # Main dashboard (modified with QC toggle)

.aicmo/
├── proof/
│   ├── operator/           # Per-report proof files
│   │   ├── launch_gtm_pack_20251126_161234.md
│   │   ├── quick_social_basic_20251126_161500.md
│   │   └── ...
│   └── wow_end_to_end/     # Audit test proof files (from audit script)
│       ├── launch_gtm_pack.md
│       ├── quick_social_basic.md
│       └── ... (12 packs total)
```

### Data Flow

```
Report Generated
    ↓
Proof File Created (.aicmo/proof/operator/<id>.md)
    ↓
Contains:
  - Brief metadata
  - Placeholder injection table
  - Quality gate results
  - Sanitization diff
  - Full sanitized report
    ↓
Operator Mode: View in UI
  - Quality Gate Inspector
  - Proof File Viewer
  - WOW Pack Health Monitor
```

---

## Module Details

### 1️⃣ Internal QA Panel

**Purpose:** Control center for operators

**Components:**

#### A. Status Summary
```
Total Packs: 12
✅ OK: 12
❌ BAD: 0
```

#### B. Control Buttons
- **▶️ Run Quick QA** – Validate brief, check quality gates, scan patterns
- **🧪 Run Full WOW Audit** – Execute `scripts/dev/aicmo_wow_end_to_end_check.py`
- **📁 Open Proof Folder** – Navigate to proof file directory

#### C. Learning Controls
```
☑ Enable Learning for This Report Only
☑ Force Skip Learning
☑ Show Raw Model Output
☑ Show Sanitization Diff
```

**Example Usage:**

1. Operator generates a report
2. Clicks "Run Quick QA" to verify
3. Proof file automatically created
4. Quality results displayed
5. Learning control allows override per-report

---

### 2️⃣ Proof File Viewer

**Purpose:** One-click inspection of report generation artifacts

**What's Included:**

```markdown
# AICMO Proof File Report

Report ID: launch_gtm_pack_20251126_161234
Generated: 2025-11-26 16:12:34
Package: launch_gtm_pack

## Executive Summary
- Brand: Pure Botanicals
- Industry: Organic Skincare
- Geography: Mumbai, India
- Report Length: 12,841 characters
- Learnable: ✅ Yes

## Brief Metadata
(Complete JSON dump of input brief)

## Quality Gate Results
✅ Learnability: Eligible for Learning
✅ No forbidden patterns
✅ All checks passed

## Placeholder Usage
| Placeholder | Status |
|---|---|
| {{brand_name}} | Filled: Pure Botanicals |
| {{industry}} | Filled: Organic Skincare |
| ... | ... |

## Sanitization Report
Original: 13,200 chars
Sanitized: 12,841 chars
Removed: 359 chars (internal markers, placeholders)

## Final Report (Sanitized)
(Complete sanitized report ready for client)

## System Metadata
- Proof File Version: 1.0
- Generated: 2025-11-26T16:12:34
```

**UI Actions:**
- **👁️ View Full Content** – Expand full proof file
- **⬇️ Download** – Save as markdown
- **📋 Copy to Clipboard** – For quick sharing

---

### 3️⃣ Quality Gate Inspector

**Purpose:** Live quality checks highlighting problems

**Checks Displayed:**

```
Learnability:
✅ Eligible for Learning

Report Length:
✅ OK (12,841 chars, minimum: 500)

Forbidden Pattern Scan:
✅ No [This section was missing]
✅ No {brand_name} placeholders
✅ No unfilled {{variables}}
✅ No 'your industry' or generics
✅ No 'Morgan Lee' B2B bleed-over
✅ No Python error markers
✅ No AttributeError strings
✅ No Traceback leakage

Brief Integrity:
✅ brand_name: Pure Botanicals
✅ industry: Organic Skincare
✅ geography: Mumbai, India
✅ audience: Women 22-40, skincare-aware
✅ goals: Launch + GTM + brand equity

Generator Integrity:
✅ No generator exceptions caught
✅ All section generators completed
✅ Placeholder injection completed
```

**Problem Highlighting:**

If a check fails:
```
❌ Placeholder Leak: '{{offer_headline}}' found in final output
❌ Error Marker: '[Error generating messaging_framework]' detected
❌ Brief Issue: Missing 'industry' field
```

---

### 4️⃣ WOW Pack Health Monitor

**Purpose:** Continuous health dashboard for all 12 packages

**Display Format:**

```
Total Packs: 12
Healthy ✅: 12
Issues ❌: 0

Pack Name                       Status     Size
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
quick_social_basic              ✅ OK      1.3 KB
strategy_campaign_standard      ✅ OK      1.7 KB
full_funnel_growth_suite        ✅ OK      2.4 KB
launch_gtm_pack                 ✅ OK      1.2 KB
brand_turnaround_lab            ✅ OK      1.5 KB
retention_crm_booster           ✅ OK      0.8 KB
performance_audit_revamp        ✅ OK      0.7 KB
strategy_campaign_basic         ✅ OK      1.4 KB
strategy_campaign_premium       ✅ OK      2.5 KB
strategy_campaign_enterprise    ✅ OK      3.2 KB
pr_reputation_pack              ✅ OK      1.0 KB
always_on_content_engine        ✅ OK      1.1 KB
```

**Controls:**
- **🔄 Run Audit Again** – Re-run full WOW E2E test
- Click pack row to view proof file

---

### 5️⃣ Advanced Features (Optional)

#### A. Sanitization Diff Viewer

Shows exactly what was removed:

```
Raw Output:
─────────────────────────────────────
[Error generating messaging_framework]
{{brand_name}} – {{product_name}}
This section was missing.

Sanitized Output:
─────────────────────────────────────
Pure Botanicals – Organic Skincare
This report is production-ready.
```

#### B. Placeholder Table

Verify all placeholders filled before delivery:

```
| Placeholder | Value | Status |
|---|---|---|
| {{brand_name}} | Pure Botanicals | ✅ Filled |
| {{industry}} | Organic Skincare | ✅ Filled |
| {{geography}} | Mumbai, India | ✅ Filled |
| {{target_audience}} | Women 22-40... | ✅ Filled |
```

#### C. Regenerate Section Tool

Re-run a single section:

```
Select section: messaging_framework
[🔄 Regenerate This Section]
```

---

## Integration with Main Dashboard

### Toggle in Sidebar

```python
# In streamlit_pages/aicmo_operator.py

with st.sidebar:
    operator_mode = st.toggle("🛡️ Operator Mode (QC)", value=False)
    if operator_mode:
        st.caption("✅ Internal QA tools enabled")
        st.markdown("""
        **Quick Links:**
        - 📊 [QC Dashboard](/operator_qc)
        - 📁 [Proof Files](.aicmo/proof/)
        - 🧪 [WOW Audit](scripts/dev/...)
        """)
```

### Auto-Proof File Generation

Every report automatically generates a proof file:

```python
# In render_final_output_tab()

if st.session_state.get("final_report"):
    from streamlit_pages.proof_utils import generate_proof_file
    
    brief_dict = build_client_brief_payload()
    package_key = st.session_state.get("selected_package", "unknown")
    
    proof_path = generate_proof_file(
        report_markdown=st.session_state["final_report"],
        brief_dict=brief_dict,
        package_key=package_key,
    )
    st.session_state["last_proof_file"] = str(proof_path)
```

---

## Files Created/Modified

### New Files

| File | Purpose | Lines |
|------|---------|-------|
| `streamlit_pages/operator_qc.py` | Main QC interface with 5 tabs | 800+ |
| `streamlit_pages/proof_utils.py` | Proof file utilities & ProofFileManager class | 250+ |

### Modified Files

| File | Change | Impact |
|------|--------|--------|
| `streamlit_pages/aicmo_operator.py` | Added Operator Mode toggle + proof file generation | Automatic proof tracking |

---

## Usage Examples

### Scenario 1: Generate a Report with Proof

1. Operator fills in client brief
2. Selects package: "Launch & GTM Pack"
3. Clicks "Generate draft report"
4. Report generated and proof file created automatically
5. In Final Output tab, sees "📋 Proof File Info (Operator Mode)"
6. Proof file contains complete generation history

### Scenario 2: Investigate a Problem Report

1. Operator notices report quality issue
2. Opens Operator QC dashboard
3. Goes to "Quality Gates" tab
4. Sees exactly which check failed
5. Clicks "Proof Files" tab to view complete generation artifacts
6. Opens proof file, examines brief, placeholders, sanitization diff
7. Can regenerate specific section or re-run audit

### Scenario 3: Audit All WOW Packages

1. Operator toggles "Operator Mode ON"
2. Navigates to Operator QC dashboard
3. Goes to "Pack Health" tab
4. Sees all 12 packages with status
5. Clicks "🔄 Run Audit Again"
6. Audit runs, proof files updated
7. Dashboard refreshes with latest status
8. All 12 show ✅ OK

---

## Technical Details

### Proof File Structure

```
ProofFileManager
├── generate()              # Create new proof file
├── list_all()             # Get all proof files with timestamps
├── get_latest()           # Get most recent proof file
├── get_by_id()            # Retrieve specific proof by ID
└── _build_proof_markdown() # Format proof content
```

### Quality Gate Integration

```python
# From backend/quality_gates.py
is_report_learnable(report_markdown, brief_brand_name)
  → Returns: (is_learnable: bool, rejection_reasons: List[str])

sanitize_final_report_text(text)
  → Returns: Cleaned text (all internal markers removed)
```

---

## Benefits

### For Operators
✅ See exactly how each report is constructed  
✅ Diagnose problems in seconds  
✅ Verify quality before sending to client  
✅ Audit trail for disputes/rollback  
✅ Control learning per-report  

### For QA
✅ Compliance-ready audit trail  
✅ Pattern detection across all reports  
✅ Black box flight recorder for every report  
✅ Easy regression testing  
✅ Learning data quality validation  

### For Clients
✅ Transparent, verifiable reports  
✅ No generic/error leakage  
✅ Proper geographic grounding  
✅ Professional lifecycle tracking  
✅ Enterprise-grade audit trail  

---

## Deployment Checklist

- [x] `operator_qc.py` created with 5 tabs
- [x] `proof_utils.py` created with ProofFileManager
- [x] Integration toggle added to `aicmo_operator.py`
- [x] Auto-proof file generation in final output
- [x] Quality gate inspector with live checks
- [x] WOW pack health monitor dashboard
- [x] Advanced features (sanitization diff, placeholder table)
- [x] All files compile without errors
- [x] Documentation complete

---

## Future Enhancements (Optional)

1. **S3 Integration** – Auto-upload proof files to S3 for backup
2. **Analytics Dashboard** – Track patterns across all generated reports
3. **Diff Viewer** – Visual diff between draft and final versions
4. **Rollback Tool** – Restore previous report versions
5. **Learning Analytics** – Show impact of learned blocks on report quality
6. **Webhook Alerts** – Notify on quality gate failures

---

## Quick Reference

### Access Operator QC
```
Main Dashboard → Toggle "🛡️ Operator Mode" in sidebar → "📊 QC Dashboard"
```

### View Latest Proof File
```
Operator QC → "Proof Files" tab → Select from dropdown → View Full Content
```

### Run WOW Audit
```
Operator QC → "QA Panel" tab → "🧪 Run Full WOW Audit" button
```

### Check Pack Health
```
Operator QC → "Pack Health" tab → See all 12 packs with status
```

### View Quality Checks
```
Operator QC → "Quality Gates" tab → See pass/fail for all checks
```

---

**Status:** ✅ Production Ready  
**Last Updated:** November 26, 2025  
**Version:** 1.0
