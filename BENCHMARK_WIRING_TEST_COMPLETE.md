# Benchmark Wiring Test Implementation Complete

## Overview

Created a comprehensive test suite that verifies the wiring between:
- **SECTION_GENERATORS** in `backend/main.py` (80+ section generators)
- **PACKAGE_PRESETS** in `aicmo/presets/package_presets.py` (10 packs)
- **Benchmark files** in `learning/benchmarks/*.json` (5 files)

## File Created

**`backend/tests/test_benchmarks_wiring.py`** - Single test file (650+ lines)

## Test Suite Features

### 1. Core Wiring Tests

#### `test_all_pack_sections_have_benchmarks`
- Scans ALL pack presets and ALL sections
- Verifies each section has a benchmark entry
- **FAILS LOUDLY** with detailed report showing:
  - Which packs are missing benchmarks
  - Which sections within each pack lack definitions
  - Clear action items for fixing

#### `test_all_benchmarks_target_existing_sections`
- Scans ALL benchmark JSON files
- Verifies each benchmark section_id exists in SECTION_GENERATORS
- **FAILS LOUDLY** if benchmarks reference non-existent generators
- Shows available generators to help fix mismatches

#### `test_benchmark_file_naming_convention`
- Verifies benchmark files follow naming convention
- Ensures files can be loaded by `load_benchmarks_for_pack()`
- Checks for required fields: `pack_key`, `sections`, `strict`
- Detects naming mismatches between files and pack keys

#### `test_no_duplicate_sections_in_benchmarks`
- Checks for consistency within benchmark files
- Ensures section keys match their internal `id` fields
- Prevents logical inconsistencies

### 2. Coverage Tests

#### `test_every_pack_has_at_least_one_benchmark_file`
- High-level check for pack coverage
- Lists all packs without benchmark files
- Provides pack details (label, section count)

#### `test_benchmark_coverage_statistics`
- Informational test (always passes)
- Generates detailed coverage report showing:
  - Overall benchmark coverage percentage
  - Per-pack breakdown with missing sections
  - Visual indicators (✅ for 100%, ⚠️ for incomplete)

## Current Test Results

### Failing Tests (As Expected)

The tests are **working correctly** by detecting real issues:

1. **126 missing benchmarks** across 9 packs
   - `brand_turnaround_lab`: 14 missing (0% coverage)
   - `full_funnel_growth_suite`: 13 missing (43.5% coverage)
   - `launch_gtm_pack`: 13 missing (0% coverage)
   - `performance_audit_revamp`: 9 missing (43.8% coverage)
   - `retention_crm_booster`: 14 missing (0% coverage)
   - `strategy_campaign_basic`: 4 missing (33.3% coverage)
   - `strategy_campaign_enterprise`: 28 missing (28.2% coverage)
   - `strategy_campaign_premium`: 21 missing (25.0% coverage)
   - `strategy_campaign_standard`: 10 missing (37.5% coverage)

2. **2 invalid section references** in `performance_audit.json`
   - `kpi_plan` - no matching generator
   - `quick_wins` - no matching generator

3. **1 file naming mismatch**
   - `section_benchmarks.crm_retention.json` cannot be loaded by `retention_crm_booster` pack

4. **3 packs missing benchmark files entirely**
   - `brand_turnaround_lab`
   - `launch_gtm_pack`
   - `retention_crm_booster`

### Passing Tests

- ✅ `test_no_duplicate_sections_in_benchmarks` - No consistency issues found
- ✅ `test_benchmark_coverage_statistics` - Report generated (informational)

## Overall Coverage

**Current State**: 53/179 sections (29.6% coverage)

**Fully Covered Packs**:
- ✅ `quick_social_basic` - 10/10 sections (100%)

**Partially Covered Packs**:
- ⚠️ All other packs have significant gaps

## How to Use

### Run All Tests
```bash
pytest backend/tests/test_benchmarks_wiring.py -v
```

### Run Specific Test
```bash
pytest backend/tests/test_benchmarks_wiring.py::TestBenchmarksWiring::test_all_pack_sections_have_benchmarks -v
```

### See Coverage Report
```bash
pytest backend/tests/test_benchmarks_wiring.py::TestBenchmarksComprehensiveCoverage::test_benchmark_coverage_statistics -v -s
```

