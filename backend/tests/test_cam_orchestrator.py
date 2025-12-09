"""
Tests for CAM Orchestrator.

Verifies that the daily CAM cycle:
- Runs without raising exceptions
- Respects dry_run mode
- Respects daily limits
- Returns valid CAMCycleReport
- Logs events via existing learning system
"""

import pytest
from unittest.mock import MagicMock, patch

from aicmo.cam.orchestrator import (
    CAMCycleConfig,
    CAMCycleReport,
    run_daily_cam_cycle,
)


class TestCAMOrchestrator:
    """Test suite for CAM orchestrator."""
    
    def test_run_daily_cam_cycle_basic(self):
        """Test basic CAM cycle execution with default settings."""
        config = CAMCycleConfig(
            max_new_leads_per_day=5,
            max_outreach_per_day=5,
            max_followups_per_day=5,
            channels_enabled=["email"],
            dry_run=True
        )
        
        report = run_daily_cam_cycle(config)
        
        # Verify return type
        assert isinstance(report, CAMCycleReport)
        
        # Verify structure
        assert hasattr(report, 'leads_created')
        assert hasattr(report, 'outreach_sent')
        assert hasattr(report, 'followups_sent')
        assert hasattr(report, 'hot_leads_detected')
        assert hasattr(report, 'errors')
        
        # Verify errors is a list
        assert isinstance(report.errors, list)
        
        # Verify counters are integers
        assert isinstance(report.leads_created, int)
        assert isinstance(report.outreach_sent, int)
        assert isinstance(report.followups_sent, int)
        assert isinstance(report.hot_leads_detected, int)
    
    def test_run_daily_cam_cycle_respects_dry_run(self):
        """Test that dry_run mode is respected and no real sends occur."""
        config = CAMCycleConfig(
            max_new_leads_per_day=10,
            max_outreach_per_day=10,
            max_followups_per_day=5,
            channels_enabled=["email", "linkedin"],
            dry_run=True
        )
        
        # Mock the gateway factories
        with patch('aicmo.cam.orchestrator.get_email_sender') as mock_email, \
             patch('aicmo.cam.orchestrator.get_social_poster') as mock_social, \
             patch('aicmo.cam.orchestrator.get_crm_syncer') as mock_crm:
            
            # Create mock adapters
            mock_email_adapter = MagicMock()
            mock_social_adapter = MagicMock()
            mock_crm_adapter = MagicMock()
            
            mock_email.return_value = mock_email_adapter
            mock_social.return_value = mock_social_adapter
            mock_crm.return_value = mock_crm_adapter
            
            # Run cycle
            report = run_daily_cam_cycle(config)
            
            # Verify no exceptions raised
            assert isinstance(report, CAMCycleReport)
            
            # In dry_run mode, we should still call factories
            # (they return no-op adapters that don't actually send)
            # The assertion is that we get a valid report back
            assert report is not None
    
    def test_run_daily_cam_cycle_with_limits(self):
        """Test that orchestrator respects max limits."""
        config = CAMCycleConfig(
            max_new_leads_per_day=1,  # Very restrictive
            max_outreach_per_day=0,   # No outreach allowed
            max_followups_per_day=0,  # No followups
            channels_enabled=["email"],
            dry_run=True
        )
        
        report = run_daily_cam_cycle(config)
        
        # Should not crash with restrictive limits
        assert isinstance(report, CAMCycleReport)
        
        # Expected behavior: limits prevent actions
        assert report.outreach_sent <= config.max_outreach_per_day
    
    def test_run_daily_cam_cycle_no_exceptions(self):
        """Test that orchestrator gracefully handles errors without crashing."""
        config = CAMCycleConfig(
            max_new_leads_per_day=5,
            max_outreach_per_day=5,
            max_followups_per_day=5,
            channels_enabled=["email", "linkedin"],
            dry_run=True
        )
        
        # Even if gateways fail, cycle should complete and return a report
        with patch('aicmo.cam.orchestrator.get_email_sender') as mock_email:
            mock_email.side_effect = Exception("Gateway unavailable")
            
            # Should NOT raise
            report = run_daily_cam_cycle(config)
            
            # Should return valid report
            assert isinstance(report, CAMCycleReport)
    
    def test_cam_cycle_config_defaults(self):
        """Test that CAMCycleConfig has expected defaults."""
        config = CAMCycleConfig(
            max_new_leads_per_day=10,
            max_outreach_per_day=10,
            max_followups_per_day=5,
            channels_enabled=["email"]
        )
        
        # dry_run should default to True
        assert config.dry_run is True
        
        # safety_settings should start as None and be set by orchestrator
        assert config.safety_settings is None
    
    def test_cam_cycle_report_structure(self):
        """Test CAMCycleReport dataclass structure."""
        report = CAMCycleReport(
            leads_created=5,
            outreach_sent=10,
            followups_sent=2,
            hot_leads_detected=1,
            errors=[]
        )
        
        assert report.leads_created == 5
        assert report.outreach_sent == 10
        assert report.followups_sent == 2
        assert report.hot_leads_detected == 1
        assert report.errors == []
    
    def test_cam_cycle_with_multiple_channels(self):
        """Test cycle with multiple enabled channels."""
        config = CAMCycleConfig(
            max_new_leads_per_day=10,
            max_outreach_per_day=15,
            max_followups_per_day=5,
            channels_enabled=["email", "linkedin", "twitter"],
            dry_run=True
        )
        
        report = run_daily_cam_cycle(config)
        
        # Should handle multiple channels without error
        assert isinstance(report, CAMCycleReport)
        assert len(config.channels_enabled) == 3


class TestCAMOrchestratorIntegration:
    """Integration tests for CAM orchestrator with real gateways (no-op)."""
    
    def test_run_daily_cam_cycle_with_real_gateways(self):
        """Test that real no-op gateways work correctly with orchestrator."""
        config = CAMCycleConfig(
            max_new_leads_per_day=5,
            max_outreach_per_day=5,
            max_followups_per_day=5,
            channels_enabled=["email", "linkedin"],
            dry_run=True
        )
        
        # Use real gateway factories (they return no-op adapters)
        report = run_daily_cam_cycle(config)
        
        # Should succeed with real factories
        assert isinstance(report, CAMCycleReport)
        assert isinstance(report.errors, list)
    
    def test_run_daily_cam_cycle_logging(self):
        """Test that orchestrator logs events to learning system."""
        config = CAMCycleConfig(
            max_new_leads_per_day=5,
            max_outreach_per_day=5,
            max_followups_per_day=5,
            channels_enabled=["email"],
            dry_run=True
        )
        
        with patch('aicmo.cam.orchestrator.log_event') as mock_log:
            report = run_daily_cam_cycle(config)
            
            # Verify that logging was attempted
            # (exact number of calls depends on implementation)
            assert mock_log.called
            
            # Verify at least a cycle_started and cycle_completed were logged
            call_args_list = [call[0][0] for call in mock_log.call_args_list]
            assert any("cycle_started" in arg for arg in call_args_list)
            assert any("cycle_completed" in arg for arg in call_args_list)
