# Self-Test Engine 2.0 - Implementation Guide

## Overview

Self-Test Engine 2.0 adds comprehensive coverage validation, layout checks, format validation, and content quality analysis to the existing Self-Test Engine v1.

## New Modules

### 1. `benchmarks_harvester.py`
**Purpose:** Discover and map benchmarks from `aicmo/learning/benchmarks/` to features.

**Key Functions:**
- `discover_all_benchmarks()` - Find all benchmark JSON files
- `map_benchmarks_to_features()` - Map benchmarks to known features
- `find_benchmark_validators()` - Locate validators enforcing benchmarks

**Current Status:**
- ✅ Benchmark discovery fully implemented
- ⚠️ No benchmarks directory currently exists (code ready, will detect 0 benchmarks)
- ⚠️ Validator detection is heuristic-based (works but may not catch all)

**Integration Points:**
- Call in orchestrator after discovery phase
- Results stored in `FeatureStatus.benchmark_coverage`

---

### 2. `layout_checkers.py`
**Purpose:** Validate structure and layout of client-facing outputs (HTML, PPTX, PDF).

**Key Functions:**
- `check_html_layout()` - Validate HTML structure, headings, sections
- `check_pptx_layout()` - Check slide count, titles, minimum requirements
- `check_pdf_layout()` - Check page count and first-page content

**Checklist per Modality:**
- **HTML:** ✅ heading order, ✅ section presence, ✅ title tag
- **PPTX:** ✅ slide count (min 3), ✅ slide titles, ✅ basic structure
- **PDF:** ⚠️ Only if PyPDF2 or pdfplumber installed (code ready, graceful fallback)

**Integration Points:**
- Call in packager tests when HTML/PPTX generated
- Results stored in `FeatureStatus.layout_checks`

---

### 3. `format_checkers.py`
**Purpose:** Validate text format, word counts, and structural completeness.

**Key Functions:**
- `check_text_format()` - Word counts against thresholds (summary, caption, etc.)
- `check_structure()` - Bullets, paragraphs, sections
- `validate_calendar_format()` - Social calendar entries
- `validate_list_completeness()` - Item counts and required fields

**Thresholds Implemented:**
| Field Type | Min Words | Max Words |
|-----------|-----------|-----------|
| summary | 30 | 200 |
| strategy | 50 | 500 |
| caption | 5 | 50 |
| insight | 15 | 100 |
| headline | 3 | 15 |
| bullet | 3 | 30 |

**Integration Points:**
- Call on generator outputs to check format
- Results stored in `FeatureStatus.format_checks`

---

### 4. `quality_checkers.py`
**Purpose:** Detect generic content, placeholders, and calculate quality metrics.

**Key Functions:**
- `check_content_quality()` - Genericity score, placeholder detection
- `check_placeholder_markers()` - Find [INSERT], {YOUR_NAME}, etc.
- `check_lexical_diversity()` - Unique word ratio
- `summarize_quality_metrics()` - Overall quality assessment (excellent/good/fair/poor)

**Generic Phrases Detected (26+):**
- "leverage cutting-edge solutions"
- "drive engagement and growth"
- "paradigm shift"
- "synergy"
- etc.

**Placeholder Patterns:**
- `[INSERT...]`, `[TBD]`, `[FILL...]`
- `{YOUR_NAME}`, `{BRAND}`
- `<<SOMETHING>>`

**Quality Score Components:**
- Originality (40%) - based on generic phrase ratio
- Diversity (20%) - lexical diversity ratio
- Completeness (30%) - presence of content
- No Placeholders (10%) - explicit placeholder detection

**Integration Points:**
- Call on all text outputs from generators
- Results stored in `FeatureStatus.quality_checks`
- Feature flag: `AICMO_SELF_TEST_ENABLE_QUALITY` (default: True)

---

### 5. `coverage_report.py`
**Purpose:** Generate coverage summary and recommendations.

**Key Functions:**
- `build_coverage_summary()` - Create coverage metrics
- `coverage_assessment()` - Analysis and recommendations

**Coverage Metrics:**
- Benchmark coverage: `enforced / mapped * 100%`
- Layout coverage: count of modalities checked (HTML, PPTX, PDF)
- Quality checks: enabled/disabled
- Format checks: enabled/disabled

**Overall Coverage Score:**
- 40% benchmarks enforced
- 30% layout checks
- 30% quality/format checks

**Integration Points:**
- Call after all features tested
- Stored in `SelfTestResult.coverage_info`

---

## Integration with Orchestrator

