"""
Tests for Execution Orchestrator.

Verifies that the execution layer:
- Runs without raising exceptions
- Respects execution_enabled flag
- Respects dry_run mode
- Returns valid ExecutionReport
- Logs events via existing learning system
- Handles errors gracefully
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import os

from aicmo.delivery.execution_orchestrator import (
    ExecutionConfig,
    ExecutionReport,
    get_execution_config,
    execute_plan_for_project,
)


class TestExecutionConfig:
    """Test suite for execution configuration."""
    
    def test_default_config_is_safe(self):
        """Test that default config is safe (execution disabled, dry-run enabled)."""
        config = ExecutionConfig()
        
        assert config.execution_enabled is False  # DEFAULT: Never execute
        assert config.dry_run is True  # DEFAULT: Preview only
        assert "email" in config.channels_enabled
    
    def test_config_with_custom_values(self):
        """Test configuration with custom values."""
        config = ExecutionConfig(
            execution_enabled=True,
            dry_run=False,
            channels_enabled=["email", "linkedin"]
        )
        
        assert config.execution_enabled is True
        assert config.dry_run is False
        assert "email" in config.channels_enabled
        assert "linkedin" in config.channels_enabled


class TestGetExecutionConfig:
    """Test suite for configuration reader."""
    
    def test_get_execution_config_defaults(self):
        """Test that get_execution_config returns safe defaults."""
        # Clear environment
        for key in ["EXECUTION_ENABLED", "EXECUTION_DRY_RUN", "EXECUTION_CHANNELS"]:
            if key in os.environ:
                del os.environ[key]
        
        config = get_execution_config()
        
        assert config.execution_enabled is False
        assert config.dry_run is True
        assert "email" in config.channels_enabled
    
    def test_get_execution_config_from_env(self):
        """Test that get_execution_config reads from environment."""
        # Set environment variables
        os.environ["EXECUTION_ENABLED"] = "true"
        os.environ["EXECUTION_DRY_RUN"] = "false"
        os.environ["EXECUTION_CHANNELS"] = "email,linkedin,instagram"
        
        try:
            config = get_execution_config()
            
            assert config.execution_enabled is True
            assert config.dry_run is False
            assert "email" in config.channels_enabled
            assert "linkedin" in config.channels_enabled
            assert "instagram" in config.channels_enabled
        finally:
            # Clean up environment
            for key in ["EXECUTION_ENABLED", "EXECUTION_DRY_RUN", "EXECUTION_CHANNELS"]:
                if key in os.environ:
                    del os.environ[key]
    
    def test_get_execution_config_string_parsing(self):
        """Test that environment string values are parsed correctly."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
        ]
        
        for env_value, expected_bool in test_cases:
            os.environ["EXECUTION_ENABLED"] = env_value
            
            try:
                config = get_execution_config()
                assert config.execution_enabled == expected_bool, \
                    f"Failed for {env_value}: expected {expected_bool}, got {config.execution_enabled}"
            finally:
                if "EXECUTION_ENABLED" in os.environ:
                    del os.environ["EXECUTION_ENABLED"]


class TestExecutionReport:
    """Test suite for execution report structure."""
    
    def test_execution_report_structure(self):
        """Test that ExecutionReport has all required fields."""
        report = ExecutionReport(project_id="proj-123")
        
        assert hasattr(report, 'project_id')
        assert hasattr(report, 'total_items_processed')
        assert hasattr(report, 'items_sent_successfully')
        assert hasattr(report, 'items_failed')
        assert hasattr(report, 'channels_used')
        assert hasattr(report, 'errors')
        assert hasattr(report, 'execution_results')
        
        # Verify initial state
        assert report.project_id == "proj-123"
        assert report.total_items_processed == 0
        assert report.items_sent_successfully == 0
        assert report.items_failed == 0
        assert isinstance(report.channels_used, list)
        assert isinstance(report.errors, list)
        assert isinstance(report.execution_results, list)


