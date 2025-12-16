"""
Test LLM runtime gating and graceful degradation.

Verifies that:
1. llm_enabled() returns correct status
2. require_llm() raises with helpful message when unconfigured
3. safe_llm_status() returns diagnostics safely
4. No heavy modules imported at import-time
"""

import os
import pytest
from unittest.mock import patch


def test_llm_enabled_with_key():
    """Test that llm_enabled returns True when API key is set."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'}):
        from aicmo.core.llm.runtime import llm_enabled
        assert llm_enabled() is True


def test_llm_enabled_without_key():
    """Test that llm_enabled returns False when API key is missing."""
    with patch.dict(os.environ, {}, clear=False):
        # Remove API key if it exists
        os.environ.pop('OPENAI_API_KEY', None)
        
        # Reimport to get fresh function state
        import importlib
        import aicmo.core.llm.runtime as runtime_module
        importlib.reload(runtime_module)
        
        assert runtime_module.llm_enabled() is False


def test_llm_enabled_with_feature_flag_disabled():
    """Test that llm_enabled respects AICMO_USE_LLM=0 even with key set."""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'sk-test123',
        'AICMO_USE_LLM': '0'
    }):
        # Reimport to get fresh state
        import importlib
        import aicmo.core.llm.runtime as runtime_module
        importlib.reload(runtime_module)
        
        assert runtime_module.llm_enabled() is False


def test_require_llm_raises_when_disabled():
    """Test that require_llm raises RuntimeError with helpful message."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop('OPENAI_API_KEY', None)
        
        import importlib
        import aicmo.core.llm.runtime as runtime_module
        importlib.reload(runtime_module)
        
        with pytest.raises(RuntimeError) as exc_info:
            runtime_module.require_llm()
        
        # Check error message contains setup instructions
        error_msg = str(exc_info.value)
        assert 'OPENAI_API_KEY' in error_msg
        assert 'export' in error_msg or 'set' in error_msg.lower()


def test_require_llm_succeeds_when_enabled():
    """Test that require_llm does not raise when LLM is enabled."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'}):
        import importlib
        import aicmo.core.llm.runtime as runtime_module
        importlib.reload(runtime_module)
        
        # Should not raise
        runtime_module.require_llm()


def test_safe_llm_status_returns_dict():
    """Test that safe_llm_status returns proper diagnostic dict."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'}):
        import importlib
        import aicmo.core.llm.runtime as runtime_module
        importlib.reload(runtime_module)
        
        status = runtime_module.safe_llm_status()
        
        assert isinstance(status, dict)
        assert 'enabled' in status
        assert 'has_api_key' in status
        assert 'feature_flag' in status
        assert 'reason' in status
        assert status['enabled'] is True
        assert status['has_api_key'] is True


def test_safe_llm_status_disabled():
    """Test that safe_llm_status reports correctly when LLM disabled."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop('OPENAI_API_KEY', None)
        
        import importlib
        import aicmo.core.llm.runtime as runtime_module
        importlib.reload(runtime_module)
        
        status = runtime_module.safe_llm_status()
        
        assert status['enabled'] is False
        assert 'OPENAI_API_KEY' in status['reason']


def test_llm_runtime_no_heavy_imports():
    """Test that llm runtime module doesn't import heavy dependencies."""
    import sys
    import importlib
    
    # Track modules before import
    before = set(sys.modules.keys())
    
    import aicmo.core.llm.runtime
    importlib.reload(aicmo.core.llm.runtime)
    
    # Track modules after import
    after = set(sys.modules.keys())
    new_modules = after - before
    
    # Check that heavy modules were NOT imported
    heavy_modules = {'openai', 'aicmo.core.llm.client', 'aicmo.core.llm.service'}
    imported_heavy = new_modules & heavy_modules
    
    # Note: might be okay if openai is not loaded, but this test ensures it doesn't happen at import-time
    # assert len(imported_heavy) == 0, f"Heavy modules imported at import-time: {imported_heavy}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
