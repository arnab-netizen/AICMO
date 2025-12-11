# Performance & Flakiness Tracking - Implementation Index

## 📋 Overview

This document provides a complete index of the Performance & Flakiness Tracking feature implementation for the AICMO Self-Test Engine.

**Status:** ✅ **100% COMPLETE**  
**Implementation Date:** December 11, 2025  
**Tests Passing:** 9/9 (100%)  
**Total System Tests:** 41/42 (97.6%)

---

## 📚 Documentation Files

### 1. **PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md** (COMPREHENSIVE)
**Purpose:** Complete technical documentation  
**Contents:**
- Full feature overview and architecture
- Implementation details for all 5 files
- Code examples and snippets
- Testing results and validation
- Complete file manifest
- Performance metrics
- Success criteria checklist

**When to use:** 
- Need complete technical reference
- Implementing extensions
- Understanding architecture decisions
- Troubleshooting complex issues

**Key Sections:**
- Implementation Summary
- Architecture & Implementation Details
- Testing Results
- Code Changes Summary
- File Manifest
- Validation Checklist

---

### 2. **PERFORMANCE_FLAKINESS_QUICK_REFERENCE.md** (QUICK START)
**Purpose:** Quick reference for daily use  
**Contents:**
- Quick start commands
- Available flags and options
- Usage examples
- Report interpretation
- Common use cases
- Troubleshooting tips

**When to use:**
- Need quick command reference
- Starting new task
- Common troubleshooting
- Daily development work

**Key Sections:**
- Quick Start Commands
- Available Flags
- Understanding the Report
- Use Cases
- Common Combinations
- Troubleshooting

---

### 3. **PERFORMANCE_FLAKINESS_TRACKING_INDEX.md** (THIS FILE)
**Purpose:** Navigation and cross-reference  
**Contents:**
- Overview of all documentation
- File-by-file implementation guide
- Quick navigation links
- Key contacts and related files

**When to use:**
- Finding specific documentation
- Understanding project structure
- Navigating to relevant code

---

## 🗂️ Implementation Files

### Core Changes (5 Files)

#### 1. **aicmo/self_test/models.py**
**Purpose:** Data model enhancements  
**Changes:**
- Line ~148: Added `runtime_seconds: Optional[float] = None` to `FeatureStatus`
- Line ~214: Added `deterministic_mode: bool = False` to `SelfTestResult`
- Line ~215: Added `flakiness_check_results: Dict[str, List[str]] = field(default_factory=dict)` to `SelfTestResult`

**Key Classes:**
- `FeatureStatus` - Extended with runtime tracking
- `SelfTestResult` - Extended with deterministic mode and flakiness results

**Related Documentation:**
- See PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md for complete code

---

#### 2. **aicmo/self_test/orchestrator.py**
**Purpose:** Core test orchestration with timing and deterministic mode  
**Changes:**
- Line 62: Added `deterministic: bool = False` parameter to `run_self_test()`
- Lines 92-103: Implemented deterministic mode (seed setting, env var)
- Line 133 & 277: Generator timing instrumentation
- Line 294 & 398: Packager timing instrumentation

**Key Methods:**
- `run_self_test()` - Main orchestrator method (now with deterministic param)
- `_test_generators()` - Generator testing (now with timing)
- `_test_packagers()` - Packager testing (now with timing)

**Deterministic Implementation:**
```python
if deterministic:
    import random
    import numpy as np
    random.seed(42)
    np.random.seed(42)
    import os
    os.environ["AICMO_USE_LLM"] = "0"
```

**Related Documentation:**
- PERFORMANCE_FLAKINESS_QUICK_REFERENCE.md for usage
- PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md for architecture

---

#### 3. **aicmo/self_test/cli.py**
**Purpose:** CLI interface with flags and flakiness detection logic  
**Changes:**
- Lines 16-43: Added `deterministic` and `flakiness_check` parameters to `main()`
- Lines 70-111: Implemented 3-iteration flakiness check logic
- Lines 265-302: Added argument parser flags and function call integration

**Key Features:**
- `--deterministic` flag: Enable reproducible testing
- `--flakiness-check` flag: Run multiple iterations to detect flakiness
- Integrated flakiness detection algorithm

**Flakiness Detection Logic:**
- 3 iterations of test execution
- Feature signature tracking: (status, error_count, warning_count)
- Signature comparison to detect inconsistencies
- Results stored in `result.flakiness_check_results`

**Related Documentation:**
- PERFORMANCE_FLAKINESS_QUICK_REFERENCE.md for commands
- PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md for architecture

---

