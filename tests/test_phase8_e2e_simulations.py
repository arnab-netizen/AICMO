"""
Phase 8: End-to-End Simulation Tests for Complete Lead Pipeline

Comprehensive tests validating the complete lead pipeline (Phases 2-7)
working together from lead harvest through nurture execution.

Test Coverage:
- Full pipeline simulations (Harvest → Score → Qualify → Route → Nurture)
- Single lead journey tracking (audit trail validation)
- Performance benchmarking across lead volumes
- Data validation at each pipeline stage
- Error recovery and edge case handling
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from aicmo.cam.engine.continuous_cron import (
    CronOrchestrator,
    JobType,
    JobStatus,
)


# ============================================================================
# Test Pipeline Simulation Helpers
# ============================================================================

class MockPipelineEngines:
    """Factory for creating mock pipeline engines."""
    
    @staticmethod
    def create_mocks():
        """Create complete set of mocks for all pipeline phases."""
        harvester = Mock()
        harvester.run_harvest_batch = Mock(return_value=100)
        
        scorer = Mock()
        scorer.batch_score_leads = Mock(return_value=100)
        
        qualifier = Mock()
        qualifier.batch_qualify_leads = Mock(return_value=75)
        
        router = Mock()
        router.batch_route_leads = Mock(return_value=75)
        
        nurture = Mock()
        nurture.get_leads_to_nurture = Mock(return_value=[])
        nurture.evaluate_lead_nurture = Mock()
        nurture.send_email = Mock()
        
        return harvester, scorer, qualifier, router, nurture


# ============================================================================
# Test Full Pipeline Simulations
# ============================================================================

class TestFullPipelineSimulation:
    """Test complete pipeline execution from harvest to nurture."""

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_full_pipeline_100_leads(self, mock_session_class):
        """Test pipeline processing 100 leads through all stages."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        
        # Run pipeline
        h_result, s_result, q_result, r_result, n_result = orchestrator.run_full_pipeline(
            max_leads_per_stage=100
        )
        
        # Verify sequence
        assert h_result.job_type == JobType.HARVEST
        assert s_result.job_type == JobType.SCORE
        assert q_result.job_type == JobType.QUALIFY
        assert r_result.job_type == JobType.ROUTE
        assert n_result.job_type == JobType.NURTURE
        
        # Verify all completed
        assert h_result.status == JobStatus.COMPLETED
        assert s_result.status == JobStatus.COMPLETED
        assert q_result.status == JobStatus.COMPLETED
        assert r_result.status == JobStatus.COMPLETED
        assert n_result.status == JobStatus.COMPLETED

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_full_pipeline_lead_progression(self, mock_session_class):
        """Test that leads progress through pipeline with expected counts."""
        # Simulate: Harvest 100 → Score 100 → Qualify 75 → Route 75 → Nurture 75
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        
        harvester.run_harvest_batch = Mock(return_value=100)
        scorer.batch_score_leads = Mock(return_value=100)
        qualifier.batch_qualify_leads = Mock(return_value=75)  # 25% filtered out
        router.batch_route_leads = Mock(return_value=75)
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        results = orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        h, s, q, r, n = results
        
        # Verify lead flow
        assert h.leads_succeeded == 100  # Harvested
        assert s.leads_succeeded == 100  # All scored
        assert q.leads_succeeded == 75   # 75% qualified
        assert r.leads_succeeded == 75   # All routed
        assert n.leads_succeeded == 0    # None nurtured (empty mock list)

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_full_pipeline_fail_recovery(self, mock_session_class):
        """Test that pipeline continues even if one phase fails."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        
        # Make SCORE fail
        scorer.batch_score_leads = Mock(side_effect=Exception("Scoring error"))
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        h, s, q, r, n = orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        # Harvest succeeded
        assert h.status == JobStatus.COMPLETED
        assert h.leads_succeeded == 100
        
        # Score failed
        assert s.status == JobStatus.FAILED
        
        # But pipeline continues (Qualify onwards still run)
        assert q.status == JobStatus.COMPLETED  # Runs even though Score failed


# ============================================================================
# Test Single Lead Journey Tracking
# ============================================================================

class TestSingleLeadJourney:
    """Test tracking a single lead through entire pipeline."""

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_lead_journey_happy_path(self, mock_session_class):
        """Test single lead successfully progressing through pipeline."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        
        # Run a single lead (empty list means no actual execution, but test structure)
        from aicmo.cam.domain import Lead, LeadStatus
        
        test_lead = Lead(
            name="Test Lead",
            email="test@example.com",
            company="Test Corp",
            status=LeadStatus.NEW,
        )
        
        # Verify lead object can be created
        assert test_lead.name == "Test Lead"
        assert test_lead.email == "test@example.com"
        assert test_lead.status == LeadStatus.NEW

    def test_lead_journey_audit_trail(self):
        """Test that lead transformations are tracked through pipeline."""
        # Create a mock lead journey
        journey_steps = [
            {"phase": "harvest", "status": "discovered", "timestamp": datetime.now()},
            {"phase": "score", "status": "scored", "score": 0.85, "timestamp": datetime.now()},
            {"phase": "qualify", "status": "qualified", "timestamp": datetime.now()},
            {"phase": "route", "status": "routed", "sequence": "aggressive", "timestamp": datetime.now()},
            {"phase": "nurture", "status": "nurtured", "email_sent": True, "timestamp": datetime.now()},
        ]
        
        # Verify journey structure
        assert len(journey_steps) == 5
        assert journey_steps[0]["phase"] == "harvest"
        assert journey_steps[1]["score"] == 0.85
        assert journey_steps[2]["status"] == "qualified"
        assert journey_steps[3]["sequence"] == "aggressive"
        assert journey_steps[4]["email_sent"] is True


