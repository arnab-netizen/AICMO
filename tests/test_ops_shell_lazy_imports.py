"""
Test that ops shell doesn't import heavy modules at import-time.

Verifies lazy loading by checking sys.modules after importing the ops shell.
"""

import sys
import pytest


def test_ops_shell_lazy_imports():
    """Test that importing ops shell doesn't load heavy modules."""
    import importlib
    
    # Track modules before import
    before = set(sys.modules.keys())
    
    # Import ops shell
    from streamlit_pages import aicmo_ops_shell
    importlib.reload(aicmo_ops_shell)
    
    # Track modules after import
    after = set(sys.modules.keys())
    new_modules = after - before
    
    # Define heavy modules we should NOT import at load time
    heavy_modules = {
        'aicmo.cam.orchestrator',
        'aicmo.creative',
        'aicmo.social',
        'aicmo.delivery',
        'openai',
        'sqlalchemy',
        'psycopg2',
    }
    
    # Check that heavy modules were NOT imported
    imported_heavy = new_modules & heavy_modules
    
    # Note: It's okay if aicmo.core.llm.runtime imported since it's lightweight
    # But the main heavy modules should not be loaded
    if imported_heavy:
        # Filter out aicmo.core.* which are lightweight
        imported_heavy = {m for m in imported_heavy if not m.startswith('aicmo.core')}
    
    assert len(imported_heavy) == 0, (
        f"Heavy modules imported at import-time: {imported_heavy}. "
        f"These should be lazy-imported only when user clicks a button."
    )


def test_ops_shell_imports_streamlit():
    """Test that ops shell properly imports streamlit."""
    # Streamlit should be imported, but only streamlit itself
    # Heavy integrations should not be
    import streamlit
    import importlib
    
    from streamlit_pages import aicmo_ops_shell
    importlib.reload(aicmo_ops_shell)
    
    # Should not crash
    assert aicmo_ops_shell is not None


def test_sentinel_functions_exist():
    """Test that all sentinel check functions exist."""
    from streamlit_pages.aicmo_ops_shell import (
        check_python_runtime,
        check_aicmo_import,
        check_public_api_imports,
        check_database_connectivity,
        check_database_tables,
        check_alembic_ready,
        check_llm_status,
        check_canonical_ui_presence,
        check_database_url_validation,
    )
    
    # All should be callable
    assert callable(check_python_runtime)
    assert callable(check_aicmo_import)
    assert callable(check_public_api_imports)
    assert callable(check_database_connectivity)
    assert callable(check_database_tables)
    assert callable(check_alembic_ready)
    assert callable(check_llm_status)
    assert callable(check_canonical_ui_presence)
    assert callable(check_database_url_validation)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