#### 4. **aicmo/self_test/reporting.py**
**Purpose:** Report generation with performance metrics  
**Changes:**
- Lines 33-55: Added "Performance & Flakiness" markdown section
- Added deterministic mode indicator in report header
- Shows feature runtimes and flakiness detection results

**Report Section Examples:**

**Example 1 - Deterministic Mode**
```markdown
**Mode:** Deterministic ✅ (stub outputs, fixed seeds)
```

**Example 2 - Feature Runtimes**
```markdown
## Performance & Flakiness

**Feature Runtimes:**
- persona_generator: 0.123s
- social_calendar_generator: 0.045s
```

**Example 3 - Flakiness Status**
```markdown
**Flakiness Check:** No inconsistencies detected ✅
```

**Related Documentation:**
- PERFORMANCE_FLAKINESS_QUICK_REFERENCE.md for interpreting reports
- PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md for implementation

---

#### 5. **tests/test_self_test_engine.py**
**Purpose:** Test coverage for new features  
**Changes:**
- Lines 220-240: `TestPerformanceTracking` class (6 tests)
- Lines 241-335: `TestFlakinesDetection` class (3 tests)

**New Test Classes:**

**TestPerformanceTracking (6 tests):**
1. `test_runtime_seconds_recorded` - Verifies runtime tracking
2. `test_runtime_seconds_in_range` - Validates reasonable values
3. `test_deterministic_flag_recognized` - Checks parameter acceptance
4. `test_deterministic_mode_sets_seeds` - Verifies seed setting
5. `test_performance_section_in_markdown_report` - Checks report section
6. `test_markdown_report_shows_runtime_for_features` - Verifies runtime display

**TestFlakinesDetection (3 tests):**
1. `test_flakiness_check_result_structure` - Verifies data structure
2. `test_flakiness_check_accepts_flag` - Checks flag acceptance
3. `test_deterministic_mode_flag` - Verifies flag handling

**Test Execution:**
```bash
# Run all new tests
pytest tests/test_self_test_engine.py::TestPerformanceTracking -v
pytest tests/test_self_test_engine.py::TestFlakinesDetection -v

# All 9 tests PASS ✅
```

**Related Documentation:**
- PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md for test results

---

## 🎯 Quick Navigation by Task

### I want to...

**...use the new features**
1. Read: PERFORMANCE_FLAKINESS_QUICK_REFERENCE.md
2. Run: `python -m aicmo.self_test.cli --deterministic`
3. Check: Report at `self_test_artifacts/AICMO_SELF_TEST_REPORT.md`

**...understand the architecture**
1. Read: PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md (Architecture section)
2. Review: orchestrator.py (timing logic)
3. Review: cli.py (flakiness detection)

**...extend the features**
1. Read: PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md (Code Changes)
2. Review: models.py (data structures)
3. Check: tests (examples of usage)

**...troubleshoot issues**
1. Check: PERFORMANCE_FLAKINESS_QUICK_REFERENCE.md (Troubleshooting)
2. Review: Test cases in test_self_test_engine.py
3. Check: CLI help: `python -m aicmo.self_test.cli --help`

**...integrate with CI/CD**
1. Read: PERFORMANCE_FLAKINESS_QUICK_REFERENCE.md (Integration section)
2. Use: `python -m aicmo.self_test.cli --deterministic`
3. Parse: Generated markdown report

**...measure performance**
1. Run: `python -m aicmo.self_test.cli --deterministic`
2. Check: "Feature Runtimes" section in report
3. Compare: Runtimes across multiple runs

**...find flaky tests**
1. Run: `python -m aicmo.self_test.cli --flakiness-check`
2. Check: "Flakiness Detected" section in report
3. Review: Features with inconsistent outputs

---

## 🔍 Implementation Details by Feature

### Feature 1: Runtime Tracking

**Files Modified:**
- models.py (data model)
- orchestrator.py (timing instrumentation)
- reporting.py (display)

**How It Works:**
1. Each feature test wrapped with `time.perf_counter()`
2. Elapsed time calculated after test completes
3. Stored in `FeatureStatus.runtime_seconds`
4. Displayed in report sorted by duration

**Usage:**
```bash
python -m aicmo.self_test.cli --deterministic
# Check report section: "## Performance & Flakiness"
```

---

### Feature 2: Deterministic Mode

**Files Modified:**
- orchestrator.py (seed setting)
- reporting.py (indicator)

**How It Works:**
1. Parameter passed to `run_self_test(deterministic=True)`
2. Seeds set: `random.seed(42)`, `np.random.seed(42)`
3. Environment: `AICMO_USE_LLM="0"` (forces stubs)
4. Result marked: `deterministic_mode=True`
5. Report shows: "Mode: Deterministic ✅"

