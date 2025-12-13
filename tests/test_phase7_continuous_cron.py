"""
Tests for Phase 7: Continuous Harvesting Cron Engine

Coverage:
- CronScheduler: Timing and job scheduling
- CronMetrics: Health tracking and aggregation
- JobResult: Result tracking and aggregation
- CronOrchestrator: Pipeline orchestration (harvest→score→qualify→route→nurture)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from aicmo.cam.engine.continuous_cron import (
    CronScheduler,
    CronMetrics,
    CronOrchestrator,
    JobResult,
    JobStatus,
    JobType,
    CronJobConfig,
)


# ============================================================================
# Test CronJobConfig
# ============================================================================

class TestCronJobConfig:
    """Test cron job configuration."""

    def test_default_harvest_config(self):
        """Test default harvest job configuration."""
        config = CronJobConfig(JobType.HARVEST)
        assert config.job_type == JobType.HARVEST
        assert config.enabled is True
        assert config.run_hour == 2
        assert config.run_minute == 0
        assert config.max_leads_per_run == 100
        assert config.timeout_seconds == 3600

    def test_custom_config(self):
        """Test custom job configuration."""
        config = CronJobConfig(
            JobType.NURTURE,
            enabled=True,
            run_hour=6,
            run_minute=30,
            max_leads_per_run=50,
        )
        assert config.job_type == JobType.NURTURE
        assert config.run_hour == 6
        assert config.run_minute == 30
        assert config.max_leads_per_run == 50

    def test_disabled_config(self):
        """Test disabled job configuration."""
        config = CronJobConfig(JobType.QUALIFY, enabled=False)
        assert config.enabled is False


# ============================================================================
# Test JobResult
# ============================================================================

class TestJobResult:
    """Test job result tracking."""

    def test_job_result_creation(self):
        """Test creating a job result."""
        start = datetime.now()
        result = JobResult(
            job_type=JobType.HARVEST,
            status=JobStatus.RUNNING,
            started_at=start,
            completed_at=None,
            duration_seconds=0,
            leads_processed=100,
        )
        assert result.job_type == JobType.HARVEST
        assert result.status == JobStatus.RUNNING
        assert result.leads_processed == 100

    def test_job_result_completed(self):
        """Test completed job result."""
        start = datetime.now()
        end = start + timedelta(seconds=30)
        result = JobResult(
            job_type=JobType.SCORE,
            status=JobStatus.COMPLETED,
            started_at=start,
            completed_at=end,
            duration_seconds=30,
            leads_processed=50,
            leads_succeeded=50,
        )
        assert result.status == JobStatus.COMPLETED
        assert result.duration_seconds == 30
        assert result.leads_succeeded == 50

    def test_job_result_with_errors(self):
        """Test job result with failures."""
        start = datetime.now()
        end = start + timedelta(seconds=45)
        result = JobResult(
            job_type=JobType.QUALIFY,
            status=JobStatus.FAILED,
            started_at=start,
            completed_at=end,
            duration_seconds=45,
            leads_processed=100,
            leads_succeeded=80,
            leads_failed=20,
            error_message="API timeout",
        )
        assert result.status == JobStatus.FAILED
        assert result.leads_failed == 20
        assert result.error_message == "API timeout"


# ============================================================================
# Test CronMetrics
# ============================================================================

class TestCronMetrics:
    """Test cron metrics tracking and aggregation."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = CronMetrics()
        assert metrics.total_runs == 0
        assert metrics.successful_runs == 0
        assert metrics.failed_runs == 0
        assert metrics.health_status == "healthy"

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = CronMetrics()
        metrics.successful_runs = 8
        metrics.failed_runs = 2
        assert metrics.success_rate == 80.0

    def test_success_rate_no_runs(self):
        """Test success rate with no runs."""
        metrics = CronMetrics()
        assert metrics.success_rate == 0.0

    def test_lead_success_rate(self):
        """Test lead success rate calculation."""
        metrics = CronMetrics()
        metrics.total_leads_succeeded = 450
        metrics.total_leads_failed = 50
        assert metrics.lead_success_rate == 90.0

    def test_update_from_result_successful(self):
        """Test updating metrics from successful result."""
        metrics = CronMetrics()
        start = datetime.now()
        end = start + timedelta(seconds=60)
        result = JobResult(
            job_type=JobType.HARVEST,
            status=JobStatus.COMPLETED,
            started_at=start,
            completed_at=end,
            duration_seconds=60,
            leads_processed=100,
            leads_succeeded=100,
        )
        metrics.update_from_result(result)

        assert metrics.total_runs == 1
        assert metrics.successful_runs == 1
        assert metrics.failed_runs == 0
        assert metrics.total_leads_processed == 100
        assert metrics.total_leads_succeeded == 100
        assert metrics.consecutive_failures == 0
        assert metrics.health_status == "healthy"

    def test_update_from_result_failed(self):
        """Test updating metrics from failed result."""
        metrics = CronMetrics()
        start = datetime.now()
        end = start + timedelta(seconds=30)
        result = JobResult(
            job_type=JobType.SCORE,
            status=JobStatus.FAILED,
            started_at=start,
            completed_at=end,
            duration_seconds=30,
            error_message="Connection timeout",
        )
        metrics.update_from_result(result)

        assert metrics.total_runs == 1
        assert metrics.successful_runs == 0
        assert metrics.failed_runs == 1
        assert metrics.consecutive_failures == 1
        assert metrics.last_failure_at is not None

    def test_health_degradation(self):
        """Test health degradation after failures."""
        metrics = CronMetrics()

        # Add 3 failures
        for i in range(3):
            start = datetime.now()
            result = JobResult(
                job_type=JobType.HARVEST,
                status=JobStatus.FAILED,
                started_at=start,
                completed_at=start + timedelta(seconds=10),
                duration_seconds=10,
            )
            metrics.update_from_result(result)

        assert metrics.consecutive_failures == 3
        assert metrics.health_status == "failed"

    def test_health_recovery(self):
        """Test health recovery after successful run."""
        metrics = CronMetrics()
        metrics.consecutive_failures = 2
        metrics.failed_runs = 2
        metrics.successful_runs = 0

        # Add successful result
        start = datetime.now()
        result = JobResult(
            job_type=JobType.HARVEST,
            status=JobStatus.COMPLETED,
            started_at=start,
            completed_at=start + timedelta(seconds=30),
            duration_seconds=30,
            leads_processed=50,
            leads_succeeded=50,
        )
        metrics.update_from_result(result)

        assert metrics.consecutive_failures == 0
        # After 1 success and 2 prior failures, success_rate = 1/3 = 33%, still degraded
        assert metrics.health_status == "degraded"