The orchestrator needs to:

1. **After generator execution:**
   ```python
   # Call format and quality checkers
   format_result = check_text_format(output)
   quality_result = check_content_quality(str(output))
   feature_status.format_checks = format_result
   feature_status.quality_checks = quality_result
   ```

2. **After packager execution (HTML/PPTX):**
   ```python
   # Check layouts
   if html_file:
       layout_result.html_valid = check_html_layout(file_path=html_file).is_valid
   if pptx_file:
       pptx_result = check_pptx_layout(pptx_file)
       layout_result.pptx_valid = pptx_result.is_valid
       layout_result.pptx_slide_count = pptx_result.slide_count
   ```

3. **After all features:**
   ```python
   # Build coverage summary
   coverage = build_coverage_summary(
       total_benchmarks=len(all_benchmarks),
       mapped_benchmarks=len(mapped),
       enforced_benchmarks=len(enforced),
       html_checked=html_layout_ran,
       pptx_checked=pptx_layout_ran,
       pdf_checked=pdf_layout_ran,
   )
   result.coverage_info = coverage
   ```

---

## Reporting Integration

The reports should include new sections:

### Markdown Report
```markdown
## Coverage Analysis

### Benchmarks
- Mapped: X / Y
- Enforced: A / B
- Unmapped: Z

### Layout Checks
- HTML: PASS/FAIL (X sections checked)
- PPTX: PASS/FAIL (X slides)
- PDF: NOT CHECKED (no PDF parser)

### Quality & Format
- Quality checks: enabled
- Format validation: enabled

### Coverage Summary
[detailed summary of what is and isn't covered]
```

### HTML Report
Similar structure with cleaner formatting.

---

## CLI Options (Future)

New flags for `python -m aicmo.self_test.cli`:

```bash
--quality / --no-quality          # Enable/disable quality checks
--layout / --no-layout            # Enable/disable layout checks
--benchmarks-only                 # Only check benchmarks
--coverage-report                 # Generate coverage assessment
--full                           # Run everything (default)
```

---

## Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Benchmarks discovery | ✅ Full | No benchmarks directory exists yet |
| Benchmarks mapping | ✅ Full | Heuristic + metadata-based |
| Validator detection | ⚠️ Heuristic | Catches most patterns |
| HTML layout checks | ✅ Full | Headings, sections, structure |
| PPTX layout checks | ✅ Full | Slides, titles, min requirements |
| PDF layout checks | ⚠️ Optional | Requires PyPDF2 or pdfplumber |
| Format validation | ✅ Full | Word counts, structure, calendar |
| Quality checks | ✅ Full | Genericity, placeholders, diversity |
| Coverage reporting | ✅ Full | Metrics and recommendations |
| Orchestrator integration | ❌ TODO | Needs wiring |
| Reporting integration | ❌ TODO | Needs new report sections |
| CLI options | ❌ TODO | Needs new flags |
| Tests | ❌ TODO | Needs 2.0-specific tests |

---

## Hard Evidence Philosophy

Every check in 2.0 is designed around hard evidence:

✅ **Counted:** word counts, slide counts, page counts
✅ **Parsed:** HTML structure, PPTX slides, PDF pages
✅ **Detected:** placeholder patterns, generic phrases, duplicates
✅ **Measured:** genericity score, diversity ratio, lexical richness

❌ **Never:** "AI feels this is bad" or unquantified claims
❌ **Never:** Assuming features are covered without explicit checks
❌ **Never:** Reporting coverage that isn't actually implemented

---

## Known Limitations

1. **Benchmarks:** Currently no benchmarks directory; code ready for when populated
2. **PDF checks:** Optional - requires additional dependencies
3. **Validator detection:** Heuristic-based, may not catch all patterns
4. **Quality checks:** Uses simple rules (generic phrases, lexical diversity) not LLM-based
5. **Layout checks:** Basic structure validation only, not pixel-perfect layout

---

## Next Steps (In Priority Order)

1. Integrate 2.0 modules into orchestrator.py
2. Add reporting sections to reporting.py
3. Add CLI options for 2.0 features
4. Create comprehensive tests in test_self_test_engine.py
5. Run full validation and gather coverage metrics
6. Populate benchmark directory (if using benchmarks)

---

## References

- **Models:** `aicmo/self_test/models.py` (2.0 dataclasses)
- **Discovery:** `aicmo/self_test/discovery.py`
- **Validators:** `aicmo/quality/validators.py`
- **Packagers:** `aicmo/delivery/output_packager.py`
