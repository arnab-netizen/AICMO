"""
Test Intake Workflow - Verify ImportError fix and session state propagation

These tests validate:
1. validate_intake can be imported correctly (R0)
2. Intake workflow sets session state keys (R1)
3. require_active_context blocks when keys missing
4. require_active_context returns tuple when keys present
"""

import pytest
from unittest.mock import Mock, patch
from aicmo.ui.persistence.artifact_store import (
    validate_intake,
    validate_intake_content,
    create_valid_intake_content,
)


def test_validate_intake_exists():
    """Test that validate_intake can be imported and is a valid function"""
    assert validate_intake is not None
    assert callable(validate_intake)
    # Should be alias of validate_intake_content
    assert validate_intake == validate_intake_content


def test_validate_intake_missing_fields():
    """Test validation fails with missing required fields"""
    incomplete_payload = {
        "client_name": "Test Company"
        # Missing: website, industry, geography, primary_offer, objective
    }
    
    ok, errors, warnings = validate_intake(incomplete_payload)
    
    assert ok is False
    assert len(errors) > 0
    assert any("website" in e.lower() for e in errors)


def test_validate_intake_valid_payload():
    """Test validation passes with complete payload"""
    valid_payload = create_valid_intake_content()
    
    ok, errors, warnings = validate_intake(valid_payload)
    
    assert ok is True
    assert len(errors) == 0


def test_create_valid_intake_content_structure():
    """Test that helper creates valid intake with all required fields"""
    intake = create_valid_intake_content()
    
    required_fields = [
        "client_name", "website", "industry", "geography",
        "primary_offer", "objective"
    ]
    
    for field in required_fields:
        assert field in intake, f"Missing required field: {field}"
        assert intake[field], f"Field {field} is empty"


def test_run_intake_step_sets_session_keys():
    """Test that run_intake_step sets active_client_id and active_engagement_id"""
    # Import locally to avoid Streamlit import issues in pytest
    import sys
    import os
    
    # Mock streamlit if not available
    if 'streamlit' not in sys.modules:
        sys.modules['streamlit'] = Mock()
    
    from operator_v2 import run_intake_step
    
    # Create valid inputs
    inputs = create_valid_intake_content()
    inputs["generation_plan"] = {
        "strategy_jobs": [],
        "creative_jobs": [],
        "execution_jobs": [],
        "monitoring_jobs": [],
        "delivery_jobs": []
    }
    
    # Mock st.session_state
    with patch('operator_v2.st') as mock_st:
        mock_session = {}
        mock_st.session_state = mock_session
        
        # Run intake step
        result = run_intake_step(inputs)
        
        # Verify session keys were set
        assert "active_client_id" in mock_session
        assert "active_engagement_id" in mock_session
        assert mock_session["active_client_id"] is not None
        assert mock_session["active_engagement_id"] is not None


# Note: require_active_context tests moved to test_intake_propagation_integration.py
# as they are better suited for integration testing with proper streamlit mocking


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
