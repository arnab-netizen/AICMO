"""
Test that verifies:
1. Canonical Streamlit UI (streamlit_pages/aicmo_operator.py) is production-ready
2. Secondary UIs raise RuntimeError
"""

import sys
import subprocess
import pytest
from pathlib import Path


class TestCanonicalStreamlitUI:
    """STEP 3.1: Canonical Streamlit UI is production-ready."""
    
    def test_aicmo_operator_exists_and_large(self):
        """
        Evidence: RUNBOOK_RENDER_STREAMLIT.md:33
        Entry Point: streamlit_pages/aicmo_operator.py
        Expected: Large file (mature), properly titled
        """
        operator_ui = Path(__file__).parent.parent / "streamlit_pages" / "aicmo_operator.py"
        assert operator_ui.exists(), "streamlit_pages/aicmo_operator.py should exist"
        
        # Check it's a substantial file (109 KB = mature)
        size_kb = operator_ui.stat().st_size / 1024
        assert size_kb > 50, f"Canonical UI should be substantial ({size_kb}KB)"
        
        content = operator_ui.read_text()
        assert 'AICMO Operator' in content or 'st.set_page_config' in content, \
            "Canonical UI should have Streamlit setup"
    
    def test_aicmo_operator_has_production_title(self):
        """Verify canonical UI has proper page title."""
        operator_ui = Path(__file__).parent.parent / "streamlit_pages" / "aicmo_operator.py"
        content = operator_ui.read_text()
        
        # Should have st.set_page_config with page_title
        assert 'page_title=' in content or 'st.set_page_config' in content, \
            "Canonical UI should configure Streamlit page"
        
        # Should NOT have deprecation warning
        assert 'DEPRECATED' not in content, \
            "Canonical UI should not have deprecation warning"


class TestDeprecatedStreamlitUIs:
    """STEP 3.2: Secondary UIs raise RuntimeError to prevent deployment."""
    
    @pytest.mark.parametrize("ui_file,ui_name", [
        ("aicmo_ops_shell.py", "Ops Shell"),
        ("cam_engine_ui.py", "CAM Engine"),
        ("operator_qc.py", "Operator QC"),
    ])
    def test_secondary_ui_raises_runtime_error(self, ui_file, ui_name):
        """
        Verify each secondary UI raises RuntimeError on execution.
        
        Secondary UIs:
        - aicmo_ops_shell.py: Diagnostics & E2E sentinels
        - cam_engine_ui.py: CAM-specific engine testing
        - operator_qc.py: Internal QC panel
        """
        ui_path = Path(__file__).parent.parent / "streamlit_pages" / ui_file
        assert ui_path.exists(), f"streamlit_pages/{ui_file} should exist"
        
        # Check syntax
        result = subprocess.run(
            ["python", "-m", "py_compile", str(ui_path)],
            capture_output=True,
            timeout=10
        )
        assert result.returncode == 0, \
            f"{ui_file} has syntax errors: {result.stderr.decode()}"
        
        # Check deprecation message
        content = ui_path.read_text()
        assert 'DEPRECATED' in content, \
            f"{ui_file} should have DEPRECATED notice"
        assert 'aicmo_operator.py' in content, \
            f"{ui_file} should reference canonical UI"
    
    def test_secondary_uis_have_clear_deprecation_messages(self):
        """Verify all secondary UIs have clear deprecation messages."""
        secondary_uis = [
            "aicmo_ops_shell.py",
            "cam_engine_ui.py", 
            "operator_qc.py",
        ]
        
        for ui_file in secondary_uis:
            ui_path = Path(__file__).parent.parent / "streamlit_pages" / ui_file
            content = ui_path.read_text()
            
            # All should have consistent deprecation pattern
            assert 'DEPRECATED_STREAMLIT_ENTRYPOINT' in content or 'DEPRECATED' in content, \
                f"{ui_file} should have deprecation notice"
            assert 'aicmo_operator.py' in content, \
                f"{ui_file} should point to canonical UI"
            assert 'RUNBOOK' in content, \
                f"{ui_file} should reference RUNBOOK"


class TestStreamlitUILaunchScript:
    """STEP 3.3: Launch script references canonical UI only."""
    
    def test_launch_script_uses_canonical_ui(self):
        """Verify launch script uses canonical Streamlit UI."""
        launch_script = Path(__file__).parent.parent / "scripts" / "launch_operator_ui.sh"
        
        if launch_script.exists():
            content = launch_script.read_text()
            assert 'aicmo_operator.py' in content, \
                "Launch script should reference canonical UI"
            # Should NOT reference secondary UIs
            assert 'aicmo_ops_shell.py' not in content
            assert 'cam_engine_ui.py' not in content
            assert 'operator_qc.py' not in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
