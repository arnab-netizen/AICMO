"""
Test: LLM graceful degradation when OpenAI key is missing.

Verifies:
  - UI imports work with no OpenAI key (no crash)
  - Daemon loop imports work with no OpenAI key (no crash)
  - llm_enabled() returns False when key missing
  - Functions that require LLM raise clear RuntimeError with setup instructions
"""

import os
import pytest


def test_llm_runtime_disabled_without_key():
    """Test that LLM runtime returns False when OPENAI_API_KEY not set."""
    # Save original key if exists
    original_key = os.environ.get('OPENAI_API_KEY')
    
    try:
        # Ensure key is not set
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        from aicmo.core.llm.runtime import llm_enabled, safe_llm_status
        
        assert llm_enabled() == False, "llm_enabled() should return False without API key"
        
        status = safe_llm_status()
        assert status['enabled'] == False
        assert status['has_api_key'] == False
        assert 'not set' in status['reason'].lower()
        
    finally:
        # Restore original key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']


def test_require_llm_raises_with_clear_message():
    """Test that require_llm() raises RuntimeError with setup instructions when key missing."""
    original_key = os.environ.get('OPENAI_API_KEY')
    
    try:
        # Ensure key is not set
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        from aicmo.core.llm.runtime import require_llm
        
        with pytest.raises(RuntimeError) as exc_info:
            require_llm()
        
        error_msg = str(exc_info.value)
        assert 'OPENAI_API_KEY' in error_msg
        assert 'configure' in error_msg.lower() or 'set' in error_msg.lower()
        
    finally:
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']


def test_llm_client_degradation_without_key():
    """Test that enhance_with_llm returns stub output when LLM not enabled."""
    from aicmo.llm.client import enhance_with_llm
    
    original_key = os.environ.get('OPENAI_API_KEY')
    
    try:
        # Ensure key is not set
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        # Create a simple mock output object
        class MockOutput:
            def __init__(self):
                self.company_name = "Test Corp"
        
        output = MockOutput()
        
        # Should return stub output unchanged, not crash
        result = enhance_with_llm({}, output)  # Brief can be empty dict for test
        
        assert result is not None
        assert result.company_name == "Test Corp"
        
    finally:
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']


def test_streamlit_ui_imports_without_llm_key():
    """Test that canonical UI can be imported without OpenAI key (no early crash)."""
    original_key = os.environ.get('OPENAI_API_KEY')
    
    try:
        # Ensure key is not set
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        # Should not raise ImportError or crash at module load time
        # Note: We can't actually run the UI, but we can verify core UI module imports
        import streamlit_pages.aicmo_operator as ui_module
        
        # If we got here, UI imported successfully without crashing
        assert ui_module is not None
        
    finally:
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']


def test_aol_daemon_imports_without_llm_key():
    """Test that AOL daemon can be imported without OpenAI key."""
    original_key = os.environ.get('OPENAI_API_KEY')
    
    try:
        # Ensure key is not set
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        # Should not raise ImportError at module load time
        from aicmo.orchestration.daemon import AOLDaemon
        
        assert AOLDaemon is not None
        
    finally:
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