### Quick Check (Quiet Mode)
```bash
pytest backend/tests/test_benchmarks_wiring.py -q
```

## Error Messages

The tests provide **detailed, actionable error messages**:

### Example: Missing Benchmarks
```
================================================================================
BENCHMARK WIRING FAILURE: Missing Benchmarks Detected
================================================================================

Found 126 sections without benchmarks:

📦 Pack: full_funnel_growth_suite
   Missing 13 benchmark(s):
   • Section 'overview'
     Reason: Benchmark returned None (section not defined in benchmark file)
   • Section 'competitor_analysis'
     Reason: Benchmark returned None (section not defined in benchmark file)
   ...

================================================================================
ACTION REQUIRED:
================================================================================
1. Identify which benchmark file should contain these sections
2. Add benchmark entries with required fields
3. Verify section_id matches SECTION_GENERATORS key
================================================================================
```

### Example: Invalid References
```
================================================================================
BENCHMARK WIRING FAILURE: Invalid Section References
================================================================================

Found 2 benchmark entries that reference non-existent sections:

📄 File: section_benchmarks.performance_audit.json
   • Section ID: 'kpi_plan'
     Pack: performance_audit_revamp
     Label: KPI Quality Check
     Issue: No matching generator in SECTION_GENERATORS

================================================================================
ACTION REQUIRED:
================================================================================
1. Check if the section_id is misspelled
2. Available generators in SECTION_GENERATORS:
   - account_audit
   - campaign_level_findings
   - conversion_audit
   ... and 62 more
================================================================================
```

## Implementation Details

### Reuses Existing Infrastructure
- `backend.utils.benchmark_loader` functions
- `backend.main.SECTION_GENERATORS` registry
- `aicmo.presets.package_presets.PACKAGE_PRESETS` configuration

### No Hardcoding
- Discovers packs dynamically from PACKAGE_PRESETS
- Discovers sections dynamically from pack configurations
- Discovers benchmark files by scanning directory
- Always uses actual config, never hardcoded values

### Comprehensive Validation
- Checks both directions: packs→benchmarks AND benchmarks→generators
- Validates file structure and naming conventions
- Provides coverage statistics for visibility
- Groups errors by pack for easier debugging

## Benefits

1. **Prevents Silent Failures**: Tests fail loudly if configuration is incorrect
2. **Early Detection**: Catch mismatches before deployment
3. **Clear Guidance**: Detailed error messages with action items
4. **Full Coverage**: Scans all packs, all sections, all benchmarks
5. **Non-Destructive**: Only detects issues, never modifies code
6. **CI/CD Ready**: Can be integrated into automated testing pipelines

## Next Steps

To achieve 100% coverage:

1. **Fix invalid references** in `performance_audit.json`:
   - Change `kpi_plan` to existing generator (e.g., `kpi_reset_plan`)
   - Change `quick_wins` to existing generator (e.g., `optimization_opportunities`)

2. **Fix file naming** for `crm_retention`:
   - Rename `section_benchmarks.crm_retention.json` to `section_benchmarks.retention_crm.json`

3. **Create missing benchmark files**:
   - `section_benchmarks.brand_turnaround.json`
   - `section_benchmarks.launch_gtm.json`

4. **Add missing section benchmarks** to existing files:
   - 126 sections need benchmark definitions across 9 packs

## Testing Philosophy

This test suite follows the principle: **"Test the wiring, not the implementation"**

- ❌ Does NOT modify production code
- ❌ Does NOT auto-fix issues
- ❌ Does NOT assume optionality
- ✅ DOES detect all mismatches
- ✅ DOES provide clear guidance
- ✅ DOES fail with detailed context

## Success Criteria Met

✅ Single test file created: `backend/tests/test_benchmarks_wiring.py`  
✅ No other files modified  
✅ Tests fail loudly with clear messages  
✅ Reuses existing benchmark loader infrastructure  
✅ Discovers all packs and sections dynamically  
✅ Validates both directions (packs→benchmarks, benchmarks→generators)  
✅ Provides actionable error messages with pack/section context  
✅ Can be run with `pytest backend/tests/test_benchmarks_wiring.py -q`  

## File Statistics

- **Lines of Code**: ~650
- **Test Classes**: 2
- **Test Methods**: 6
- **Helper Functions**: 3
- **Import Dependencies**: 7 (all existing modules)