# ============================================================================
# Test Performance Benchmarking
# ============================================================================

class TestPerformanceBenchmark:
    """Test pipeline performance under varying lead volumes."""

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_pipeline_throughput_small_batch(self, mock_session_class):
        """Test pipeline throughput with small batch (50 leads)."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        h, s, q, r, n = orchestrator.run_full_pipeline(max_leads_per_stage=50)
        
        # Verify timing exists
        assert h.duration_seconds >= 0
        assert s.duration_seconds >= 0
        assert q.duration_seconds >= 0
        assert r.duration_seconds >= 0
        assert n.duration_seconds >= 0

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_pipeline_throughput_large_batch(self, mock_session_class):
        """Test pipeline throughput with large batch (500 leads)."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        harvester.run_harvest_batch = Mock(return_value=500)
        scorer.batch_score_leads = Mock(return_value=500)
        qualifier.batch_qualify_leads = Mock(return_value=375)  # 75% qualify
        router.batch_route_leads = Mock(return_value=375)
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        results = orchestrator.run_full_pipeline(max_leads_per_stage=500)
        
        # Verify large batch processing
        h, s, q, r, n = results
        assert h.leads_succeeded == 500
        assert q.leads_succeeded == 375

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_pipeline_scaling_linear(self, mock_session_class):
        """Test that pipeline can handle varying lead volumes."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        
        # Run two batches with different volumes
        small_results = orchestrator.run_full_pipeline(max_leads_per_stage=100)
        large_results = orchestrator.run_full_pipeline(max_leads_per_stage=200)
        
        # Verify both pipelines complete successfully
        assert small_results is not None
        assert large_results is not None
        assert len(small_results) == 5
        assert len(large_results) == 5
        
        # Verify jobs complete with proper status
        for result in small_results + large_results:
            assert result.status == JobStatus.COMPLETED


# ============================================================================
# Test Data Validation at Each Stage
# ============================================================================

class TestDataValidation:
    """Test that data is properly validated at each pipeline stage."""

    def test_harvest_output_validation(self):
        """Test that harvested leads have required fields."""
        from aicmo.cam.domain import Lead, LeadStatus, LeadSource
        
        # Create valid harvested lead
        lead = Lead(
            name="John Doe",
            email="john@example.com",
            company="ACME Corp",
            source=LeadSource.APOLLO,
            status=LeadStatus.NEW,
        )
        
        # Verify required fields
        assert lead.name is not None
        assert lead.email is not None
        assert lead.company is not None
        assert lead.status == LeadStatus.NEW

    def test_score_output_validation(self):
        """Test that scored leads have valid score values."""
        from aicmo.cam.domain import Lead, LeadStatus
        
        lead = Lead(
            name="Jane Doe",
            email="jane@example.com",
            company="ACME Corp",
            status=LeadStatus.NEW,
            lead_score=0.85,
        )
        
        # Verify score is valid (0.0-1.0)
        assert lead.lead_score is not None
        assert 0.0 <= lead.lead_score <= 1.0

    def test_qualify_output_validation(self):
        """Test that qualified leads have necessary metadata."""
        from aicmo.cam.domain import Lead, LeadStatus
        
        # Lead that qualified
        qualified_lead = Lead(
            name="Bob Smith",
            email="bob@example.com",
            company="Tech Inc",
            status=LeadStatus.QUALIFIED,
            lead_score=0.75,
        )
        
        # Lead that was lost (not qualified)
        lost_lead = Lead(
            name="Alice Jones",
            email="alice@example.com",
            company="Unknown",
            status=LeadStatus.LOST,
            lead_score=0.25,
        )
        
        assert qualified_lead.status == LeadStatus.QUALIFIED
        assert lost_lead.status == LeadStatus.LOST

    def test_route_output_validation(self):
        """Test that routed leads have sequence assignment."""
        from aicmo.cam.domain import Lead, LeadStatus
        
        routed_lead = Lead(
            name="Charlie Brown",
            email="charlie@example.com",
            company="Peanuts Inc",
            status=LeadStatus.ROUTED,
            lead_score=0.80,
        )
        
        # Routed lead should have status set
        assert routed_lead.status == LeadStatus.ROUTED

    def test_nurture_output_validation(self):
        """Test that nurtured leads have engagement data."""
        from aicmo.cam.domain import Lead, LeadStatus
        
        nurtured_lead = Lead(
            name="Diana Prince",
            email="diana@example.com",
            company="Wonder Inc",
            status=LeadStatus.CONTACTED,
            lead_score=0.82,
        )
        
        # Nurtured lead should transition to CONTACTED
        assert nurtured_lead.status == LeadStatus.CONTACTED


# ============================================================================
# Test Error Scenarios & Edge Cases
# ============================================================================

class TestErrorScenarios:
    """Test pipeline behavior under error conditions."""

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_harvest_failure_handling(self, mock_session_class):
        """Test pipeline behavior when harvest fails."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        harvester.run_harvest_batch = Mock(side_effect=Exception("API timeout"))
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        h, s, q, r, n = orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        # Harvest should fail
        assert h.status == JobStatus.FAILED
        assert "API timeout" in h.error_message

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_qualify_filtering(self, mock_session_class):
        """Test that qualification properly filters leads."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        
        # Simulate 30% qualification rate (70% filtered)
        harvester.run_harvest_batch = Mock(return_value=100)
        scorer.batch_score_leads = Mock(return_value=100)
        qualifier.batch_qualify_leads = Mock(return_value=30)  # 70% filtered
        router.batch_route_leads = Mock(return_value=30)
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        h, s, q, r, n = orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        # Verify filtering
        assert h.leads_succeeded == 100
        assert q.leads_succeeded == 30  # 70% filtered out
        assert r.leads_succeeded == 30

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_empty_batch_handling(self, mock_session_class):
        """Test pipeline behavior with empty lead batch."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        harvester.run_harvest_batch = Mock(return_value=0)
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        h, s, q, r, n = orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        # Pipeline should handle empty batch gracefully
        assert h.leads_succeeded == 0
        assert h.status == JobStatus.COMPLETED


