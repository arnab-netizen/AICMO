# AICMO Phase 14 + Self-Test Engine - Quick Reference

**Status:** ✅ COMPLETE | **Tests:** 135/135 PASSING | **Regressions:** ZERO

---

## What's New in This Session

### Phase 14: Operator Command Center ✅
- **Goal:** Unified dashboard for operators to control brand automation
- **Status:** 41/41 tests passing, production-ready
- **Location:** `aicmo/operator/`
- **Key API:** `aicmo.operator_services` (6 wrapper functions)

### Self-Test Engine ✅
- **Goal:** Automated system health testing with dynamic discovery
- **Status:** 19/19 tests passing, production-ready
- **Location:** `aicmo/self_test/`
- **CLI:** `python -m aicmo.self_test.cli`

---

## Quick Start

### Get Operator Dashboard
```python
from aicmo.operator_services import get_brand_dashboard
dashboard = get_brand_dashboard("brand_123")
print(f"Brand: {dashboard.brand_status.brand_name}")
print(f"Tasks: {dashboard.task_queue.pending}")
print(f"Automation: {dashboard.automation_mode.mode}")
```

### Update Automation Mode
```python
from aicmo.operator_services import update_automation_settings
update_automation_settings("brand_123", mode="review_first", dry_run=True)
```

### Trigger Execution
```python
from aicmo.operator_services import trigger_execution_cycle
trigger_execution_cycle("brand_123", max_tasks=5)
```

### Run Self-Test
```bash
# CLI (quick test)
python -m aicmo.self_test.cli

# CLI (full test)
python -m aicmo.self_test.cli --full

# Python API
from aicmo.self_test import SelfTestOrchestrator, ReportGenerator
orchestrator = SelfTestOrchestrator()
result = orchestrator.run_self_test()
reporter = ReportGenerator()
reporter.save_reports(result)
```

---

## File Structure

```
aicmo/
├── operator/ (NEW)
│   ├── __init__.py
│   ├── dashboard_models.py (6 dataclasses)
│   ├── automation_settings.py (Settings + Repository)
│   └── dashboard_service.py (Main orchestrator)
├── operator_services.py (MODIFIED - added 6 functions)
└── self_test/ (NEW)
    ├── __init__.py
    ├── models.py (Data structures)
    ├── discovery.py (Dynamic component scanning)
    ├── test_inputs.py (6 synthetic briefs)
    ├── validators.py (Validation wrapper)
    ├── snapshots.py (Regression detection)
    ├── orchestrator.py (Test engine)
    ├── reporting.py (Report generation)
    └── cli.py (CLI interface)

tests/
├── test_phase14_operator_dashboard.py (NEW - 41 tests)
└── test_self_test_engine.py (NEW - 19 tests)
```

---

## Automation Modes

| Mode | Behavior | Safety |
|------|----------|--------|
| **manual** | Operator must explicitly trigger everything | 🟢 Maximum |
| **review_first** | Auto-tasks with operator approval (default) | 🟡 High |
| **full_auto** | Safe tasks auto-execute | 🔴 Lower |

---

## Test Commands

```bash
# All Phase 14 tests
pytest tests/test_phase14_operator_dashboard.py -v

# All Self-Test Engine tests
pytest tests/test_self_test_engine.py -v

# Specific test class
pytest tests/test_self_test_engine.py::TestSelfTestDiscovery -v

# With coverage
pytest tests/test_self_test_engine.py --cov=aicmo.self_test

# All phases (11-14)
pytest tests/test_phase*.py -v
```

---

## Key Components Discovered

Self-Test Engine automatically discovers:
- **Generators:** 11 modules (persona, social_calendar, swot, etc.)
- **Adapters:** 10+ modules (apollo, dropcontact, airtable, etc.)
- **Packagers:** 6+ functions (output, execution, kaizen orchestrators)
- **Validators:** 20+ validators from quality module
- **Benchmarks:** 8+ JSON files in learning/benchmarks/
- **CAM:** 4+ components (orchestrator, runner, models, etc.)

---

## Documentation

- **PHASE_14_COMPLETION_SUMMARY.md** - Detailed Phase 14 guide
- **SELF_TEST_ENGINE_COMPLETION_SUMMARY.md** - Detailed Self-Test guide
- **AICMO_SESSION_FINAL_STATUS.md** - Session overview
- **SESSION_DELIVERABLES.txt** - This session's deliverables

---

## Test Results Summary

```
Phase 14 Tests:           41/41 ✅
Self-Test Engine Tests:   19/19 ✅
Phase 11 Tests:           26/26 ✅ (regression)
Phase 12 Tests:           19/19 ✅ (regression)
Phase 13 Tests:           30/30 ✅ (regression)
─────────────────────────────────────────
TOTAL:                   135/135 ✅
```

---

## Usage Patterns

### Phase 14 in Streamlit
```python
import streamlit as st
from aicmo.operator_services import get_brand_dashboard, update_automation_settings

st.title("AICMO Operator Dashboard")

brand_id = st.selectbox("Select Brand", ["brand_1", "brand_2", "brand_3"])
dashboard = get_brand_dashboard(brand_id)

st.header(f"Brand: {dashboard.brand_status.brand_name}")
st.metric("Pending Tasks", dashboard.task_queue.pending)
st.metric("Automation Mode", dashboard.automation_mode.mode)

mode = st.selectbox("Change Mode", ["manual", "review_first", "full_auto"])
if st.button("Update"):
    update_automation_settings(brand_id, mode=mode, dry_run=True)
```

### Self-Test in CI/CD
```bash
#!/bin/bash
python -m aicmo.self_test.cli --full --output /artifacts
if [ $? -eq 0 ]; then
  echo "✅ System health check passed"
  exit 0
else
  echo "❌ System health check failed"
  exit 1
fi
```

---

## Production Checklist

- [x] All tests passing (135/135)
- [x] Zero regressions
- [x] Documentation complete
- [x] CLI working
- [x] Error handling robust
- [x] Type hints complete
- [x] Performance acceptable (~1 second for full test)

**Ready for:** Deployment, CI/CD integration, monitoring setup

---

## Next Steps

1. ✅ Phase 14 ready for UI integration (Streamlit/Next.js/React)
2. ✅ Self-Test Engine ready for CI/CD integration
3. Optional: Set up automated health checks (scheduled runs)
4. Optional: Web dashboard for self-test reports
5. Optional: Custom report formats

---

## Support

For detailed information:
- Phase 14 details → See `PHASE_14_COMPLETION_SUMMARY.md`
- Self-Test details → See `SELF_TEST_ENGINE_COMPLETION_SUMMARY.md`
- Session overview → See `AICMO_SESSION_FINAL_STATUS.md`

For immediate help:
- Python API → Check docstrings in source code
- CLI help → Run `python -m aicmo.self_test.cli --help`
- Tests → Check test files for usage examples

---

**Session:** December 10, 2025 | **Status:** ✅ Production Ready
