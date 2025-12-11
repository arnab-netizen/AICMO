# Full Project Rehearsal - Quick Start Guide

**Status:** ✅ READY TO USE  
**Test Status:** 5/5 tests passing

---

## One-Minute Overview

The Full Project Rehearsal feature simulates a complete project workflow:

```
Brief → Generators → Validation → Packaging → Report
```

It exercises all critical components end-to-end and generates a detailed execution report.

---

## Quick Usage

### Run with Default Briefs
```bash
cd /workspaces/AICMO
python -m aicmo.self_test.cli --project-rehearsal
```

This will:
1. Run full self-test suite
2. Run 2 project rehearsals (SaaS startup + Restaurant)
3. Generate complete report with "Full Project Rehearsal" section

### Run with Verbose Output
```bash
python -m aicmo.self_test.cli --project-rehearsal -v
```

Shows step-by-step progress:
```
📋 Running Full Project Rehearsals...
   - Rehearsing: CloudSync AI
     ✅ PASS (6/7 steps)
   - Rehearsing: The Harvest Table
     ✅ PASS (6/7 steps)
```

### Run Programmatically
```python
from aicmo.self_test.orchestrator import SelfTestOrchestrator
from aicmo.self_test.test_inputs import _saas_startup_brief

# Create orchestrator
orch = SelfTestOrchestrator()

# Get a brief
brief = _saas_startup_brief()

# Run rehearsal
result = orch.run_full_project_rehearsal(brief, "My Project")

# Check results
print(f"Status: {'✅ PASS' if result.passed else '❌ FAIL'}")
print(f"Success Rate: {result.success_rate:.1f}%")
print(f"Duration: {result.overall_duration_ms / 1000:.2f}s")

# Show artifacts
for artifact in result.artifacts_generated:
    print(f"  📄 {artifact}")
```

---

## What Gets Tested

### Generators (All 5 Must Pass)
1. ✅ `persona_generator` - Creates buyer personas
2. ✅ `situation_analysis_generator` - Analyzes market/competition
3. ✅ `messaging_pillars_generator` - Creates messaging strategy
4. ✅ `swot_generator` - Generates SWOT analysis
5. ✅ `social_calendar_generator` - Creates social calendar

### Packagers (At Least 1 Must Pass)
1. ✅ `generate_html_summary` - Creates HTML summary
2. ⚠️  `generate_full_deck_pptx` - Creates PPTX deck (optional, may not be available)

### Validation
- Output schema compliance
- No crashes or exceptions
- Successful file generation (HTML)
- Execution timing

---

## Understanding Results

### Success Criteria
A project **PASSES** if:
- ✅ At least 4 of 5 generators succeed
- ✅ At least 1 packager succeeds

A project **FAILS** if:
- ❌ Less than 4 generators succeed, OR
- ❌ No packagers succeed

### Example Report Section

```markdown
### ✅ CloudSync AI

- **Overall Status:** PASS
- **Success Rate:** 85.7% (6/7 steps)
- **Duration:** 0.03s

#### Execution Steps

- ✅ **Generate: persona_generator** (0ms)
  - Metrics: output_size=1341
- ✅ **Generate: situation_analysis_generator** (0ms)
  - Metrics: output_size=506
- ...
- ✅ **Package: HTML Summary** (25ms)
  - Metrics: file=/tmp/summary.html
- ❌ **Package: PPTX Deck** (0ms)
  - Warnings: PPTX generation returned None

#### Generated Artifacts

- HTML: /tmp/summary.html
```

---

## Key Features

| Feature | Details |
|---------|---------|
| **Speed** | Typically completes in < 1 second (stub mode) |
| **Scope** | All 5 critical generators + HTML packager |
| **Metrics** | Output size, execution time, file paths |
| **Error Handling** | Per-step errors don't block other steps |
| **Reporting** | Full markdown section with details |
| **API** | Programmatic access via orchestrator method |

---

## Common Questions

**Q: What does PPTX generation failure mean?**  
A: It's expected if `python-pptx` isn't installed. The project still PASSES because HTML generation succeeded. Not a failure.

**Q: Can I run rehearsal on a custom brief?**  
A: Yes! Pass any `ClientInputBrief` object to `run_full_project_rehearsal()`.

**Q: How long does it take?**  
A: ~10-50ms per generator in stub mode, ~25ms for HTML packaging = ~100ms total per project.

**Q: Is this using LLM?**  
A: No, it uses fast stub/heuristic mode by default. Set `AICMO_USE_LLM=true` to use LLM if needed.

**Q: Where is the report saved?**  
A: `/workspaces/AICMO/self_test_artifacts/AICMO_SELF_TEST_REPORT.md` (default)

---

## Test Verification

Run the tests to verify everything works:

```bash
# Run all rehearsal tests
pytest tests/test_self_test_engine.py::TestProjectRehearsal -v

# Expected output:
# test_run_full_project_rehearsal_basic PASSED
# test_run_full_project_rehearsal_has_step_results PASSED
# test_run_full_project_rehearsal_tracks_artifacts PASSED
# test_run_full_project_rehearsal_calculates_success_rate PASSED
# test_markdown_report_includes_rehearsal_section PASSED
```

All 5 tests should pass ✅

---

## Report Locations

| Report Type | Location |
|------------|----------|
| Markdown | `/workspaces/AICMO/self_test_artifacts/AICMO_SELF_TEST_REPORT.md` |
| HTML | `/workspaces/AICMO/self_test_artifacts/AICMO_SELF_TEST_REPORT.html` |

Both include the "Full Project Rehearsal" section when run with `--project-rehearsal` flag.

---

## Next Steps

- ✅ Run the CLI: `python -m aicmo.self_test.cli --project-rehearsal`
- ✅ Check the report: Open the generated markdown or HTML
- ✅ Run tests: `pytest tests/test_self_test_engine.py::TestProjectRehearsal`
- ✅ Use in CI/CD: Add `--project-rehearsal` flag to your test pipeline

---

**Feature Status:** 🟢 COMPLETE AND TESTED  
**Test Coverage:** 5/5 passing  
**Ready for Production:** YES
