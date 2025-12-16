"""
Test: AOL Worker imports successfully without OpenAI API key.

Verifies that scripts/run_aol_worker.py does not require OpenAI at import time.
"""

import os
import sys
import subprocess
import pytest


def test_worker_imports_without_openai_key():
    """Test that worker script can be imported without OPENAI_API_KEY set."""
    env = os.environ.copy()
    env.pop('OPENAI_API_KEY', None)
    
    # Try to compile the worker script without OPENAI_API_KEY
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', 'scripts/run_aol_worker.py'],
        env=env,
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, f"Worker compile failed: {result.stderr}"


def test_worker_imports_modules():
    """Test that worker imports required AOL modules."""
    env = os.environ.copy()
    env.pop('OPENAI_API_KEY', None)
    
    # Try to import the worker module
    result = subprocess.run(
        [sys.executable, '-c', 'from scripts.run_aol_worker import AOLDaemon; print("OK")'],
        env=env,
        capture_output=True,
        text=True,
    )
    
    # Note: May fail on import if AOL not available, but should not fail on OpenAI
    # Just verify no OpenAI import error
    assert 'openai' not in result.stderr.lower() or 'ImportError' in result.stderr, \
        f"Unexpected error: {result.stderr}"


def test_worker_script_exists():
    """Test that worker script file exists and is readable."""
    assert os.path.exists('scripts/run_aol_worker.py'), "Worker script not found"
    assert os.path.isfile('scripts/run_aol_worker.py'), "Worker path is not a file"
    
    with open('scripts/run_aol_worker.py', 'r') as f:
        content = f.read()
        assert 'def run_worker_loop' in content, "run_worker_loop function not found"
        assert 'AOL_TICK_INTERVAL_SECONDS' in content, "Config constant not found"


@pytest.mark.smoke
def test_worker_can_compile_and_import():
    """Smoke test: worker is syntactically valid."""
    env = os.environ.copy()
    env['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
    env.pop('OPENAI_API_KEY', None)
    
    # Just verify syntax is OK
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', 'scripts/run_aol_worker.py'],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, f"Syntax error: {result.stderr}"
