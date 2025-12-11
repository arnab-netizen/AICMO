# Layout Checkers - Quick Start Guide

## Overview
The Self-Test Engine 2.0 now includes **real, evidence-based layout validation** for HTML, PPTX, and PDF outputs. This guide covers how to use the layout checkers.

## Running Layout Checks

### Command Line
```bash
# Full mode with layout checks
python -m aicmo.self_test.cli --full --layout

# Quick mode with layout checks
python -m aicmo.self_test.cli --quick --layout
```

### Programmatically
```python
from aicmo.self_test.orchestrator import SelfTestOrchestrator

orchestrator = SelfTestOrchestrator()
result = orchestrator.run_self_test(
    quick_mode=False,
    enable_layout_checks=True
)

# Access results
for feature in result.features:
    if feature.layout_checks:
        print(f"{feature.name}:")
        print(f"  HTML valid: {feature.layout_checks.html_valid}")
        print(f"  PPTX valid: {feature.layout_checks.pptx_valid}")
        print(f"  PDF valid:  {feature.layout_checks.pdf_valid}")
```

## What Gets Validated

### HTML Output
- **Presence** of AICMO required sections:
  - Project Overview
  - Strategy
  - Content Calendar
  - Deliverables
- **Heading count** and extraction
- **Heading order** (sections should appear in logical sequence)

**Example Report:**
```
### HTML Summary Validation

**✅ generate_html_summary**

- **Headings Found:** 5
- **Has Overview Section:** True
- **Has Deliverables Section:** True
- **Heading Order Valid:** True
```

### PPTX Output
- **Slide count** (minimum 3 slides)
- **Required titles** presence (Strategy, Content Calendar, Metrics)
- **Title extraction** from slides

**Example Report:**
```
### PPTX Deck Validation

**✅ generate_full_deck_pptx**

- **Total Slides:** 3
- **Required Titles Found:** strategy, calendar
```

### PDF Output
- **Currently:** Returns explicit "not implemented" message
- **Why:** PDF parsing libraries (PyPDF2, pdfplumber) not in requirements
- **Honest reporting:** No fake metrics or assumed values

**Example Report:**
```
### PDF Validation

**⚠️ generate_strategy_pdf**

- **Status:** PDF layout check not implemented
- **Note:** PyPDF2 or pdfplumber required for PDF parsing
```

## Using Layout Checkers Directly

### HTML Validation
```python
from aicmo.self_test.layout_checkers import check_html_layout

# Check from file
result = check_html_layout(file_path="/path/to/file.html")

# Check from content
result = check_html_layout(html_content="<html>...</html>")

# Result contains:
# - is_valid: bool
# - found_headings: List[str]
# - missing_sections: List[str]
# - heading_order_ok: bool
# - details: Dict with additional info
```

### PPTX Validation
```python
from aicmo.self_test.layout_checkers import check_pptx_layout

result = check_pptx_layout("/path/to/file.pptx")

# Result contains:
# - is_valid: bool
# - slide_count: int
# - found_titles: List[str]
# - missing_titles: List[str]
# - details: Dict with additional info
```

### PDF Validation
```python
from aicmo.self_test.layout_checkers import check_pdf_layout

result = check_pdf_layout("/path/to/file.pdf")

# Result contains:
# - is_valid: bool (False if parser not available)
# - page_count: int
# - details: Dict explaining "not implemented" if parser unavailable
```

## Example: Full Validation Suite

```python
from aicmo.self_test.layout_checkers import validate_layout_suite

# Check all outputs in a directory
results = validate_layout_suite(
    output_dir="/path/to/outputs",
    project_name="CloudSync AI"
)

# Results organized by format
print(f"HTML: {results.html_valid}")
print(f"PPTX: {results.pptx_valid}")
print(f"PDF:  {results.pdf_valid}")

# Access detailed info
print(results.html_details)
print(results.pptx_details)
print(results.pdf_details)
```

## Report Format

Layout Checks section appears in the markdown report between:
```
[Benchmark Coverage section above]
        ↓
## Layout Checks
        ↓
[Feature Testing Results section below]
```

## Return Values

### Success Cases
- **is_valid = True**: All checks passed
- Concrete metrics provided (e.g., "Headings Found: 5")
- Specific findings listed (e.g., "Found Titles: strategy, calendar")

### Failure Cases  
- **is_valid = False**: Checks failed or unavailable
- Clear reason provided in `details`
- No pretended metrics - honest reporting

### Example Results

**HTML Success:**
```
is_valid: True
found_headings: ['Project Overview', 'Strategy', 'Deliverables', 'Conclusion']
missing_sections: []
heading_order_ok: True
```

**PPTX Success:**
```
is_valid: True
slide_count: 3
found_titles: ['Strategy', 'Content Calendar']
missing_titles: ['Metrics']
```

**PDF (Not Implemented):**
```
is_valid: False
page_count: 0
details: {
    'reason': 'PDF layout check not implemented',
    'message': 'PyPDF2 or pdfplumber required for PDF parsing'
}
```

## Configuration

### Enable/Disable
```python
# Enable layout checks
orchestrator = SelfTestOrchestrator()
result = orchestrator.run_self_test(enable_layout_checks=True)

# Disable (default is enabled)
result = orchestrator.run_self_test(enable_layout_checks=False)
```

### CLI
```bash
# Enable layout checks (explicit)
python -m aicmo.self_test.cli --full --layout

# Run without layout checks
python -m aicmo.self_test.cli --full  # layout checks enabled by default

# Disable via environment variable (if supported)
export AICMO_DISABLE_LAYOUT_CHECKS=1
python -m aicmo.self_test.cli --full
```

## Troubleshooting

### "Headings Found: 0"
- Check HTML structure
- Verify headers use `<h1>` through `<h6>` tags
- Check for CSS that hides headers

### "PPTX layout check failed"
- Ensure `python-pptx` is installed: `pip install python-pptx`
- Or gracefully handles absence (returns is_valid=None)

### "PDF layout check not implemented"
- Expected behavior - PDF parser not available
- To add PDF checking: `pip install PyPDF2` or `pip install pdfplumber`
- Then update layout_checkers.py to use the library

### Results Not Appearing in Report
- Ensure `enable_layout_checks=True`
- Check that packagers are actually running (check logs)
- Verify output files are generated before layout checks

## Examples in Tests

See `/tests/test_self_test_engine_2_0.py` for:
- `test_check_html_layout_aicmo_sections` - Basic HTML validation
- `test_check_html_layout_heading_order` - Heading order validation
- `test_check_pptx_layout_slide_count` - PPTX slide validation
- `test_check_pptx_layout_title_detection` - PPTX title extraction

## Design Principles

✅ **Real Parsing** - Actually reads and parses files
✅ **Concrete Metrics** - Reports actual counts, not assumptions
✅ **Honest Limitations** - Explicit "not implemented" when unavailable
✅ **No Pretending** - Never fabricates validation data
✅ **Graceful Degradation** - System works even if some checks unavailable

---

**For more details**, see [LAYOUT_CHECKERS_IMPLEMENTATION_COMPLETE.md](LAYOUT_CHECKERS_IMPLEMENTATION_COMPLETE.md)
