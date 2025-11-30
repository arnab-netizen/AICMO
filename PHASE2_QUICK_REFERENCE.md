# PHASE 2: BENCHMARK QUALITY VALIDATION - QUICK REFERENCE

**Last Updated**: 2025  
**For**: Developers using the AICMO benchmark validation system

---

## 🎯 ONE-MINUTE OVERVIEW

Phase 2 adds **content quality validation** on top of Phase 1's **structural validation**:

- **Phase 1**: ✅ Right sections in right order with content
- **Phase 2**: ✅ Content meets quality standards (word count, formatting, no clichés)

**Status**: Integrated into main flow, non-breaking, 26 tests passing

---

## 🚀 QUICK START

### Validate a Single Section

```python
from backend.validators.benchmark_validator import validate_section_against_benchmark

result = validate_section_against_benchmark(
    pack_key="quick_social_basic",
    section_id="overview",
    content=your_section_markdown
)

if result.status == "FAIL":
    for issue in result.issues:
        print(f"{issue.code}: {issue.message}")
```

### Validate Full Report

```python
from backend.validators.report_gate import validate_report_sections

sections = [
    {"id": "overview", "content": "..."},
    {"id": "audience_segments", "content": "..."}
]

result = validate_report_sections(
    pack_key="quick_social_basic",
    sections=sections
)

if result.status == "FAIL":
    print(result.get_error_summary())
```

---

## 📋 VALIDATION CHECKLIST

Each section is checked for:

- [ ] **Word count** in range (min_words to max_words)
- [ ] **Bullet points** in range (min_bullets to max_bullets)
- [ ] **Headings** in range (min_headings to max_headings)
- [ ] **Required headings** present (e.g., "Brand", "Industry")
- [ ] **Required phrases** present (e.g., "Brand:", "Primary Goal:")
- [ ] **Forbidden phrases** absent (e.g., "lorem ipsum", "[Brand]")
- [ ] **Forbidden patterns** not matched (e.g., clichés like "in today's digital age")
- [ ] **Repetition ratio** below threshold (unique content)
- [ ] **Sentence length** reasonable (avg words per sentence)
- [ ] **Format** matches expectation (markdown block/list/table)

---

## 📊 VALIDATION STATUSES

| Status | Meaning | Action |
|--------|---------|--------|
| `PASS` | All checks passed | ✅ Ship it |
| `PASS_WITH_WARNINGS` | Minor issues (warnings only) | ⚠️ Review, but OK to ship |
| `FAIL` | Critical issues (errors) | ❌ Fix before shipping |

---

## 🔧 COMMON ERROR CODES

| Code | Problem | Solution |
|------|---------|----------|
| `TOO_SHORT` | Below min word count | Add more content |
| `TOO_LONG` | Above max word count | Trim content |
| `TOO_FEW_BULLETS` | Not enough bullet points | Add bullet points |
| `MISSING_HEADING` | Required heading missing | Add heading (e.g., `### Brand`) |
| `MISSING_PHRASE` | Required text missing | Add exact phrase (e.g., "Brand:") |
| `FORBIDDEN_PHRASE` | Contains banned text | Remove/replace text |
| `FORBIDDEN_PATTERN` | Matches banned pattern | Rewrite to avoid cliché |
| `TOO_REPETITIVE` | Too many duplicate lines | Add variety |

**Full error code reference**: See `PHASE2_BENCHMARK_VALIDATION_COMPLETE.md`

---

## 📁 FILE LOCATIONS

```
Core Files:
  learning/benchmarks/section_benchmarks.*.json  - Benchmark definitions
  backend/utils/benchmark_loader.py              - Loads benchmarks
  backend/validators/benchmark_validator.py      - Section validation
  backend/validators/report_gate.py              - Report validation
  backend/main.py (line ~3277)                   - Integration point

Tests:
  backend/tests/test_benchmark_validation.py     - 26 tests

Docs:
  PHASE2_BENCHMARK_VALIDATION_COMPLETE.md        - Full documentation
  PHASE2_QUICK_REFERENCE.md                      - This file
```

---

## 🎨 BENCHMARK FILE STRUCTURE

Example: `learning/benchmarks/section_benchmarks.quick_social.json`

```json
{
  "pack_key": "quick_social_basic",
  "strict": true,
  "sections": {
    "overview": {
      "id": "overview",
      "min_words": 120,
      "max_words": 260,
      "min_bullets": 3,
      "max_bullets": 8,
      "required_headings": ["Brand", "Industry"],
      "required_substrings": ["Brand:", "Industry:"],
      "forbidden_substrings": ["lorem ipsum"],
      "forbidden_regex": ["(?i)in today's digital age"],
      "max_repeated_line_ratio": 0.3,
      "format": "markdown_block"
    }
  }
}
```

**Naming convention**: `section_benchmarks.<pack_prefix>.json`

---

## 🧪 TESTING

```bash
# Run benchmark tests
pytest backend/tests/test_benchmark_validation.py -v

# Run specific test
pytest backend/tests/test_benchmark_validation.py::test_validate_good_content -v

# Run with output
pytest backend/tests/test_benchmark_validation.py -v -s
```

**Current status**: 26 tests, 100% passing ✅

---

## 🔍 DEBUGGING VALIDATION ISSUES

### Check What's Wrong