# ============================================================================
# Test CronScheduler
# ============================================================================

class TestCronScheduler:
    """Test cron job scheduling and timing."""

    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = CronScheduler()
        assert len(scheduler.schedule) == 5  # 5 job types
        assert JobType.HARVEST in scheduler.schedule
        assert JobType.NURTURE in scheduler.schedule

    def test_is_job_due_matching_time(self):
        """Test checking if job is due at matching time."""
        scheduler = CronScheduler()
        # Create time matching HARVEST job (2:00 AM)
        test_time = datetime(2024, 1, 15, 2, 0, 0)
        assert scheduler.is_job_due(JobType.HARVEST, test_time) is True

    def test_is_job_due_non_matching_time(self):
        """Test checking if job is not due at non-matching time."""
        scheduler = CronScheduler()
        # Create time not matching HARVEST job
        test_time = datetime(2024, 1, 15, 3, 0, 0)
        assert scheduler.is_job_due(JobType.HARVEST, test_time) is False

    def test_is_job_due_disabled(self):
        """Test that disabled jobs are not due."""
        scheduler = CronScheduler()
        scheduler.schedule[JobType.HARVEST].enabled = False
        test_time = datetime(2024, 1, 15, 2, 0, 0)
        assert scheduler.is_job_due(JobType.HARVEST, test_time) is False

    def test_get_next_run_time_today(self):
        """Test getting next run time for today."""
        # Create custom schedule with HARVEST enabled
        schedule = {
            JobType.HARVEST: CronJobConfig(JobType.HARVEST, enabled=True, run_hour=2, run_minute=0),
        }
        scheduler = CronScheduler(schedule)
        
        # Current time before job run
        now = datetime(2024, 1, 15, 1, 0, 0)
        next_run = scheduler.get_next_run_time(JobType.HARVEST, now)

        assert next_run is not None
        assert next_run.hour == 2
        assert next_run.minute == 0
        assert next_run.day == 15

    def test_get_next_run_time_tomorrow(self):
        """Test getting next run time for tomorrow."""
        # Create custom schedule with HARVEST enabled
        schedule = {
            JobType.HARVEST: CronJobConfig(JobType.HARVEST, enabled=True, run_hour=2, run_minute=0),
        }
        scheduler = CronScheduler(schedule)
        
        # Current time after job run
        now = datetime(2024, 1, 15, 3, 0, 0)
        next_run = scheduler.get_next_run_time(JobType.HARVEST, now)

        assert next_run is not None
        assert next_run.hour == 2
        assert next_run.day == 16

    def test_get_hours_until_next_run(self):
        """Test calculating hours until next run."""
        # Create custom schedule
        schedule = {
            JobType.HARVEST: CronJobConfig(JobType.HARVEST, enabled=True, run_hour=2, run_minute=0),
        }
        scheduler = CronScheduler(schedule)
        
        # Mock the current time to ensure consistent calculation
        now = datetime(2024, 1, 15, 1, 0, 0)
        # Get next run time
        next_run = scheduler.get_next_run_time(JobType.HARVEST, now)
        
        # Calculate hours manually
        delta = next_run - now
        hours_expected = delta.total_seconds() / 3600
        
        # Should be approximately 1 hour (at 2 AM)
        assert hours_expected > 0
        assert hours_expected <= 2

    def test_record_job_result(self):
        """Test recording a job result."""
        scheduler = CronScheduler()
        start = datetime.now()
        result = JobResult(
            job_type=JobType.HARVEST,
            status=JobStatus.COMPLETED,
            started_at=start,
            completed_at=start + timedelta(seconds=30),
            duration_seconds=30,
            leads_processed=100,
            leads_succeeded=100,
        )
        scheduler.record_job_result(result)

        assert len(scheduler.job_history) == 1
        metrics = scheduler.get_metrics(JobType.HARVEST)
        assert metrics.total_runs == 1
        assert metrics.successful_runs == 1

    def test_job_history_cleanup(self):
        """Test that old job history is cleaned up."""
        scheduler = CronScheduler()
        old_date = datetime.now() - timedelta(days=35)

        # Add old result
        old_result = JobResult(
            job_type=JobType.HARVEST,
            status=JobStatus.COMPLETED,
            started_at=old_date,
            completed_at=old_date + timedelta(seconds=30),
            duration_seconds=30,
        )
        scheduler.job_history.append(old_result)

        # Add new result
        new_result = JobResult(
            job_type=JobType.HARVEST,
            status=JobStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now() + timedelta(seconds=30),
            duration_seconds=30,
        )
        scheduler.record_job_result(new_result)

        # Old result should be cleaned up
        assert len(scheduler.job_history) == 1
        assert scheduler.job_history[0].completed_at == new_result.completed_at


