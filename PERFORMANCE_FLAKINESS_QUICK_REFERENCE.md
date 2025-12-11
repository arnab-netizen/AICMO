# Performance & Flakiness Tracking - Quick Reference Guide

## Quick Start

### Enable Deterministic Mode
Run tests with fixed seeds and stub outputs (no LLM calls):
```bash
python -m aicmo.self_test.cli --deterministic
```

**What it does:**
- Sets `random.seed(42)` for reproducible randomness
- Sets `np.random.seed(42)` for NumPy reproducibility
- Forces `AICMO_USE_LLM=0` to use stub generators instead of LLM
- Records feature runtimes
- Marks report with "Mode: Deterministic ✅"

---

### Check for Flaky Features
Run 3 iterations to detect non-deterministic behavior:
```bash
python -m aicmo.self_test.cli --flakiness-check
```

**What it does:**
- Runs tests 3 times in deterministic mode
- Tracks feature signatures: `(status, error_count, warning_count)`
- Compares signatures across runs
- Reports features that changed between runs
- Shows results in "Performance & Flakiness" section

---

### View Performance Metrics
Any test run shows feature runtimes in the report:
```bash
python -m aicmo.self_test.cli --deterministic
# → Look for "## Performance & Flakiness" section
# → Shows all features with execution times
```

---

## Available Flags

| Flag | Purpose | Usage |
|------|---------|-------|
| `--deterministic` | Enable deterministic/reproducible mode | `--deterministic` |
| `--flakiness-check` | Run 3 iterations to detect flaky features | `--flakiness-check` |
| `-v` / `--verbose` | Show detailed output | `-v` |
| `--output DIR` | Specify report output directory | `--output /path/to/dir` |

---

## Understanding the Report

### Performance & Flakiness Section

**Example 1: With deterministic mode**
```markdown
## Performance & Flakiness

**Feature Runtimes:**

- persona_generator: 0.123s
- social_calendar_generator: 0.045s
- messaging_pillars_generator: 0.089s
...

**Flakiness Check:** No inconsistencies detected ✅
```

**Example 2: With flaky feature detected**
```markdown
**Flakiness Detected:** ⚠️
- output_formatter: Inconsistent across runs (3 different outputs)
```

### Report Header Indicator

**When deterministic mode is used:**
```markdown
**Mode:** Deterministic ✅ (stub outputs, fixed seeds)
```

---

## How It Works

### Performance Tracking

1. Each feature test is wrapped with `time.perf_counter()`
2. Elapsed time calculated after test completes
3. Stored in feature result as `runtime_seconds`
4. Report displays all features sorted by duration (longest first)

### Deterministic Mode

1. When `--deterministic` flag used:
   ```
   ✓ random.seed(42) called
   ✓ np.random.seed(42) called
   ✓ AICMO_USE_LLM="0" environment variable set
   ✓ Forces use of stub generators (no LLM calls)
   ```

2. Result is fully reproducible
3. Same input → always same output
4. Good for CI/CD pipelines and testing

### Flakiness Detection

1. Runs test 3 times in deterministic mode
2. For each feature, creates signature: `(status.value, errors_count, warnings_count)`
3. Compares signatures across 3 runs
4. If signature changes, feature is "flaky"
5. Indicates non-deterministic behavior

---

## Use Cases

### Testing in CI/CD Pipeline
```bash
# Use deterministic mode for consistent, reproducible results
python -m aicmo.self_test.cli --deterministic --output ./reports
```

### Find Non-Deterministic Bugs
```bash
# Run flakiness check to detect inconsistent features
python -m aicmo.self_test.cli --flakiness-check
# Look for features in "Flakiness Detected" section
```

### Performance Profiling
```bash
# Run any test and check runtime metrics
python -m aicmo.self_test.cli --deterministic

# Compare runtimes from multiple runs
python -m aicmo.self_test.cli --deterministic --output ./run1
python -m aicmo.self_test.cli --deterministic --output ./run2
# Compare AICMO_SELF_TEST_REPORT.md files
```

### Local Development
```bash
# Run tests with detailed output
python -m aicmo.self_test.cli --deterministic -v

# Check for regressions
python -m aicmo.self_test.cli --flakiness-check
```

---

## Common Combinations

