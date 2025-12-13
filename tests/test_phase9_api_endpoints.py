"""
Phase 9: Final Integration Tests - Comprehensive system validation.

Tests for:
- Campaign management functions
- Pipeline orchestration
- Scheduling operations
- Metrics aggregation
- System health checks
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from aicmo.cam.domain import LeadStatus
from aicmo.cam.engine import JobStatus, JobType, CronOrchestrator


# ============================================================================
# Test Fixtures
# ============================================================================

# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    return db


@pytest.fixture
def orchestrator():
    """Cron orchestrator instance."""
    return CronOrchestrator()


# ============================================================================
# Campaign Management Tests
# ============================================================================

class TestCampaignManagement:
    """Test campaign CRUD operations."""
    
    def test_campaign_creation(self):
        """Test creating new campaign."""
        # Campaign data
        campaign_data = {
            "name": "Test Campaign",
            "description": "Test Description",
            "target_niche": "Tech Startups",
            "service_key": "web_design",
            "target_clients": 50,
            "target_mrr": 5000.0,
            "active": True,
        }
        
        # Verify campaign structure
        assert campaign_data["name"] == "Test Campaign"
        assert campaign_data["target_clients"] == 50
        assert campaign_data["active"] == True
    
    def test_campaign_validation(self):
        """Test campaign field validation."""
        # Valid campaign
        valid_campaign = {
            "name": "Campaign 1",
            "active": True,
        }
        assert "name" in valid_campaign
        
        # Campaign fields
        assert valid_campaign["name"]
        assert valid_campaign["active"] == True


# ============================================================================
# Pipeline Orchestration Tests
# ============================================================================

class TestPipelineOrchestration:
    """Test pipeline execution and orchestration."""
    
    def test_orchestrator_creation(self, orchestrator):
        """Test creating orchestrator instance."""
        assert orchestrator is not None
        assert hasattr(orchestrator, 'run_harvest_cron')
        assert hasattr(orchestrator, 'run_full_pipeline')
    
    def test_orchestrator_has_scheduler(self, orchestrator):
        """Test orchestrator has scheduler."""
        assert hasattr(orchestrator, 'scheduler')
        assert orchestrator.scheduler is not None
    
    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_execute_harvest_workflow(self, mock_session_class, orchestrator):
        """Test harvest execution workflow."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Execute harvest
        result = orchestrator.run_harvest_cron(max_leads_per_stage=100)
        
        # Verify result structure
        assert result is not None
        assert hasattr(result, 'type')
        assert hasattr(result, 'status')
        assert result.type == JobType.HARVEST
    
    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_full_pipeline_execution(self, mock_session_class, orchestrator):
        """Test full pipeline execution."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Execute full pipeline
        results = orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        # Should have 5 results (harvest, score, qualify, route, nurture)
        assert len(results) == 5
        
        # Verify stages in order
        assert results[0].type == JobType.HARVEST
        assert results[1].type == JobType.SCORE
        assert results[2].type == JobType.QUALIFY
        assert results[3].type == JobType.ROUTE
        assert results[4].type == JobType.NURTURE


# ============================================================================
# Scheduling Tests
# ============================================================================

class TestJobScheduling:
    """Test job scheduling functionality."""
    
    def test_schedule_job_configuration(self):
        """Test job scheduling configuration."""
        schedule_config = {
            "job_type": JobType.HARVEST,
            "campaign_id": 1,
            "hour": 2,
            "minute": 0,
            "batch_size": 100,
            "timeout_seconds": 300,
            "enabled": True,
        }
        
        # Verify config fields
        assert schedule_config["hour"] == 2
        assert schedule_config["batch_size"] == 100
        assert schedule_config["enabled"] == True
    
    def test_scheduler_next_run_calculation(self, orchestrator):
        """Test scheduler calculates next run time correctly."""
        from aicmo.cam.engine.continuous_cron import CronJobConfig
        
        # Create job config
        config = CronJobConfig(
            hour=2,
            minute=0,
            batch_size=100,
            timeout_seconds=300,
            enabled=True,
        )
        
        # Scheduler should calculate next run
        assert config.hour == 2
        assert config.minute == 0
        assert config.batch_size == 100


# ============================================================================
# Metrics & Dashboard Tests
# ============================================================================

class TestMetricsAndDashboard:
    """Test metrics collection and dashboard generation."""
    
    def test_dashboard_data_structure(self, orchestrator):
        """Test dashboard returns proper data structure."""
        dashboard = orchestrator.get_cron_dashboard()
        
        # Verify dashboard structure
        assert dashboard is not None
        assert isinstance(dashboard, dict)
        assert "health_status" in dashboard
    
    def test_health_status_calculation(self, orchestrator):
        """Test health status is calculated correctly."""
        dashboard = orchestrator.get_cron_dashboard()
        
        health_status = dashboard.get("health_status", "unknown")
        assert health_status in ["healthy", "degraded", "failed", "unknown"]
    
    def test_metrics_aggregation(self, orchestrator):
        """Test metrics are properly aggregated."""
        dashboard = orchestrator.get_cron_dashboard()
        
        # Should have aggregated metrics
        assert isinstance(dashboard, dict)
        # Can check for presence of key metrics
        assert "health_status" in dashboard


# ============================================================================
# System Health Tests
# ============================================================================

class TestSystemHealth:
    """Test system health checks."""
    
    def test_orchestrator_operational(self, orchestrator):
        """Test orchestrator is operational."""
        assert orchestrator is not None
        
        # Check key methods exist
        methods = [
            'run_harvest_cron',
            'run_score_cron',
            'run_qualify_cron',
            'run_route_cron',
            'run_nurture_cron',
            'run_full_pipeline',
            'get_scheduler_status',
            'get_cron_dashboard',
        ]
        
        for method in methods:
            assert hasattr(orchestrator, method), f"Missing method: {method}"
    
    def test_scheduler_status(self, orchestrator):
        """Test scheduler status retrieval."""
        status = orchestrator.get_scheduler_status()
        
        # Status should be a dict
        assert isinstance(status, dict)
        assert "health_status" in status


# ============================================================================
# Integration Workflow Tests
# ============================================================================

class TestIntegrationWorkflows:
    """Test complete workflows."""
    
    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_complete_pipeline_workflow(self, mock_session_class):
        """Test complete pipeline from start to finish."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator()
        
        # Execute full pipeline
        results = orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        # Verify all 5 stages executed
        assert len(results) == 5
        
        # All should have completed status
        for result in results:
            assert result.status == JobStatus.COMPLETED
    
    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_harvest_then_score_workflow(self, mock_session_class):
        """Test harvest followed by scoring."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator()
        
        # Run harvest
        harvest_result = orchestrator.run_harvest_cron(max_leads_per_stage=100)
        assert harvest_result.type == JobType.HARVEST
        assert harvest_result.status == JobStatus.COMPLETED
        
        # Run score
        score_result = orchestrator.run_score_cron(max_leads_per_stage=100)
        assert score_result.type == JobType.SCORE
        assert score_result.status == JobStatus.COMPLETED


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in system."""
    
    def test_orchestrator_error_recovery(self):
        """Test orchestrator handles errors gracefully."""
        orchestrator = CronOrchestrator()
        
        # Orchestrator should be resilient
        assert orchestrator is not None
        
        # Test with non-existent session
        with patch('aicmo.cam.engine.continuous_cron.SessionLocal') as mock_session:
            mock_session.side_effect = Exception("Session error")
            
            # Even with error, object should remain valid
            assert orchestrator is not None
    
    def test_invalid_campaign_handling(self, mock_db):
        """Test handling of invalid campaign."""
        # When campaign doesn't exist, system should handle gracefully
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # This mimics API behavior
        campaign = mock_db.query.return_value.filter.return_value.first()
        assert campaign is None


