# PART 1 & PART 2: QUICK REFERENCE

## PART 1: WOW System (Full Decks Only)

### How It Works

```
Client Request → Backend sees wow_enabled=true, wow_package_key="strategy_campaign_standard"
              ↓
            build_wow_report() gets the full 121-line deck template
              ↓
            Renders all 44 section placeholders with actual content
              ↓
            Returns full strategic deck (never a short fallback)
```

### Available WOW Packages

| Package | Sections | Lines | Use Case |
|---------|----------|-------|----------|
| `quick_social_basic` | 10 | 63 | Quick social content plan |
| `strategy_campaign_standard` | 17 | 121 | Full campaign strategy |
| `full_funnel_growth_suite` | 21 | 130 | Complete growth funnel |
| `launch_gtm_pack` | 18 | 90 | Product launch GTM |
| `brand_turnaround_lab` | 18 | 89 | Brand repositioning |
| `retention_crm_booster` | 14 | 71 | Retention & CRM strategy |
| `performance_audit_revamp` | 15 | 68 | Performance audit |

### API Usage

```bash
curl -X POST http://localhost:8000/aicmo/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brief": { "brand_name": "...", ... },
    "wow_enabled": true,
    "wow_package_key": "strategy_campaign_standard"
  }'
```

### What You Get

- Full deck with all sections and headings
- All section placeholders filled with content
- No short fallbacks, ever
- If template missing: empty string (fail-safe)

### No More...

❌ Hidden defaults like "agency_strategy_default"  
❌ Short "Diwali-style" mini decks  
❌ Implicit fallbacks when template missing  
❌ Unpredictable output structures  

---

## PART 2: PDF Export (Valid Bytes)

### How It Works

```
Browser → Streamlit "Download PDF" button
       ↓
Sends request to backend: POST /aicmo/export/pdf
       ↓
Backend generates PDF bytes (reportlab)
       ↓
Returns StreamingResponse (media_type="application/pdf")
       ↓
Streamlit receives resp.content (raw bytes)
       ↓
Browser downloads valid PDF file
       ↓
✅ Opens in any PDF reader (no "Failed to load PDF" errors)
```

### API Usage

```bash
# Simple markdown → PDF
curl -X POST http://localhost:8000/aicmo/export/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# My Report\n\nContent here..."
  }' \
  -o report.pdf

# Verify it's a real PDF
file report.pdf
# Output: PDF document, version 1.3...
```

### What You Get

- Real PDF bytes (not text, not base64)
- Valid PDF header: `%PDF-1.3`
- Proper content-type: `application/pdf`
- Proper attachment header for download
- Clear error messages on failure

### No More...

❌ "Failed to load PDF document" errors  
❌ Text files masquerading as PDFs  
❌ Binary data that browsers can't read  
❌ Silent failures with no error info  

---

## TESTING BOTH PARTS

### Part 1: WOW System

```bash
# Verify templates are clean
python3 -c "from aicmo.presets.wow_templates import WOW_TEMPLATES; print(len(WOW_TEMPLATES), 'templates')"
# Expected: 7 templates

# Check no fallback logic
grep "agency_strategy_default" aicmo/agency/baseline.py
# Expected: (no output)

# Test generation
curl -X POST http://localhost:8000/aicmo/generate \
  -H "Content-Type: application/json" \
  -d '{"brief": {...}, "wow_enabled": true, "wow_package_key": "strategy_campaign_standard"}' \
  | grep "wow_markdown"
# Expected: long markdown with multiple headings
```

### Part 2: PDF Export

```bash
# Generate a test PDF
curl -X POST http://localhost:8000/aicmo/export/pdf \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# Test\n\nContent"}' \
  -o /tmp/test.pdf

# Verify file
file /tmp/test.pdf
# Expected: PDF document, version 1.3...

# Check header
head -c 4 /tmp/test.pdf
# Expected: %PDF
```

---

## TROUBLESHOOTING

### Part 1: WOW Not Working

**Problem:** Getting empty or short WOW output  
**Solution:** Check that `wow_package_key` matches exactly:
```python
from aicmo.presets.wow_rules import get_wow_rule
rule = get_wow_rule("your_package_key")
if rule:
    print(f"Found: {len(rule['sections'])} sections")
else:
    print("Package not found!")
```

**Problem:** Template has missing placeholders  
**Solution:** Check WOW_TEMPLATES has the key:
```python
from aicmo.presets.wow_templates import WOW_TEMPLATES
if "your_key" in WOW_TEMPLATES:
    print("Template exists")
```

### Part 2: PDF Not Downloading

**Problem:** Browser shows "Failed to load PDF"  
**Check:** Is backend returning 200?
```bash
curl -v http://localhost:8000/aicmo/export/pdf -d '...'
# Look for: HTTP/1.1 200 OK
```

**Check:** Does response have PDF header?
```bash
curl http://localhost:8000/aicmo/export/pdf -d '...' | xxd | head
# Look for: 25 50 44 46 (which is "%PDF")
```

**Check:** Is Streamlit using resp.content?
```python
# Lines 985–1074 in streamlit_pages/aicmo_operator.py should show:
pdf_bytes = resp.content  # ← This is correct
# NOT:
# pdf_bytes = resp.text   # ← This would be wrong
```

---

## FILES YOU NEED TO KNOW

| File | Purpose | Status |
|------|---------|--------|
| `aicmo/presets/wow_templates.py` | All WOW deck templates | 7 templates, clean |
| `aicmo/presets/wow_rules.py` | Package → section mapping | Section-based |
| `aicmo/agency/baseline.py` | Agency report generation | No fallback logic |
| `backend/main.py` | PDF export endpoint | Returns StreamingResponse |
| `backend/pdf_utils.py` | PDF generation | Returns bytes |
| `streamlit_pages/aicmo_operator.py` | Streamlit UI | Uses resp.content |

---

## KEY TAKEAWAYS

### Part 1
✅ WOW templates are **pack-specific only**  
✅ No hidden defaults or fallbacks  
✅ Section-based rules ensure predictability  
✅ Missing template → empty string (fail-safe)  

### Part 2
✅ PDF export returns **real bytes**  
✅ Streamlit uses `resp.content` (not `resp.text`)  
✅ Status codes are checked  
✅ PDF header is validated  
✅ Errors show clear messages  

---

## NEXT STEPS

- ✅ Part 1 & Part 2 complete
- Deploy to staging/production
- Monitor PDF downloads (should be 100% success)
- Monitor WOW generation (should always use full deck)