### Fast, reproducible test run
```bash
python -m aicmo.self_test.cli --deterministic
```

### Fast test with detailed output
```bash
python -m aicmo.self_test.cli --deterministic -v
```

### Full test with flakiness detection
```bash
python -m aicmo.self_test.cli --full --flakiness-check
```

### With custom output directory
```bash
python -m aicmo.self_test.cli --deterministic --output ./my_reports
```

---

## Understanding Results

### Runtime Values

**Interpretation:**
- `< 0.1s` - Very fast (likely cached or minimal)
- `0.1s - 0.5s` - Normal (basic generator/packager)
- `> 1.0s` - Slow (complex processing, consider optimization)

**Example:**
```
persona_generator: 0.123s  ← Normal
output_formatter: 0.456s   ← Slightly slow
agency_processor: 0.001s   ← Cached/minimal
```

### Flakiness Status

**No inconsistencies detected ✅**
- All features produced same output across 3 runs
- Test is deterministic and stable

**Flakiness Detected:** ⚠️
- One or more features produced different outputs
- May indicate:
  - Non-deterministic randomness
  - External API calls
  - Timing-dependent behavior
  - Race conditions

---

## Technical Details

### Feature Signature (Flakiness Detection)

```python
signature = (
    feature.status.value,      # Status enum value (PASS, FAIL, etc.)
    len(feature.errors),        # Number of errors
    len(feature.warnings)       # Number of warnings
)
```

Two features are considered "the same" if all three values match across runs.

### Seed Values

- **Python randomness:** `random.seed(42)`
- **NumPy randomness:** `np.random.seed(42)`
- **LLM mode:** `AICMO_USE_LLM="0"` forces stubs

Seed value `42` was chosen arbitrarily; same value ensures reproducibility.

### Timing Precision

- Uses `time.perf_counter()` for nanosecond precision
- Measures total feature test duration (generators + packagers)
- Includes all processing, validation, and reporting
- Excludes report generation and I/O (only test execution)

---

## Troubleshooting

### Report doesn't show runtimes
**Solution:** Ensure you're using latest code with timing instrumentation
```bash
git pull  # Get latest version
python -m aicmo.self_test.cli --deterministic
```

### Flakiness check shows false positives
**Solution:** May indicate legitimate non-deterministic behavior. Check:
- Are you using external APIs without mocking?
- Does code use `time.time()` or other non-reproducible sources?
- Are there race conditions or threading issues?

### Deterministic mode still shows variations
**Solution:** Check:
- Is `AICMO_USE_LLM` already set in environment? (Takes precedence)
- Are generators using custom random sources?
- Are there external dependencies being called?

```bash
# Check environment variable
echo $AICMO_USE_LLM

# Run with verbose output to see what's happening
python -m aicmo.self_test.cli --deterministic -v
```

---

## Integration with Development Workflow

### Pre-commit Check
```bash
# Fast deterministic check before committing
python -m aicmo.self_test.cli --deterministic --output ./tmp

# Inspect report
cat ./tmp/AICMO_SELF_TEST_REPORT.md
```

### CI/CD Pipeline
```bash
# In GitHub Actions or similar
- name: Run AICMO Self-Tests (Deterministic)
  run: python -m aicmo.self_test.cli --deterministic --output ./reports

- name: Check for Flakiness
  run: python -m aicmo.self_test.cli --flakiness-check --output ./flakiness
```

### Performance Regression Testing
```bash
# Baseline run
python -m aicmo.self_test.cli --deterministic --output ./baseline

# After changes
python -m aicmo.self_test.cli --deterministic --output ./current

# Compare runtimes in both reports
diff baseline/AICMO_SELF_TEST_REPORT.md current/AICMO_SELF_TEST_REPORT.md
```

---

## Related Files

- **Implementation:** [aicmo/self_test/](aicmo/self_test/)
- **Tests:** [tests/test_self_test_engine.py](tests/test_self_test_engine.py)
- **Full Details:** [PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md](PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md)

---

## Support & Questions

For issues or questions about performance tracking:
1. Check [PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md](PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md) for detailed documentation
2. Review test cases in [tests/test_self_test_engine.py](tests/test_self_test_engine.py)
3. Check CLI help: `python -m aicmo.self_test.cli --help`