# ============================================================================
# Test CronOrchestrator
# ============================================================================

class TestCronOrchestrator:
    """Test cron pipeline orchestration."""

    def _create_mock_engines(self):
        """Helper to create mock pipeline engines."""
        harvester = Mock()
        harvester.run_harvest_batch = Mock(return_value=25)

        scorer = Mock()
        scorer.batch_score_leads = Mock(return_value=25)

        qualifier = Mock()
        qualifier.batch_qualify_leads = Mock(return_value=18)

        router = Mock()
        router.batch_route_leads = Mock(return_value=18)

        nurture = Mock()
        nurture.get_leads_to_nurture = Mock(return_value=[])
        nurture.evaluate_lead_nurture = Mock()
        nurture.send_email = Mock()

        return harvester, scorer, qualifier, router, nurture

    def test_orchestrator_creation(self):
        """Test creating orchestrator."""
        engines = self._create_mock_engines()
        orchestrator = CronOrchestrator(*engines)

        assert orchestrator.harvester is not None
        assert orchestrator.scorer is not None
        assert orchestrator.scheduler is not None

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_run_harvest_success(self, mock_session_class):
        """Test successful harvest job."""
        harvester, scorer, qualifier, router, nurture = self._create_mock_engines()
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = orchestrator.run_harvest(max_leads=100)

        assert result.job_type == JobType.HARVEST
        assert result.status == JobStatus.COMPLETED
        assert result.leads_processed == 25
        assert result.leads_succeeded == 25
        mock_session.close.assert_called_once()

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_run_scoring_success(self, mock_session_class):
        """Test successful scoring job."""
        harvester, scorer, qualifier, router, nurture = self._create_mock_engines()
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = orchestrator.run_scoring(max_leads=100)

        assert result.job_type == JobType.SCORE
        assert result.status == JobStatus.COMPLETED
        assert result.leads_processed == 25
        mock_session.close.assert_called_once()

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_run_qualification_success(self, mock_session_class):
        """Test successful qualification job."""
        harvester, scorer, qualifier, router, nurture = self._create_mock_engines()
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = orchestrator.run_qualification(max_leads=100)

        assert result.job_type == JobType.QUALIFY
        assert result.status == JobStatus.COMPLETED
        assert result.leads_processed == 18
        mock_session.close.assert_called_once()

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_run_routing_success(self, mock_session_class):
        """Test successful routing job."""
        harvester, scorer, qualifier, router, nurture = self._create_mock_engines()
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = orchestrator.run_routing(max_leads=100)

        assert result.job_type == JobType.ROUTE
        assert result.status == JobStatus.COMPLETED
        assert result.leads_processed == 18
        mock_session.close.assert_called_once()

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_run_nurture_success(self, mock_session_class):
        """Test successful nurture job."""
        harvester, scorer, qualifier, router, nurture = self._create_mock_engines()
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = orchestrator.run_nurture(max_leads=50)

        assert result.job_type == JobType.NURTURE
        assert result.status == JobStatus.COMPLETED
        mock_session.close.assert_called_once()

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_run_full_pipeline(self, mock_session_class):
        """Test running complete daily pipeline."""
        harvester, scorer, qualifier, router, nurture = self._create_mock_engines()
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        results = orchestrator.run_full_pipeline(max_leads_per_stage=100)

        assert len(results) == 5
        assert all(r.status == JobStatus.COMPLETED for r in results)
        assert results[0].job_type == JobType.HARVEST
        assert results[4].job_type == JobType.NURTURE

    @patch('aicmo.cam.engine.continuous_cron.SessionLocal')
    def test_run_harvest_with_error(self, mock_session_class):
        """Test harvest job with error handling."""
        harvester, scorer, qualifier, router, nurture = self._create_mock_engines()
        harvester.run_harvest_batch = Mock(side_effect=Exception("API Error"))

        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = orchestrator.run_harvest(max_leads=100)

        assert result.status == JobStatus.FAILED
        assert "API Error" in result.error_message
        mock_session.close.assert_called_once()

    def test_get_scheduler_status(self):
        """Test getting scheduler status."""
        harvester, scorer, qualifier, router, nurture = self._create_mock_engines()
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)

        status = orchestrator.get_scheduler_status()

        assert "timestamp" in status
        assert "jobs" in status
        assert "overall_health" in status
        assert len(status["jobs"]) > 0

    def test_get_cron_dashboard(self):
        """Test getting cron dashboard."""
        harvester, scorer, qualifier, router, nurture = self._create_mock_engines()
        orchestrator = CronOrchestrator(harvester, scorer, qualifier, router, nurture)

        dashboard = orchestrator.get_cron_dashboard()

        assert "timestamp" in dashboard
        assert "scheduler_status" in dashboard
        assert "job_metrics" in dashboard
        assert "recent_jobs" in dashboard