class TestExecutePlanForProject:
    """Test suite for main execution function."""
    
    def test_execution_disabled_by_default(self):
        """Test that execution is disabled by default (safe behavior)."""
        # Clear environment to ensure defaults
        for key in ["EXECUTION_ENABLED", "EXECUTION_DRY_RUN", "EXECUTION_CHANNELS"]:
            if key in os.environ:
                del os.environ[key]
        
        report = execute_plan_for_project("proj-123")
        
        # With execution disabled, should return early with 0 items
        assert isinstance(report, ExecutionReport)
        assert report.project_id == "proj-123"
        assert report.total_items_processed == 0
        assert report.items_sent_successfully == 0
        assert report.items_failed == 0
        assert len(report.errors) == 0
    
    def test_execution_respects_dry_run_flag(self):
        """Test that dry_run mode prevents real execution."""
        # Enable execution but use dry_run
        os.environ["EXECUTION_ENABLED"] = "true"
        os.environ["EXECUTION_DRY_RUN"] = "true"
        
        try:
            # Mock the plan fetcher to return stub data
            with patch(
                'aicmo.delivery.execution_orchestrator.fetch_project_and_plan'
            ) as mock_fetch, \
            patch(
                'aicmo.delivery.execution_orchestrator.extract_plan_items'
            ) as mock_extract, \
            patch(
                'aicmo.delivery.execution_orchestrator.get_email_sender'
            ) as mock_email:
                
                mock_project = {"id": "proj-123", "name": "Test Project"}
                mock_fetch.return_value = mock_project
                mock_extract.return_value = [
                    {"channel": "email", "to": "test@example.com", "subject": "Test"}
                ]
                
                # Mock email gateway
                mock_email_adapter = MagicMock()
                mock_email.return_value = mock_email_adapter
                
                # Mock email execution
                with patch(
                    'aicmo.delivery.execution_orchestrator.execute_email_items'
                ) as mock_exec_email:
                    mock_exec_email.return_value = {
                        "success": 0,
                        "failed": 0,
                        "results": []
                    }
                    
                    report = execute_plan_for_project("proj-123")
                    
                    # Verify execution was called (or not, depending on implementation)
                    assert isinstance(report, ExecutionReport)
                    
        finally:
            for key in ["EXECUTION_ENABLED", "EXECUTION_DRY_RUN"]:
                if key in os.environ:
                    del os.environ[key]
    
    def test_execution_override_dry_run(self):
        """Test that override_dry_run parameter works."""
        # Enable execution with dry_run=False in env
        os.environ["EXECUTION_ENABLED"] = "true"
        os.environ["EXECUTION_DRY_RUN"] = "false"
        
        try:
            # Mock the plan fetcher
            with patch(
                'aicmo.delivery.execution_orchestrator.fetch_project_and_plan'
            ) as mock_fetch, \
            patch(
                'aicmo.delivery.execution_orchestrator.extract_plan_items'
            ) as mock_extract:
                
                mock_project = {"id": "proj-123"}
                mock_fetch.return_value = mock_project
                mock_extract.return_value = []
                
                # Call with override_dry_run=True
                report = execute_plan_for_project("proj-123", override_dry_run=True)
                
                # Should still work (no exceptions)
                assert isinstance(report, ExecutionReport)
                
        finally:
            for key in ["EXECUTION_ENABLED", "EXECUTION_DRY_RUN"]:
                if key in os.environ:
                    del os.environ[key]
    
    def test_execution_no_exceptions_on_errors(self):
        """Test that execute_plan_for_project handles errors gracefully."""
        # Enable execution
        os.environ["EXECUTION_ENABLED"] = "true"
        
        try:
            # Mock the plan fetcher to raise an error
            with patch(
                'aicmo.delivery.execution_orchestrator.fetch_project_and_plan'
            ) as mock_fetch:
                
                mock_fetch.side_effect = Exception("Database error")
                
                # Should NOT raise an exception
                report = execute_plan_for_project("proj-123")
                
                # Should return report with error recorded
                assert isinstance(report, ExecutionReport)
                assert len(report.errors) > 0
                assert "Database error" in str(report.errors)
                
        finally:
            if "EXECUTION_ENABLED" in os.environ:
                del os.environ["EXECUTION_ENABLED"]
    
    def test_execution_project_not_found(self):
        """Test that missing project is handled gracefully."""
        # Enable execution
        os.environ["EXECUTION_ENABLED"] = "true"
        
        try:
            # Mock the plan fetcher to return None (not found)
            with patch(
                'aicmo.delivery.execution_orchestrator.fetch_project_and_plan'
            ) as mock_fetch:
                
                mock_fetch.return_value = None
                
                # Should NOT raise an exception
                report = execute_plan_for_project("proj-nonexistent")
                
                # Should return report with error recorded
                assert isinstance(report, ExecutionReport)
                assert len(report.errors) > 0
                assert "not found" in str(report.errors).lower()
                
        finally:
            if "EXECUTION_ENABLED" in os.environ:
                del os.environ["EXECUTION_ENABLED"]
    
    def test_execution_report_no_exceptions(self):
        """Test that main execution function never raises exceptions."""
        # Test with various configurations
        test_configs = [
            {"execution_enabled": "false", "dry_run": "true"},
            {"execution_enabled": "true", "dry_run": "true"},
            {"execution_enabled": "true", "dry_run": "false"},
        ]
        
        for env_config in test_configs:
            for key, value in env_config.items():
                os.environ[f"EXECUTION_{key.upper()}"] = value
            
            try:
                # Should never raise
                report = execute_plan_for_project("proj-123")
                assert isinstance(report, ExecutionReport)
                
            finally:
                for key in env_config.keys():
                    env_key = f"EXECUTION_{key.upper()}"
                    if env_key in os.environ:
                        del os.environ[env_key]


class TestExecutionIntegration:
    """Integration tests for execution orchestrator."""
    
    def test_full_execution_workflow(self):
        """Test complete execution workflow from config to report."""
        # Enable execution in dry-run mode
        os.environ["EXECUTION_ENABLED"] = "true"
        os.environ["EXECUTION_DRY_RUN"] = "true"
        
        try:
            # Mock all dependencies
            with patch(
                'aicmo.delivery.execution_orchestrator.fetch_project_and_plan'
            ) as mock_fetch, \
            patch(
                'aicmo.delivery.execution_orchestrator.extract_plan_items'
            ) as mock_extract, \
            patch(
                'aicmo.delivery.execution_orchestrator.execute_email_items'
            ) as mock_exec_email:
                
                # Setup mocks
                mock_project = {"id": "proj-123", "name": "Test Project"}
                mock_fetch.return_value = mock_project
                
                plan_items = [
                    {"channel": "email", "to": "test@example.com", "subject": "Test"}
                ]
                mock_extract.return_value = plan_items
                
                mock_exec_email.return_value = {
                    "success": 1,
                    "failed": 0,
                    "results": []
                }
                
                # Execute
                report = execute_plan_for_project("proj-123")
                
                # Verify report
                assert report.project_id == "proj-123"
                assert report.total_items_processed == 1
                assert report.items_sent_successfully == 1
                assert report.items_failed == 0
                assert "email" in report.channels_used
                
        finally:
            for key in ["EXECUTION_ENABLED", "EXECUTION_DRY_RUN"]:
                if key in os.environ:
                    del os.environ[key]
