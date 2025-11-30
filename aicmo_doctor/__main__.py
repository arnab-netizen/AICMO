from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# The core health tests to run
TEST_FILES = [
    "backend/tests/test_benchmarks_wiring.py",
    "backend/tests/test_fullstack_simulation.py",
    "backend/tests/test_report_benchmark_enforcement.py",
    "backend/tests/test_benchmark_enforcement_smoke.py",
    "backend/tests/test_request_fingerprint.py",
    "backend/tests/test_report_cache.py",
    "backend/tests/test_performance_smoke.py",
]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    print("🩺 AICMO Doctor")
    print("===============\n")
    print("Running health checks:\n")
    for path in TEST_FILES:
        print(f"  • {path}")
    print()

    cmd = [sys.executable, "-m", "pytest", *TEST_FILES, "-q"]
    result = subprocess.run(cmd, cwd=repo_root)

    print()  # spacing

    if result.returncode == 0:
        print("✅ AICMO HEALTHY – safe to run client projects.")
        sys.exit(0)
    else:
        print("❌ AICMO BROKEN – see test failures above before taking client work.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
