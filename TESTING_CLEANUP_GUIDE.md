# Quick Testing & Cleanup Guide

## After Deploying the Fixes

### Step 1: Test in Streamlit
```bash
# Start the AICMO application
streamlit run streamlit_app.py
```

### Step 2: Generate a Test Report
1. Go to the Operator page
2. Select: "Strategy + Campaign Pack (Standard)"
3. Fill in a test brief
4. Click "Generate Report"

### Step 3: Verify Full-Form Output
Check the backend logs for output like:
```
## 1. Campaign Overview
[content here]

## 2. Campaign Objectives
[content here]

## 3. Core Campaign Idea
[content here]

... continuing through all 17 sections ...

## 17. Final Summary
[content here]
```

**Expected:** Output should be ~15,000+ characters (was ~3,000-5,000 before)

### Step 4: Count Sections
Search logs for all section headings. You should find exactly 17:
```
grep -c "^## [0-9]" output.log
# Should return: 17
```

### Step 5: Remove Temporary Guard (Once Confirmed)

Once you've verified the output is full-form with all 17 sections:

**File:** `backend/main.py` (lines 1226-1231)

**DELETE THIS BLOCK:**
```python
# 🔧 TEMPORARY TROUBLESHOOTING: Force WOW bypass for strategy_campaign_standard
# to verify if the underlying generator produces a long-form report
package_name = payload.get("package_name")
if package_name == "Strategy + Campaign Pack (Standard)":
    # TEMP: Disable WOW to see raw generator output
    wow_enabled = False
    wow_package_key = None
    logger.info("🔧 [TEMPORARY] WOW disabled for strategy_campaign_standard - testing raw output")
```

### Step 6: Re-run Pre-Commit Checks
```bash
# Commit the cleanup
git add -A
git commit -m "🧹 Remove temporary WOW bypass guard after verification

The strategy_campaign_standard package now produces full 17-section reports.
Temporary WOW bypass guard no longer needed. WOW template wrapping re-enabled
for professional output formatting."
```

### Step 7: Test WOW Template Wrapping
After removing the guard, verify that:
- Output still shows all 17 sections
- WOW template properly wraps the content
- Formatting looks professional

### Step 8: Test PDF Export
```bash
# Use the PDF export endpoint
curl -X POST http://localhost:8000/aicmo/export/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "package_name": "Strategy + Campaign Pack (Standard)",
    "client_brief": {
      "brand_name": "Test Brand",
      "industry": "Technology",
      "objectives": "Growth"
    },
    "services": {},
    "wow_enabled": true,
    "wow_package_key": "strategy_campaign_standard"
  }' \
  -o test_report.pdf
```

Verify the PDF contains:
- Professional cover page
- All 17 sections with proper content
- Proper typography and formatting
- Page breaks between sections

---

## Troubleshooting

### Output Still Short (~3-5k chars)?
1. Check if bypass guard is still active
2. Verify `_generate_section_content()` is being called
3. Check backend logs for errors
4. Verify extra_sections dict is populated

### Missing Sections in WOW Output?
1. Verify wow_templates.py has all 17 sections
2. Check that placeholder names match section_ids
3. Verify extra_sections dict has all 17 keys
4. Check template substitution is working

### PDF Export Issues?
1. Verify pdf_renderer.py is importable
2. Check that WeasyPrint is installed
3. Verify HTML template can render all 17 sections
4. Check PDF header validation

---

## Files to Know About

- **Main Implementation:** `backend/main.py` (lines 304-397, 713-730)
- **WOW Template:** `aicmo/presets/wow_templates.py` (lines 80-200)
- **Package Preset:** `aicmo/presets/package_presets.py` (verified, no changes needed)
- **Bypass Guard Location:** `backend/main.py` (lines 1226-1231, TEMPORARY)
- **Documentation:** `STRATEGY_CAMPAIGN_STANDARD_FIXES_COMPLETE.md`

---

## Success Criteria

✅ Raw output: ~15-20k+ characters (3-5x larger than before)
✅ Sections visible: All 17 sections present
✅ WOW template: All sections with proper content
✅ PDF export: All 17 sections rendered professionally
✅ No errors in logs
✅ User experience significantly improved

---

## Questions?

Refer to: `STRATEGY_CAMPAIGN_STANDARD_FIXES_COMPLETE.md` for detailed documentation