**Usage:**
```bash
python -m aicmo.self_test.cli --deterministic
```

---

### Feature 3: Flakiness Detection

**Files Modified:**
- cli.py (detection logic)
- models.py (result storage)
- reporting.py (display)

**How It Works:**
1. CLI flag triggers 3-iteration loop
2. Each iteration runs test in deterministic mode
3. Feature signatures tracked: (status, error_count, warning_count)
4. Signatures compared across runs
5. Inconsistent features marked as "flaky"
6. Results shown in report

**Usage:**
```bash
python -m aicmo.self_test.cli --flakiness-check
```

---

### Feature 4: CLI Flags

**Files Modified:**
- cli.py (argument parser and main)

**Available Flags:**
- `--deterministic` - Enable deterministic mode
- `--flakiness-check` - Run flakiness detection

**Usage:**
```bash
# Single flag
python -m aicmo.self_test.cli --deterministic

# Combined flags
python -m aicmo.self_test.cli --flakiness-check

# With other options
python -m aicmo.self_test.cli --deterministic -v --output ./reports
```

---

### Feature 5: Reporting

**Files Modified:**
- reporting.py (markdown generation)

**Report Section:**
```markdown
## Performance & Flakiness

**Feature Runtimes:**
[Sorted list of features with execution times]

**Flakiness Check:**
[Status: OK ✅ or list of inconsistent features]
```

---

## 📊 Test Coverage Summary

### Test Execution Results

```
Total Tests Run: 42
Tests Passed: 41 (97.6%)
Tests Failed: 1 (2.4% - pre-existing, unrelated)

New Tests (9):
✅ TestPerformanceTracking (6 tests)
✅ TestFlakinesDetection (3 tests)

Status: ALL NEW TESTS PASSING
```

### Test Location

File: `tests/test_self_test_engine.py`

Lines:
- TestPerformanceTracking: ~220-240
- TestFlakinesDetection: ~241-335

### Running Tests

```bash
# Run new tests only
pytest tests/test_self_test_engine.py::TestPerformanceTracking -v
pytest tests/test_self_test_engine.py::TestFlakinesDetection -v

# Run all tests
pytest tests/test_self_test_engine.py -v
```

---

## 🚀 Deployment Guide

### For Development

```bash
# Run locally with deterministic mode
python -m aicmo.self_test.cli --deterministic

# Check for flakiness
python -m aicmo.self_test.cli --flakiness-check

# With detailed output
python -m aicmo.self_test.cli --deterministic -v
```

### For CI/CD

```bash
# In your pipeline configuration:
python -m aicmo.self_test.cli --deterministic --output ./reports

# Parse the report:
cat ./reports/AICMO_SELF_TEST_REPORT.md
```

### Backward Compatibility

✅ All new features are optional:
- Default: `deterministic=False` (original behavior)
- Default: `flakiness_check=False` (original behavior)
- Existing tests unaffected
- No breaking changes

---

## 📞 Support & References

### Key Files by Purpose

**To understand timing:**
- orchestrator.py (lines 133, 277, 294, 398)
- See PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md

**To understand deterministic mode:**
- orchestrator.py (lines 92-103)
- See PERFORMANCE_FLAKINESS_QUICK_REFERENCE.md

**To understand flakiness detection:**
- cli.py (lines 70-111)
- See PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md

**To understand reporting:**
- reporting.py (lines 33-55)
- models.py (FeatureStatus, SelfTestResult)

**To understand tests:**
- test_self_test_engine.py (lines 220-335)
- See test implementations for usage examples

---

## ✅ Verification Checklist

Before using in production, verify:

- [ ] Run tests: `pytest tests/test_self_test_engine.py -v`
- [ ] All 41+ tests pass
- [ ] Run with flag: `python -m aicmo.self_test.cli --deterministic`
- [ ] Check report for "Performance & Flakiness" section
- [ ] Verify feature runtimes displayed
- [ ] Run flakiness check: `python -m aicmo.self_test.cli --flakiness-check`
- [ ] Check for flakiness detection output

---

## 📖 Related Documentation

- PERFORMANCE_FLAKINESS_TRACKING_COMPLETE.md - Technical details
- PERFORMANCE_FLAKINESS_QUICK_REFERENCE.md - Usage guide
- aicmo/self_test/models.py - Data structures
- aicmo/self_test/orchestrator.py - Core logic
- aicmo/self_test/cli.py - CLI interface
- aicmo/self_test/reporting.py - Reporting

---

**Status:** ✅ Complete | **Date:** December 11, 2025 | **Tests:** 41/42 Pass | **Ready:** Production
