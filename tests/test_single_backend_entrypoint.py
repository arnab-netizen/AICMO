"""
Test that verifies:
1. Canonical backend (backend.app) imports successfully
2. Deprecated backends raise RuntimeError
"""

import sys
import pytest
from pathlib import Path


class TestCanonicalBackendImport:
    """STEP 1.1: Canonical backend can be imported successfully."""
    
    def test_backend_app_imports_successfully(self):
        """
        Evidence: RUNBOOK_RENDER_STREAMLIT.md:25
        Command: uvicorn backend.app:app --host 0.0.0.0 --port $PORT
        """
        try:
            import backend.app
            assert hasattr(backend.app, 'app'), "backend.app should expose 'app' FastAPI instance"
            # Verify it's a FastAPI instance
            assert hasattr(backend.app.app, 'openapi'), "Should be FastAPI app"
        except RuntimeError as e:
            pytest.fail(f"Canonical backend.app should not raise RuntimeError: {e}")
        except Exception as e:
            pytest.fail(f"Canonical backend.app import failed: {e}")


class TestDeprecatedBackendEntrypoints:
    """STEP 1.2: Deprecated backends raise RuntimeError to prevent deployment."""
    
    def test_backend_main_raises_runtime_error(self):
        """
        Evidence: backend/main.py:1-19
        Status: Legacy 9,600+ line monolith, not in RUNBOOK
        Expected: RuntimeError on import
        """
        # Remove from sys.modules if cached
        if 'backend.main' in sys.modules:
            del sys.modules['backend.main']
        
        with pytest.raises(RuntimeError) as exc_info:
            import backend.main
        
        assert 'DEPRECATED_BACKEND_ENTRYPOINT' in str(exc_info.value)
        assert 'backend.app' in str(exc_info.value).lower()
    
    def test_app_py_is_deprecated_streamlit(self):
        """
        Evidence: app.py:1-20
        Status: Deprecated Streamlit example (not importable as Python module)
        Expected: File exists but has deprecation warning at top
        Note: app.py is a Streamlit file, not importable as Python module.
        Verify by checking file content instead of import.
        """
        app_py = Path(__file__).parent.parent / "app.py"
        assert app_py.exists(), "app.py should exist"
        
        content = app_py.read_text()
        assert 'DEPRECATED' in content, "app.py should have DEPRECATED notice"
        assert 'streamlit_pages/aicmo_operator.py' in content, \
            "app.py should reference canonical UI"
    
    def test_app_main_raises_runtime_error(self):
        """
        Evidence: app/main.py:1-18
        Status: Orphaned FastAPI app, not referenced in RUNBOOK
        Expected: RuntimeError on import
        """
        if 'app.main' in sys.modules:
            del sys.modules['app.main']
        
        with pytest.raises(RuntimeError) as exc_info:
            import app.main
        
        assert 'DEPRECATED_BACKEND_ENTRYPOINT' in str(exc_info.value)
        assert 'backend.app' in str(exc_info.value).lower()


class TestCanonicalBackendRouter:
    """STEP 1.3: Canonical backend has proper router structure."""
    
    def test_backend_app_imports_routers(self):
        """Verify canonical backend properly imports routers."""
        import backend.app
        
        # Should have router imports (not inline endpoints like legacy main.py)
        app = backend.app.app
        
        # Verify /health endpoint exists
        routes = [route.path for route in app.routes]
        assert any('/health' in route for route in routes), \
            "Canonical backend should have /health endpoint"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
