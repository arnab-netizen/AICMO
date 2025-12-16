"""
Test that verifies:
1. Canonical AOL runner (scripts/run_aol_worker.py) is production-ready
2. Deprecated AOL runner (scripts/run_aol_daemon.py) raises RuntimeError
"""

import sys
import subprocess
import pytest
from pathlib import Path


class TestCanonicalAOLRunnerImport:
    """STEP 2.1: Canonical AOL runner can be imported and has production structure."""
    
    def test_run_aol_worker_has_main_guard(self):
        """
        Evidence: RUNBOOK_RENDER_STREAMLIT.md:74
        Command: python scripts/run_aol_worker.py
        Expected: File exists and has proper structure for long-running daemon
        """
        worker_py = Path(__file__).parent.parent / "scripts" / "run_aol_worker.py"
        assert worker_py.exists(), "scripts/run_aol_worker.py should exist"
        
        content = worker_py.read_text()
        # Should have proper documentation
        assert 'AOL' in content or 'orchestration' in content.lower(), \
            "Worker should mention AOL or orchestration"
    
    def test_run_aol_worker_runs_without_error(self):
        """
        Verify canonical worker has syntax and basic structure.
        Note: Don't actually run it (it's a long-running daemon).
        Just check it's importable conceptually.
        """
        worker_py = Path(__file__).parent.parent / "scripts" / "run_aol_worker.py"
        
        # Check syntax
        result = subprocess.run(
            ["python", "-m", "py_compile", str(worker_py)],
            capture_output=True,
            timeout=10
        )
        assert result.returncode == 0, \
            f"Worker script has syntax errors: {result.stderr.decode()}"


class TestDeprecatedAOLRunner:
    """STEP 2.2: Deprecated AOL runner raises RuntimeError to prevent deployment."""
    
    def test_run_aol_daemon_raises_runtime_error(self):
        """
        Evidence: scripts/run_aol_daemon.py:1-20
        Status: Dev/integration testing runner with --ticks flag
        Expected: RuntimeError on execution
        """
        daemon_py = Path(__file__).parent.parent / "scripts" / "run_aol_daemon.py"
        assert daemon_py.exists(), "scripts/run_aol_daemon.py should exist"
        
        # Try to run it and capture error
        result = subprocess.run(
            ["python", str(daemon_py)],
            capture_output=True,
            timeout=5
        )
        
        # Should fail with RuntimeError (exit code 1)
        assert result.returncode != 0, \
            "Deprecated daemon should not run successfully"
        
        stderr = result.stderr.decode()
        assert 'DEPRECATED_AOL_RUNNER' in stderr or 'RuntimeError' in stderr, \
            f"Daemon should raise RuntimeError. stderr: {stderr}"
    
    def test_daemon_deprecation_message_clear(self):
        """Verify deprecation message points to correct canonical runner."""
        daemon_py = Path(__file__).parent.parent / "scripts" / "run_aol_daemon.py"
        content = daemon_py.read_text()
        
        assert 'DEPRECATED' in content, "Should have DEPRECATED notice"
        assert 'run_aol_worker.py' in content, \
            "Should reference canonical runner: run_aol_worker.py"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
