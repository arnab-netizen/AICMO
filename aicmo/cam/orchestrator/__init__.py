"""
Campaign Orchestrator - Fast Revenue Marketing Engine Phase 2.

This package exposes lightweight DB models and convenience API
symbols used by tests. The authoritative implementation lives in
`aicmo/cam/orchestrator.py` (module). To avoid accidental
import-time circular imports we dynamically load the module file
and re-export the high-level symbols expected by tests.
"""

from pathlib import Path
import importlib.util
import sys

from aicmo.cam.orchestrator.models import (
    OrchestratorRunDB,
    UnsubscribeDB,
    SuppressionDB,
    RunStatus,
)

__all__ = [
    "OrchestratorRunDB",
    "UnsubscribeDB",
    "SuppressionDB",
    "RunStatus",
]

# Dynamically load the sibling module file `aicmo/cam/orchestrator.py`
# and re-export the top-level API symbols used by tests to avoid the
# module/package name collision causing circular imports.
try:
    module_path = Path(__file__).resolve().parent.parent / "orchestrator.py"
    spec = importlib.util.spec_from_file_location("aicmo.cam.orchestrator_impl", str(module_path))
    orchestrator_mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = orchestrator_mod
    spec.loader.exec_module(orchestrator_mod)

    CAMCycleConfig = getattr(orchestrator_mod, "CAMCycleConfig")
    CAMCycleReport = getattr(orchestrator_mod, "CAMCycleReport")
    run_daily_cam_cycle = getattr(orchestrator_mod, "run_daily_cam_cycle")
    __all__.extend(["CAMCycleConfig", "CAMCycleReport", "run_daily_cam_cycle"])
except Exception:
    # Best-effort: if dynamic load fails, tests that depend on these
    # symbols will raise meaningful ImportErrors later.
    pass
