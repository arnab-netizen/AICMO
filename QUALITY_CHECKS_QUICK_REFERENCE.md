# Content Quality & Genericity Checks - Quick Reference

## 🚀 Quick Start

### Run with Quality Checks
```bash
python -m aicmo.self_test.cli --quality --full
```

### Direct Module Usage
```python
from aicmo.self_test.quality_checkers import check_content_quality

# Single text
result = check_content_quality("Your content here")

# Multiple texts
result = check_content_quality(["Text 1", "Text 2", "Text 3"])

# Access results
print(result.genericity_score)           # 0.0 - 1.0
print(result.generic_phrases_found)      # List of phrases
print(result.placeholders_found)         # List of placeholders
print(result.overall_quality_assessment) # excellent/good/fair/poor
print(result.warnings)                   # List of issues
```

## 📊 Key Metrics

| Metric | Range | Interpretation |
|--------|-------|-----------------|
| **Genericity Score** | 0.0 - 1.0 | 1.0 = original, 0 = very generic |
| **Lexical Diversity** | 0.0 - 1.0 | unique_words / total_words |
| **Quality Assessment** | excellent/good/fair/poor | Based on all metrics |
| **Placeholder Count** | 0+ | Number of template markers found |
| **Generic Phrases** | 0+ | Count of boilerplate phrases detected |

## 🎯 Quality Levels

### ✅ Excellent (0.85+)
- No placeholders
- Genericity score > 0.85
- Specific, original content
- Clear evidence and metrics

### ✅ Good (0.70-0.84)
- No placeholders
- Genericity score > 0.70
- Mostly original with some common phrases
- Contains supporting details

### ⚠️ Fair (0.50-0.69)
- Few or no placeholders
- Genericity score 0.50-0.70
- Multiple generic phrases
- Lacks specific metrics

### ❌ Poor (<0.50)
- Contains placeholders
- Genericity score < 0.50
- Highly generic content
- Missing concrete details

## 🔍 What Gets Detected

### Generic Phrases (40+ detected)
- Marketing boilerplate: "drive engagement", "leverage cutting-edge"
- Vague language: "synergy", "paradigm shift", "low-hanging fruit"
- Corporate jargon: "touch base", "circle back", "move the needle"

### Placeholders (3 patterns)
1. **Bracketed:** `[INSERT]`, `[TBD]`, `[FILL_IN]`
2. **Braced:** `{VARIABLE}`, `{YOUR_NAME}`
3. **Keywords:** "lorem ipsum", "placeholder", "todo", "fixme"

### Repeated Content
- Identifies sentences/phrases appearing 2+ times
- Helps spot copy-paste errors
- Detects redundant messaging

## 📝 Report Output

### Markdown Section
```markdown
## Content Quality & Genericity

**✅ feature_name**
- **Genericity Score:** 0.85/1.0
- **Lexical Diversity:** 45/120 unique words
- **Quality Assessment:** good
- **Status:** PASS
```

### HTML Report
- Same metrics displayed in formatted table
- Color-coded status indicators
- Interactive report with all features listed

## 🛠️ Configuration

### Enable/Disable Quality Checks
```python
from aicmo.self_test.orchestrator import SelfTestOrchestrator

# Enable in orchestrator
engine = SelfTestOrchestrator(
    enable_quality_checks=True  # Default: True
)

# Run self-test
engine.run_self_test(enable_quality_checks=True)
```

### CLI Flag
```bash
# Enable quality checks
python -m aicmo.self_test.cli --quality --full

# Without quality checks
python -m aicmo.self_test.cli --full
```

## 📂 Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `aicmo/self_test/quality_checkers.py` | Added dataclass fields, populated generic_phrases_found | Core quality assessment logic |
| `aicmo/self_test/orchestrator.py` | Added text extraction, quality check execution | Integration into test flow |
| `aicmo/self_test/reporting.py` | Added markdown section | Display in reports |

## ✅ Testing

```bash
# Run all tests
pytest tests/test_self_test_engine.py tests/test_self_test_engine_2_0.py -v

# Quality checker tests only
pytest tests/test_self_test_engine_2_0.py::TestQualityCheckers -v

# Reporting tests
pytest tests/test_self_test_engine.py::TestSelfTestReporting -v
```

**Current Status:** 66/66 tests passing (1 skipped)

## 🔗 Integration Points

1. **Orchestrator** → Runs quality checks after validation
2. **Reporting** → Displays results in markdown/HTML reports
3. **CLI** → `--quality` flag enables feature
4. **Models** → FeatureStatus includes quality_checks field

## 💡 Example Scenarios

### Scenario 1: Detecting Generic Content
```python
text = "In today's digital world, we leverage cutting-edge solutions."
result = check_content_quality(text)
# genericity_score: 0.67 (fair)
# generic_phrases_found: ['in today's digital world', 'leverage cutting-edge']
# assessment: 'fair' (contains generic phrases)
```

### Scenario 2: High Quality Content
```python
text = "Our algorithm achieved 23% YoY growth by implementing the new caching layer."
result = check_content_quality(text)
# genericity_score: 1.0 (excellent)
# generic_phrases_found: [] (none detected)
# assessment: 'excellent' (original with metrics)
```

### Scenario 3: Incomplete Content with Placeholders
```python
text = "Our system [INSERT FEATURE] provides [TBD] benefits."
result = check_content_quality(text)
# is_valid: False (placeholders found)
# placeholders_found: ['[INSERT FEATURE]', '[TBD]']
# assessment: 'poor' (incomplete)
```

## 📊 Report Examples

### Summary Statistics
```
✅ Features Passed: 28
❌ Features Failed: 4
Quality checks: enabled
```

### Per-Feature Assessment
```
**✅ persona_generator**
- Genericity Score: 1.00/1.0
- Lexical Diversity: 45/87 unique words
- Quality Assessment: excellent
- Status: PASS
```

### Issues Detected
```
**⚠️ marketing_copy**
- Placeholders Found: 2
- Generic Phrases: 4 instances
- Warnings:
  - Found 2 placeholder(s)
  - Content has moderate generic phrases
  - Found 1 repeated phrase(s)
```

## 🎓 Best Practices

1. **Aim for 0.80+ genericity score** - Indicates original, specific content
2. **Eliminate all placeholders** - Complete all TODO items before deployment
3. **Use concrete metrics** - "23% increase" not "significant improvement"
4. **Maintain vocabulary diversity** - Avoid repeating same terms
5. **Support claims with evidence** - Back assertions with numbers/data

## 🚦 When to Investigate

- ⚠️ Genericity < 0.70: Content may need rewriting
- ⚠️ Placeholders found: Incomplete sections need attention
- ⚠️ Repeated phrases: Check for copy-paste errors
- ⚠️ Low lexical diversity: Vary vocabulary to improve readability

## 📚 Related Documentation

- Full implementation details: `QUALITY_CHECKS_IMPLEMENTATION_SUMMARY.md`
- Test coverage: `tests/test_self_test_engine_2_0.py::TestQualityCheckers`
- Reporting: `aicmo/self_test/reporting.py` lines 161-203

---

**Last Updated:** December 11, 2025  
**Status:** ✅ Production Ready
