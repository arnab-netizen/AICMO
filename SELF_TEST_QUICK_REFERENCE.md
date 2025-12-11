# AICMO Self-Test Engine - Quick Reference Guide

## Overview

The AICMO Self-Test Engine is a production-grade CI/CD health check that:
- Tests all generators with **real, schema-correct briefs** (ClientInputBrief)
- Distinguishes **critical vs non-critical features**
- Returns **strict exit codes** for CI/CD integration
- Generates **clear, actionable reports**

**Status:** ✅ All 65 tests passing (24 self-test + 41 Phase 14)

---

## Quick Start

### CLI Usage

```bash
# Quick test (default, ~10 seconds)
python -m aicmo.self_test.cli

# Full test suite (all briefs, generators, packagers)
python -m aicmo.self_test.cli --full

# Verbose output
python -m aicmo.self_test.cli -v

# Custom output directory
python -m aicmo.self_test.cli --output /custom/path
```

### Python API

```python
from aicmo.self_test.orchestrator import SelfTestOrchestrator
from aicmo.self_test.reporting import ReportGenerator

# Run test
orchestrator = SelfTestOrchestrator()
result = orchestrator.run_self_test(quick_mode=True)

# Check results
print(f"Passed: {result.passed_features}")
print(f"Failed: {result.failed_features}")
print(f"Critical failures: {len(result.critical_failures)}")

# Generate reports
reporter = ReportGenerator()
md_path, html_path = reporter.save_reports(result)
```

---

## Exit Codes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| **0** | ✅ Success | Proceed with deployment |
| **1** | ❌ Critical failure | Stop, fix critical issues |

### Exit Code Logic

```
if has_critical_failures:
    exit(1)  # ❌ Break CI/CD
else:
    exit(0)  # ✅ Proceed
```

**Non-critical failures don't affect exit code** - they're logged but don't break CI/CD.

---

## Test Briefs Available

### 1. CloudSync AI (SaaS)
- Industry: Cloud data synchronization
- For: persona_generator, social_calendar_generator, swot_generator
- Focus: Enterprise B2B, long sales cycles

### 2. The Harvest Table (Food & Beverage)
- Industry: Farm-to-table restaurant
- For: messaging_pillars_generator, situation_analysis_generator
- Focus: Local market, community engagement

### 3. EcoThread Co (Fashion & Apparel)
- Industry: Sustainable fashion e-commerce
- For: Cross-industry testing
- Focus: DTC, sustainability messaging

### Add Custom Briefs

```python
from aicmo.self_test.test_inputs import _minimal_brief
from aicmo.io.client_reports import ClientInputBrief, BrandBrief

def my_custom_brief() -> ClientInputBrief:
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="My Company",
            industry="My Industry",
            product_service="My product",
            primary_goal="My goal",
            primary_customer="My customer"
        ),
        audience=AudienceBrief(...),
        # ... other required sub-briefs
    )
```

---

## Critical Features (7 Total)

### Generators (5 critical)
- `persona_generator` - Creates buyer personas
- `social_calendar_generator` - Social media scheduling
- `situation_analysis_generator` - Market analysis
- `messaging_pillars_generator` - Brand messaging
- `swot_generator` - SWOT analysis

### Packagers (2 critical)
- `generate_full_deck_pptx` - PowerPoint output (python-pptx)
- `generate_html_summary` - HTML output (Jinja2)

### Non-Critical (Optional)
- Apollo Lead Enrichment
- Dropcontact Email Verification
- Airtable CRM Sync
- Other external adapters

---

## Report Output

### Console Output

```
============================================================
AICMO SELF-TEST RESULTS
============================================================
✅ Features Passed:  22
❌ Features Failed:  10
⏭️  Features Skipped: 0
============================================================

📄 Markdown Report: /path/to/AICMO_SELF_TEST_REPORT.md
🌐 HTML Report:     /path/to/AICMO_SELF_TEST_REPORT.html

⚠️  OPTIONAL FEATURES FAILED (non-critical):
   - apollo_enrichment: No API credentials configured
   - dropcontact_adapter: Request timeout

✅ No critical failures - exiting with success code 0
```

### Markdown Report Features

- ✅ Summary statistics (passed/failed/skipped counts)
- ✅ Critical failures section (highlighted in red)
- ✅ Feature-by-category breakdown
- ✅ Generator details (module path, scenarios, errors)
- ✅ Packager status and file sizes
- ✅ Timestamp and report metadata

---

## CI/CD Integration Examples

### GitHub Actions

```yaml
name: AICMO Health Check

on: [push, pull_request]

jobs:
  self-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -e .
      
      - name: Run AICMO Self-Test
        run: python -m aicmo.self_test.cli --full
        # Exit code 0 = success, 1 = critical failure
      
      - name: Upload reports (always)
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: aicmo-test-reports
          path: self_test_artifacts/
```

### GitLab CI

```yaml
aicmo_health_check:
  image: python:3.11
  script:
    - pip install -e .
    - python -m aicmo.self_test.cli --full
  artifacts:
    paths:
      - self_test_artifacts/
    when: always
  allow_failure: false  # Fail pipeline on critical failures (exit 1)
```

### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('AICMO Health Check') {
            steps {
                sh 'python -m aicmo.self_test.cli --full'
                // Jenkins treats non-zero exit code as failure
                // Exit 0 = success, Exit 1 = failure
            }
        }
        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: 'self_test_artifacts/**'
            }
        }
    }
}
```

---

## Troubleshooting

### Issue: "Cannot instantiate typing.Optional"

**Cause:** Generator validation error (likely LLM not available in quick mode)

**Solution:**
```bash
# Run with full mode to get better error details
python -m aicmo.self_test.cli --full

# Or check generator logs
AICMO_USE_LLM=0 python -m aicmo.self_test.cli  # Use stub mode
```

### Issue: "Module could not be imported"

**Cause:** Missing dependencies or import error

**Solution:**
```bash
# Verify imports
python -c "from aicmo.generators import persona_generator"

# Check for missing packages
pip list | grep -E "pydantic|jinja"
```

### Issue: Exit code is 1 but I expected 0

**Cause:** At least one critical feature failed

**Solution:**
```bash
# Check which critical features failed
python -m aicmo.self_test.cli -v

# Review generated reports
cat self_test_artifacts/AICMO_SELF_TEST_REPORT.md

# Look for "⚠️ CRITICAL FAILURES DETECTED" section
```

---

## Configuration

### Environment Variables

```bash
# Use LLM for generator testing (default: 0)
export AICMO_USE_LLM=1

# Custom snapshot directory (default: ./self_test_artifacts/snapshots)
export AICMO_SNAPSHOT_DIR=/custom/snapshots

# Custom database (default: db/aicmo_memory.db)
export AICMO_MEMORY_DB=/custom/db/aicmo.db
```

### Custom Output Directory

```bash
# CLI
python -m aicmo.self_test.cli --output /my/custom/path

# Python API
orchestrator = SelfTestOrchestrator(
    snapshots_dir="/custom/snapshots",
    base_path="/custom/base"
)
```

---

## Test Coverage

### Test Classes (24 tests total)

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestSelfTestDiscovery` | 7 | Generator, adapter, packager discovery |
| `TestSelfTestInputs` | 3 | Test brief generation and selection |
| `TestSelfTestSnapshots` | 3 | Snapshot save/load/compare |
| `TestSelfTestOrchestrator` | 5 | Critical feature marking, orchestration |
| `TestSelfTestCLI` | 2 | CLI exit codes, critical vs non-critical |
| `TestSelfTestReporting` | 4 | Markdown, HTML reports, critical badges |

### Test Execution

```bash
# Run all self-test tests
pytest tests/test_self_test_engine.py -v

# Run specific test class
pytest tests/test_self_test_engine.py::TestSelfTestOrchestrator -v

# Run with coverage
pytest tests/test_self_test_engine.py --cov=aicmo.self_test --cov-report=html
```

---

## Performance

### Typical Runtime

| Mode | Duration | Briefs | Generators |
|------|----------|--------|-----------|
| Quick | ~10s | 2 | Limited |
| Full | ~30s | All | All |
| Verbose | +5s | - | With details |

### Resource Usage

- **Memory:** ~200MB
- **Disk:** ~5MB (reports + snapshots)
- **CPU:** Minimal (mostly I/O bound)

---

## Files Modified

### Core Implementation
- `aicmo/self_test/test_inputs.py` - Real briefs, scenario mapping
- `aicmo/self_test/models.py` - CRITICAL_FEATURES constant
- `aicmo/self_test/orchestrator.py` - Critical failure tracking
- `aicmo/self_test/reporting.py` - Critical feature badges
- `aicmo/self_test/cli.py` - Strict exit codes

### Tests
- `tests/test_self_test_engine.py` - 5 new critical feature tests

---

## Best Practices

### 1. Run Before Merging

```bash
# Quick check on feature branches
python -m aicmo.self_test.cli

# Full check before merge requests
python -m aicmo.self_test.cli --full
```

### 2. Monitor Critical Failures

```python
if result.has_critical_failures:
    # Alert the team, don't merge
    send_slack_message(f"⚠️ Critical failures: {result.critical_failures}")
```

### 3. Track Historical Trends

```python
# Store results for tracking
import json
from datetime import datetime

results = {
    "timestamp": datetime.utcnow().isoformat(),
    "critical_failures": result.critical_failures,
    "total_failures": result.failed_features,
    "generators_passed": len([g for g in result.generators if g.status.value == "pass"])
}

# Save to tracking database
```

### 4. Customize Critical Features

```python
# Project-specific critical features
CUSTOM_CRITICAL = {
    "persona_generator",
    "my_custom_output_formatter",
    "my_required_validator"
}

# Update in models.py and orchestrator.py
```

---

## Support & Documentation

- **Full Implementation:** `SELF_TEST_REFINEMENT_COMPLETE.md`
- **API Reference:** Docstrings in `aicmo/self_test/*.py`
- **Test Examples:** `tests/test_self_test_engine.py`
- **Integration Examples:** CI/CD config files above

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-10 | ✅ Critical/non-critical split, strict exit codes, real briefs |
| 1.0 | 2025-11-XX | ✅ Initial self-test engine with basic discovery |

---

**Last Updated:** December 10, 2025  
**Status:** Production-Ready ✅  
**Tests Passing:** 65/65 (24 self-test + 41 Phase 14)  
**Regressions:** 0