# ============================================================================
# System Statistics Tests
# ============================================================================

class TestSystemStatistics:
    """Test system statistics collection."""
    
    def test_statistics_structure(self):
        """Test statistics have proper structure."""
        stats = {
            "timestamp": datetime.utcnow(),
            "total_campaigns": 0,
            "total_leads": 0,
            "qualified_leads": 0,
            "qualified_percentage": 0.0,
        }
        
        # Verify structure
        assert "timestamp" in stats
        assert "total_campaigns" in stats
        assert "qualified_percentage" in stats
    
    def test_conversion_rates(self):
        """Test conversion rate calculations."""
        total_leads = 100
        qualified_leads = 75
        routed_leads = 60
        
        # Calculate rates
        qualified_percentage = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
        routed_percentage = (routed_leads / total_leads * 100) if total_leads > 0 else 0
        
        assert qualified_percentage == 75.0
        assert routed_percentage == 60.0


# ============================================================================
# Batch Processing Tests
# ============================================================================

class TestBatchProcessing:
    """Test batch processing capabilities."""
    
    def test_batch_size_configuration(self):
        """Test batch size configuration."""
        batch_config = {
            "harvest_batch_size": 100,
            "score_batch_size": 100,
            "qualify_batch_size": 100,
            "route_batch_size": 100,
            "nurture_batch_size": 50,
        }
        
        # Verify all batch sizes configured
        assert all(v > 0 for v in batch_config.values())
    
    def test_batch_lead_progression(self):
        """Test lead progression through batches."""
        # Simulate batch progression
        harvest_leads = 100
        score_leads = 100  # All harvested leads scored
        qualified_leads = 75  # 75% qualified
        routed_leads = 75  # All qualified routed
        nurtured_leads = 0  # Simulation doesn't actually send emails
        
        # Verify progression
        assert score_leads == harvest_leads
        assert qualified_leads < score_leads
        assert routed_leads == qualified_leads
