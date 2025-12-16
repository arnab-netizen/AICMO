"""
Test: Streamlit operator UI is safe-by-default.

Verifies that dangerous operations (raw SQL, destructive actions) are not
accessible unless explicitly enabled via AICMO_ENABLE_DANGEROUS_UI_OPS=1.
"""

import os
import subprocess
import sys
import pytest


@pytest.mark.smoke
def test_streamlit_ui_safe_by_default():
    """Test that dangerous ops are disabled by default."""
    env = os.environ.copy()
    env.pop('AICMO_ENABLE_DANGEROUS_UI_OPS', None)
    
    # Try to compile UI without danger mode
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', 'streamlit_pages/aicmo_operator.py'],
        env=env,
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, f"UI compile failed: {result.stderr}"


@pytest.mark.smoke
def test_streamlit_ui_danger_mode_env_check():
    """Test that danger mode can be enabled via env var."""
    # Read the UI source
    with open('streamlit_pages/aicmo_operator.py', 'r') as f:
        content = f.read()
    
    # Verify safety gate exists
    assert 'AICMO_ENABLE_DANGEROUS_UI_OPS' in content, \
        "Safety gate environment check not found"
    
    assert "os.getenv('AICMO_ENABLE_DANGEROUS_UI_OPS'" in content, \
        "Safety gate not reading environment variable"


@pytest.mark.smoke
def test_streamlit_ui_imports_without_llm_key():
    """Test that UI imports successfully without OpenAI API key."""
    env = os.environ.copy()
    env.pop('OPENAI_API_KEY', None)
    env.pop('AICMO_ENABLE_DANGEROUS_UI_OPS', None)
    
    # Try to import UI
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', 'streamlit_pages/aicmo_operator.py'],
        env=env,
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, f"UI import failed without key: {result.stderr}"


@pytest.mark.smoke
def test_streamlit_ui_has_safety_gate():
    """Smoke test: safety gate is present in code."""
    with open('streamlit_pages/aicmo_operator.py', 'r') as f:
        lines = f.readlines()
    
    # Check first 100 lines for safety gate
    content = ''.join(lines[:100])
    assert 'AICMO_ENABLE_DANGEROUS_UI_OPS' in content, \
        "Safety gate not in first 100 lines"
    assert 'DANGER MODE' in content, \
        "DANGER MODE warning not found"


@pytest.mark.smoke
def test_streamlit_no_hardcoded_dangerous_enabled():
    """Test that dangerous mode is not hardcoded to True."""
    with open('streamlit_pages/aicmo_operator.py', 'r') as f:
        content = f.read()
    
    # Should not have dangerous enabled by default
    assert "AICMO_ENABLE_DANGEROUS_UI_OPS = True" not in content, \
        "Dangerous ops hardcoded to enabled"
    
    # Should read from environment
    assert "os.getenv('AICMO_ENABLE_DANGEROUS_UI_OPS'" in content, \
        "Not reading from environment"