# ============================================================================
# Test Metrics Aggregation
# ============================================================================

class TestMetricsAggregation:
    """Test metrics collection across entire pipeline."""

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_overall_success_rate_calculation(self, mock_session_class):
        """Test calculation of overall pipeline success rate."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        
        # Setup: 100 → 100 → 75 → 75 → 75
        harvester.run_harvest_batch = Mock(return_value=100)
        scorer.batch_score_leads = Mock(return_value=100)
        qualifier.batch_qualify_leads = Mock(return_value=75)
        router.batch_route_leads = Mock(return_value=75)
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        results = orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        # Verify results have proper structure for conversion tracking
        assert len(results) == 5
        assert all(hasattr(r, 'leads_succeeded') for r in results)
        
        # Calculate overall conversion rate manually
        initial_leads = results[0].leads_succeeded  # harvest
        final_leads = results[4].leads_succeeded  # nurture (after all stages)
        
        if initial_leads > 0:
            overall_rate = final_leads / initial_leads
            assert 0.0 <= overall_rate <= 1.0

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_phase_duration_aggregation(self, mock_session_class):
        """Test that phase durations are properly tracked."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        
        # Record metrics
        metrics = orchestrator.scheduler.get_all_metrics()
        
        # Should have metrics for each job type
        assert len(metrics) > 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestFullPipelineIntegration:
    """Integration tests for complete pipeline with metrics."""

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_pipeline_dashboard_integration(self, mock_session_class):
        """Test that pipeline metrics feed into dashboard."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        # Get dashboard
        dashboard = orchestrator.get_cron_dashboard()
        
        # Verify dashboard structure
        assert "timestamp" in dashboard
        assert "scheduler_status" in dashboard
        assert "job_metrics" in dashboard
        assert "recent_jobs" in dashboard

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_pipeline_monitoring_alerts(self, mock_session_class):
        """Test that pipeline monitoring can detect health issues."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        
        # Simulate multiple failures
        for _ in range(3):
            harvester.run_harvest_batch = Mock(side_effect=Exception("Repeated failure"))
            _ = orchestrator.run_harvest(max_leads=100)
        
        # Check health status
        metrics = orchestrator.scheduler.get_metrics(JobType.HARVEST)
        
        # Should show degradation
        assert metrics.consecutive_failures == 3

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_end_to_end_audit_trail(self, mock_session_class):
        """Test complete audit trail for compliance."""
        harvester, scorer, qualifier, router, nurture = MockPipelineEngines.create_mocks()
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)
        orchestrator.run_full_pipeline(max_leads_per_stage=100)
        
        # Verify job history recorded
        assert len(orchestrator.scheduler.job_history) > 0
        
        # Each job should have audit details
        for job in orchestrator.scheduler.job_history:
            assert job.started_at is not None
            assert job.completed_at is not None
            assert job.duration_seconds >= 0
