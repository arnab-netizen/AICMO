"""
Test: Canonical UI command is enforced in Makefile.

Verifies:
  - Makefile ui target runs canonical streamlit_pages/aicmo_operator.py
  - Deprecated entrypoints have clear deprecation notices
"""

import os
import re
from pathlib import Path


def test_makefile_ui_target_canonical():
    """Test that Makefile ui target uses canonical UI path."""
    makefile_path = Path("Makefile")
    
    assert makefile_path.exists(), "Makefile should exist"
    
    makefile_content = makefile_path.read_text()
    
    # Find ui target
    ui_target_match = re.search(
        r"^ui:\s*\n(.*?)(?=\n[a-z\-]+:|\Z)",
        makefile_content,
        re.MULTILINE | re.DOTALL
    )
    
    assert ui_target_match, "ui target should exist in Makefile"
    
    ui_target = ui_target_match.group(1)
    
    # Check that it uses canonical path
    assert "streamlit_pages/aicmo_operator.py" in ui_target, \
        "ui target must run streamlit_pages/aicmo_operator.py"
    
    # Verify NO other deprecated paths
    assert "app.py" not in ui_target or "deprecated" in ui_target.lower(), \
        "ui target should not run app.py"


def test_deprecated_entrypoints_have_warnings():
    """Test that deprecated entrypoints contain deprecation warnings."""
    deprecated_files = [
        ("app.py", "DEPRECATED"),
        ("streamlit_app.py", "DEPRECATED"),
    ]
    
    for filename, warning_text in deprecated_files:
        file_path = Path(filename)
        
        assert file_path.exists(), f"{filename} should exist"
        
        content = file_path.read_text()
        
        assert warning_text in content, \
            f"{filename} should contain '{warning_text}' warning"
        
        # Also verify it directs to canonical UI
        assert "streamlit_pages/aicmo_operator.py" in content or \
               "aicmo_operator" in content, \
            f"{filename} should reference canonical UI"


def test_canonical_ui_module_exists():
    """Test that canonical UI module exists and is importable."""
    canonical_ui_path = Path("streamlit_pages/aicmo_operator.py")
    
    assert canonical_ui_path.exists(), \
        "Canonical UI file should exist at streamlit_pages/aicmo_operator.py"
    
    # Verify it contains streamlit import
    content = canonical_ui_path.read_text()
    
    assert "import streamlit" in content or "from streamlit" in content, \
        "Canonical UI should import streamlit"
    
    assert "st.set_page_config" in content, \
        "Canonical UI should configure page with st.set_page_config"


def test_launch_operator_delegates_to_canonical():
    """Test that launch_operator.py delegates to canonical UI."""
    launch_path = Path("launch_operator.py")
    
    assert launch_path.exists(), "launch_operator.py should exist"
    
    content = launch_path.read_text()
    
    # Verify it imports canonical UI
    assert "aicmo_operator" in content, \
        "launch_operator.py should import aicmo_operator"
    
    # Verify it's designed as a wrapper
    assert "import" in content and ("from streamlit_pages" in content or "aicmo_operator" in content), \
        "launch_operator.py should import the canonical UI module"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