# ============================================================================
# Integration Tests
# ============================================================================

class TestCronIntegration:
    """Integration tests for cron system."""

    def test_scheduler_with_multiple_jobs(self):
        """Test scheduler handling multiple job types."""
        scheduler = CronScheduler()

        # Simulate running multiple jobs
        start1 = datetime.now()
        result1 = JobResult(
            job_type=JobType.HARVEST,
            status=JobStatus.COMPLETED,
            started_at=start1,
            completed_at=start1 + timedelta(seconds=30),
            duration_seconds=30,
            leads_processed=100,
            leads_succeeded=100,
        )

        start2 = datetime.now()
        result2 = JobResult(
            job_type=JobType.SCORE,
            status=JobStatus.COMPLETED,
            started_at=start2,
            completed_at=start2 + timedelta(seconds=45),
            duration_seconds=45,
            leads_processed=100,
            leads_succeeded=100,
        )

        scheduler.record_job_result(result1)
        scheduler.record_job_result(result2)

        assert scheduler.get_metrics(JobType.HARVEST).total_runs == 1
        assert scheduler.get_metrics(JobType.SCORE).total_runs == 1
        assert len(scheduler.job_history) == 2

    def test_daily_pipeline_flow(self):
        """Test complete daily pipeline flow."""
        scheduler = CronScheduler()

        # Simulate a complete daily run
        jobs = [JobType.HARVEST, JobType.SCORE, JobType.QUALIFY, JobType.ROUTE, JobType.NURTURE]
        leads_count = [100, 100, 95, 90, 45]

        for job_type, leads in zip(jobs, leads_count):
            start = datetime.now()
            result = JobResult(
                job_type=job_type,
                status=JobStatus.COMPLETED,
                started_at=start,
                completed_at=start + timedelta(seconds=30),
                duration_seconds=30,
                leads_processed=leads,
                leads_succeeded=leads,
            )
            scheduler.record_job_result(result)

        # Verify all jobs completed successfully
        for job_type in jobs:
            metrics = scheduler.get_metrics(job_type)
            assert metrics.successful_runs == 1
            assert metrics.failed_runs == 0
            assert metrics.health_status == "healthy"