```python
result = validate_section_against_benchmark(
    pack_key="quick_social_basic",
    section_id="overview",
    content=content
)

for issue in result.issues:
    print(f"[{issue.severity}] {issue.code}: {issue.message}")
```

### Check If Benchmark Exists

```python
from backend.utils.benchmark_loader import get_section_benchmark

benchmark = get_section_benchmark("quick_social_basic", "overview")
if benchmark:
    print(f"Min words: {benchmark['min_words']}")
    print(f"Max words: {benchmark['max_words']}")
else:
    print("No benchmark defined")
```

### Check Benchmark File Loading

```python
from backend.utils.benchmark_loader import load_benchmarks_for_pack

try:
    config = load_benchmarks_for_pack("quick_social_basic")
    print(f"✅ Loaded {len(config['sections'])} sections")
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## ⚙️ CONFIGURATION

### Strict Mode

```json
{
  "strict": true  // Fail if section benchmark missing
}
```

- **strict=true**: Missing benchmarks → FAIL
- **strict=false**: Missing benchmarks → PASS (graceful)

### Cache Settings

Benchmarks cached using `@lru_cache(maxsize=32)`:
- First load: ~5-10ms
- Cached: <1ms
- Can hold 32 pack benchmarks in memory

---

## 🚦 INTEGRATION STATUS

**Phase 2 is INTEGRATED** into `backend/main.py`:

```python
# Line ~3277 in backend/main.py
from backend.validators.report_gate import validate_report_sections

validation_result = validate_report_sections(
    pack_key=req.wow_package_key,
    sections=validation_sections
)

if validation_result.status == "FAIL":
    logger.warning(f"⚠️ Quality gate FAILED")
```

**Current behavior**: Non-breaking (logs warnings, doesn't fail generation)

---

## 📦 AVAILABLE BENCHMARKS

| Pack Key | Sections | Status |
|----------|----------|--------|
| `quick_social_basic` | 10 | ✅ Complete |
| `strategy_campaign_standard` | 16 | ⏳ TODO |
| `strategy_campaign_enterprise` | 39 | ⏳ TODO |
| `full_funnel_basic` | 23 | ⏳ TODO |
| `persona_profile_deep` | 10 | ⏳ TODO |

**To add new pack**: Create `section_benchmarks.<pack_prefix>.json`

---

## 🎯 QUICK EXAMPLES

### Example 1: Valid Overview Section

```markdown
### Brand
Brand: Example Coffee Co.

### Industry
Industry: Food & Beverage

### Primary Goal
Primary Goal: Increase foot traffic by 20%

- Strategic social media approach
- Data-driven content planning
- Performance tracking system
- Community engagement tactics

This comprehensive plan provides strategies for achieving 
business objectives through coordinated activities across
digital platforms. The approach aligns with brand values
and resonates with target audiences through authentic
messaging and consistent execution.
```

**Result**: ✅ PASS

### Example 2: Invalid Overview Section

```markdown
**Brand:** [Insert Brand Name]

Lorem ipsum dolor sit amet...
```

**Result**: ❌ FAIL
- `TOO_SHORT`: 8 words, minimum is 120
- `FORBIDDEN_PHRASE`: "[Insert Brand Name]"
- `FORBIDDEN_PHRASE`: "lorem ipsum"
- `TOO_FEW_BULLETS`: 0 bullets, minimum is 3
- `MISSING_HEADING`: "Brand" not found

---

## 💡 BEST PRACTICES

### DO ✅

- Use markdown `#` headings for structure
- Include exact required phrases (with colons)
- Stay within word count ranges
- Add bullet points for key information
- Write varied, unique content
- Keep sentences reasonably short

### DON'T ❌

- Use placeholder text ("lorem ipsum", "[Brand]")
- Copy-paste the same line repeatedly
- Use overused clichés ("in today's digital age")
- Write walls of text without bullets/headings
- Skip required information
- Exceed word limits

---

## 🆘 TROUBLESHOOTING

### Problem: "BenchmarkNotFoundError"

**Cause**: No benchmark file for pack  
**Solution**: Create `learning/benchmarks/section_benchmarks.<pack>.json`

### Problem: "NO_SECTION_CONFIG error"

**Cause**: Benchmark file exists but missing section  
**Solution**: Add section to benchmark JSON

### Problem: Tests failing with TOO_SHORT

**Cause**: Test content below min_words  
**Solution**: Add more words to test content

### Problem: Validation taking too long

**Cause**: Large sections with repetition analysis  
**Solution**: Cached after first call, should be <2ms per section

---

## 📚 SEE ALSO

- **Full Documentation**: `PHASE2_BENCHMARK_VALIDATION_COMPLETE.md`
- **Phase 1 Reference**: `PHASE1_QUICK_REFERENCE.md`
- **Test Examples**: `backend/tests/test_benchmark_validation.py`
- **Benchmark Schema**: `learning/benchmarks/section_benchmarks.schema.json`

---

## 🎉 QUICK WINS

```python
# Load benchmark
from backend.utils.benchmark_loader import load_benchmarks_for_pack
config = load_benchmarks_for_pack("quick_social_basic")

# Validate section
from backend.validators.benchmark_validator import validate_section_against_benchmark
result = validate_section_against_benchmark(
    pack_key="quick_social_basic",
    section_id="overview",
    content=content
)

# Check status
if result.is_ok():
    print("✅ Good to go!")
```

**That's it!** Validation is now protecting quality at scale.
