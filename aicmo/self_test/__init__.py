"""
AICMO Self-Test Engine

A comprehensive system health testing framework that dynamically discovers and tests
all generators, adapters, validators, benchmarks, and workflows.

Features:
- Dynamic discovery (no hardcoded lists)
- End-to-end testing of all system components
- Snapshot-based regression detection
- Human-readable Markdown/HTML reports
- CLI and pytest integration
- Safe, idempotent, production-ready

Usage:
    from aicmo.self_test.orchestrator import SelfTestOrchestrator
    orchestrator = SelfTestOrchestrator()
    result = orchestrator.run_self_test()

    from aicmo.self_test.reporting import ReportGenerator
    reporter = ReportGenerator()
    reporter.save_reports(result)

Or from CLI:
    python -m aicmo.self_test.cli [--full] [--output DIR] [-v]
"""

from aicmo.self_test.models import (
    FeatureCategory,
    FeatureStatus,
    GatewayStatus,
    GeneratorStatus,
    PackagerStatus,
    SelfTestResult,
    SnapshotDiffResult,
    TestStatus,
)
from aicmo.self_test.orchestrator import SelfTestOrchestrator
from aicmo.self_test.reporting import ReportGenerator

__all__ = [
    "SelfTestOrchestrator",
    "ReportGenerator",
    "FeatureStatus",
    "GeneratorStatus",
    "GatewayStatus",
    "PackagerStatus",
    "SelfTestResult",
    "SnapshotDiffResult",
    "TestStatus",
    "FeatureCategory",
]
