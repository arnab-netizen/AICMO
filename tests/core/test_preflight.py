"""
Tests for preflight checks and run safety (MODULE 0).
"""

import pytest
import os
from unittest.mock import patch
from sqlalchemy import text

from aicmo.core.preflight import (
    run_preflight_checks,
    PreflightError,
    check_database_reachable,
    check_required_env_vars,
    check_artifact_directory_writable,
)
from aicmo.core.secure_logging import redact_secrets, SecureLogger


def test_preflight_fails_if_db_unreachable():
    """Preflight must fail if database cannot be reached."""
    # Mock session that raises exception
    class MockSession:
        def execute(self, query):
            raise Exception("Connection refused")
    
    with pytest.raises(PreflightError, match="Database unreachable"):
        run_preflight_checks(MockSession())


def test_preflight_passes_with_valid_setup(db_session):
    """Preflight passes when all checks succeed."""
    # Ensure env vars are set
    os.environ["AICMO_PERSISTENCE_MODE"] = "db"
    os.environ["DATABASE_URL"] = "postgresql://test"
    
    result = run_preflight_checks(db_session)
    
    assert result.passed is True
    assert len(result.checks_passed) >= 3  # DB, env vars, artifact dir
    assert len(result.checks_failed) == 0


def test_check_database_reachable(db_session):
    """Database reachability check works."""
    success, message = check_database_reachable(db_session)
    
    assert success is True
    assert "successful" in message.lower()


def test_check_required_env_vars_fails_if_missing():
    """Env var check fails if required vars missing."""
    # Temporarily unset
    original_mode = os.environ.get("AICMO_PERSISTENCE_MODE")
    if "AICMO_PERSISTENCE_MODE" in os.environ:
        del os.environ["AICMO_PERSISTENCE_MODE"]
    
    try:
        success, message = check_required_env_vars()
        
        assert success is False
        assert "AICMO_PERSISTENCE_MODE" in message
    finally:
        # Restore
        if original_mode:
            os.environ["AICMO_PERSISTENCE_MODE"] = original_mode


def test_check_required_env_vars_fails_if_mode_not_db():
    """Env var check fails if mode is not 'db'."""
    original_mode = os.environ.get("AICMO_PERSISTENCE_MODE")
    os.environ["AICMO_PERSISTENCE_MODE"] = "inmemory"
    
    try:
        success, message = check_required_env_vars()
        
        assert success is False
        assert "must be 'db'" in message
    finally:
        if original_mode:
            os.environ["AICMO_PERSISTENCE_MODE"] = original_mode


def test_check_artifact_directory_writable():
    """Artifact directory check creates directory and verifies write."""
    success, message = check_artifact_directory_writable()
    
    assert success is True
    assert "writable" in message.lower()


def test_logs_do_not_contain_secrets():
    """Secret redaction prevents leaks in logs."""
    # Test dict redaction
    data = {
        "campaign_id": 123,
        "api_key": "sk_live_1234567890",
        "password": "supersecret",
        "normal_field": "visible",
    }
    
    redacted = redact_secrets(data)
    
    assert redacted["campaign_id"] == 123
    assert redacted["api_key"] == "***REDACTED***"
    assert redacted["password"] == "***REDACTED***"
    assert redacted["normal_field"] == "visible"


def test_secure_logger_redacts_kwargs(caplog):
    """SecureLogger redacts secret kwargs."""
    logger = SecureLogger(__name__)
    
    # Log with secret
    logger.info("Test message", campaign_id=123, api_key="secret_key_here", password="hunter2")
    
    # Check log output
    log_output = caplog.text
    
    assert "campaign_id=123" in log_output
    assert "secret_key_here" not in log_output
    assert "hunter2" not in log_output
    assert "***REDACTED***" in log_output


def test_secret_patterns_comprehensive():
    """Verify comprehensive secret pattern matching."""
    test_cases = {
        "api_key": "should_redact",
        "API-KEY": "should_redact",
        "password": "should_redact",
        "secret": "should_redact",
        "token": "should_redact",
        "bearer_token": "should_redact",
        "auth_header": "should_redact",
        "private_key": "should_redact",
        "credential": "should_redact",
        "username": "should_not_redact",  # Not in pattern list
        "campaign_id": "should_not_redact",
    }
    
    for key, expected in test_cases.items():
        data = {key: "test_value"}
        redacted = redact_secrets(data)
        
        if expected == "should_redact":
            assert redacted[key] == "***REDACTED***", f"{key} should be redacted"
        else:
            assert redacted[key] == "test_value", f"{key} should NOT be redacted"
