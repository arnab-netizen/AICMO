"""
Phase 7: Continuous Harvesting Cron Engine

Automated scheduled orchestration of lead lifecycle:
- Daily lead harvesting from configured sources
- Batch scoring with ICP matching
- Automatic qualification rules
- Lead routing to appropriate sequences
- Nurture sequence execution

Provides:
- CronScheduler: Defines scheduled tasks and timing
- HarvestJob: Encapsulates single harvest execution
- CronMetrics: Tracks job performance and health
- CronOrchestrator: Runs daily pipeline orchestration
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
import logging

from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, LeadStatus
from aicmo.cam.db_models import LeadDB
from aicmo.core import SessionLocal

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Status of a scheduled job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class JobType(str, Enum):
    """Types of scheduled jobs in the pipeline."""
    HARVEST = "harvest"
    SCORE = "score"
    QUALIFY = "qualify"
    ROUTE = "route"
    NURTURE = "nurture"
    FULL_PIPELINE = "full_pipeline"


@dataclass
class CronJobConfig:
    """Configuration for a scheduled cron job."""
    job_type: JobType
    enabled: bool = True
    run_hour: int = 2  # Hour of day to run (0-23)
    run_minute: int = 0  # Minute of hour to run
    max_leads_per_run: int = 100  # Batch size
    timeout_seconds: int = 3600  # Max execution time (1 hour)
    retry_on_failure: bool = True
    max_retries: int = 3
    notify_on_failure: bool = True


@dataclass
class JobResult:
    """
    Result of a single job execution.
    
    PHASE B HARDENING: Added execution_id for idempotency.
    """
    job_type: JobType
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: float
    execution_id: Optional[str] = None  # PHASE B: Deterministic ID for idempotency
    campaign_id: Optional[int] = None  # Campaign context (for scoped jobs)
    leads_processed: int = 0
    leads_succeeded: int = 0
    leads_failed: int = 0
    error_message: Optional[str] = None
    outcome: str = "SUCCESS"  # PHASE B: Detailed outcome (SUCCESS, FAILURE, TIMEOUT, DUPLICATE_SKIPPED)
    details: Dict[str, any] = field(default_factory=dict)


@dataclass
class CronMetrics:
    """Metrics for cron job health and performance."""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    skipped_runs: int = 0
    total_leads_processed: int = 0
    total_leads_succeeded: int = 0
    total_leads_failed: int = 0
    total_harvest_duration: float = 0.0
    average_harvest_duration: float = 0.0
    last_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    consecutive_failures: int = 0
    health_status: str = "healthy"  # healthy, degraded, failed

    @property
    def success_rate(self) -> float:
        """Percentage of successful runs."""
        total = self.successful_runs + self.failed_runs
        if total == 0:
            return 0.0
        return (self.successful_runs / total) * 100

    @property
    def lead_success_rate(self) -> float:
        """Percentage of leads processed successfully."""
        total = self.total_leads_succeeded + self.total_leads_failed
        if total == 0:
            return 0.0
        return (self.total_leads_succeeded / total) * 100

    def update_from_result(self, result: JobResult) -> None:
        """Update metrics from a job result."""
        self.total_runs += 1
        self.last_run_at = result.completed_at

        if result.status == JobStatus.COMPLETED:
            self.successful_runs += 1
            self.last_success_at = result.completed_at
            self.consecutive_failures = 0
        elif result.status == JobStatus.FAILED:
            self.failed_runs += 1
            self.last_failure_at = result.completed_at
            self.consecutive_failures += 1
        elif result.status == JobStatus.SKIPPED:
            self.skipped_runs += 1

        self.total_leads_processed += result.leads_processed
        self.total_leads_succeeded += result.leads_succeeded
        self.total_leads_failed += result.leads_failed
        self.total_harvest_duration += result.duration_seconds

        if self.total_runs > 0:
            self.average_harvest_duration = (
                self.total_harvest_duration / self.total_runs
            )

        # Update health status
        if self.consecutive_failures >= 3:
            self.health_status = "failed"
        elif self.success_rate < 50:
            self.health_status = "degraded"
        else:
            self.health_status = "healthy"


class CronScheduler:
    """Manages timing and execution of scheduled jobs."""

    # Default schedule: run pipeline daily at 2 AM
    DEFAULT_SCHEDULE = {
        JobType.HARVEST: CronJobConfig(JobType.HARVEST, run_hour=2, run_minute=0),
        JobType.SCORE: CronJobConfig(JobType.SCORE, run_hour=3, run_minute=0),
        JobType.QUALIFY: CronJobConfig(JobType.QUALIFY, run_hour=4, run_minute=0),
        JobType.ROUTE: CronJobConfig(JobType.ROUTE, run_hour=5, run_minute=0),
        JobType.NURTURE: CronJobConfig(JobType.NURTURE, run_hour=6, run_minute=0),
    }

    def __init__(self, schedule: Optional[Dict[JobType, CronJobConfig]] = None):
        """Initialize scheduler with optional custom schedule."""
        self.schedule = schedule or self.DEFAULT_SCHEDULE
        self.job_history: List[JobResult] = []
        self.metrics: Dict[JobType, CronMetrics] = {
            jt: CronMetrics() for jt in JobType
        }

    def is_job_due(self, job_type: JobType, now: Optional[datetime] = None) -> bool:
        """Check if a job is due to run at current time."""
        config = self.schedule.get(job_type)
        if not config or not config.enabled:
            return False

        now = now or datetime.now()
        return (
            now.hour == config.run_hour
            and now.minute == config.run_minute
        )

    def get_next_run_time(
        self, job_type: JobType, now: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Calculate next scheduled run time for a job."""
        config = self.schedule.get(job_type)
        if not config or not config.enabled:
            return None

        now = now or datetime.now()

        # If job already scheduled for today, use that
        today_run = now.replace(hour=config.run_hour, minute=config.run_minute, second=0, microsecond=0)
        if today_run > now:
            return today_run

        # Otherwise, schedule for tomorrow
        tomorrow_run = today_run + timedelta(days=1)
        return tomorrow_run

    def get_hours_until_next_run(self, job_type: JobType) -> float:
        """Get hours until next scheduled run."""
        next_run = self.get_next_run_time(job_type)
        if not next_run:
            return float('inf')

        delta = next_run - datetime.now()
        return delta.total_seconds() / 3600

    def record_job_result(self, result: JobResult) -> None:
        """Record a job result in history and update metrics."""
        self.job_history.append(result)
        metrics = self.metrics.get(result.job_type)
        if metrics:
            metrics.update_from_result(result)

        # Keep only last 30 days of history
        cutoff_date = datetime.now() - timedelta(days=30)
        self.job_history = [
            r for r in self.job_history
            if r.completed_at and r.completed_at >= cutoff_date
        ]

    def get_job_config(self, job_type: JobType) -> Optional[CronJobConfig]:
        """Get configuration for a job type."""
        return self.schedule.get(job_type)

    def get_metrics(self, job_type: JobType) -> Optional[CronMetrics]:
        """Get metrics for a job type."""
        return self.metrics.get(job_type)

    def get_all_metrics(self) -> Dict[JobType, CronMetrics]:
        """Get metrics for all job types."""
        return self.metrics.copy()


class CronOrchestrator:
    """Orchestrates the complete daily lead pipeline."""

    def __init__(
        self,
        harvester: Optional[object] = None,
        scorer: Optional[object] = None,
        qualifier: Optional[object] = None,
        router: Optional[object] = None,
        nurture: Optional[object] = None,
        scheduler: Optional[CronScheduler] = None,
    ):
        """Initialize orchestrator with phase engines.
        
        Engines can be None for testing. Production setup requires all engines.
        """
        self.harvester = harvester
        self.scorer = scorer
        self.qualifier = qualifier
        self.router = router
        self.nurture = nurture
        self.scheduler = scheduler or CronScheduler()

    @staticmethod
    def _generate_execution_id(
        job_type: JobType,
        campaign_id: Optional[int],
        scheduled_time: Optional[datetime] = None,
    ) -> str:
        """
        PHASE B: Generate deterministic execution ID for idempotency.
        
        Format: "{job_type}_{campaign_id}_{scheduled_time_iso}"
        Same inputs → Same ID (enables duplicate detection)
        """
        scheduled_time = scheduled_time or datetime.now()
        time_str = scheduled_time.isoformat()
        if campaign_id:
            return f"{job_type.value}_{campaign_id}_{time_str}"
        else:
            return f"{job_type.value}_global_{time_str}"

    def _check_and_record_execution(
        self,
        execution_id: str,
        job_type: JobType,
        campaign_id: Optional[int],
        scheduled_time: datetime,
    ) -> Tuple[bool, Optional[str]]:
        """
        PHASE B: Check if execution already recorded (prevent duplicates).
        
        Returns: (should_execute, existing_execution_id)
        - (True, None) = safe to execute (not yet recorded)
        - (False, exec_id) = skip execution (already ran or running)
        """
        try:
            from aicmo.cam.db_models import CronExecutionDB
            session = SessionLocal()
            try:
                # Check if this execution was already recorded
                existing = session.query(CronExecutionDB).filter(
                    CronExecutionDB.execution_id == execution_id
                ).first()
                
                if existing:
                    # Duplicate execution detected
                    logger.warning(
                        f"⚠️ Duplicate execution detected: {execution_id} "
                        f"(status={existing.status}). SKIPPING."
                    )
                    return False, existing.execution_id
                
                # Record pending execution to claim this slot
                new_exec = CronExecutionDB(
                    execution_id=execution_id,
                    job_type=job_type.value,
                    campaign_id=campaign_id,
                    scheduled_time=scheduled_time,
                    status="PENDING",
                )
                session.add(new_exec)
                session.commit()
                logger.info(f"📝 Execution recorded: {execution_id}")
                return True, None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"⚠️ Could not check execution (DB unavailable): {e}. Proceeding.")
            # If DB is down, allow execution (fail-open)
            return True, None

    def _update_execution_result(
        self,
        execution_id: str,
        result: JobResult,
    ) -> None:
        """PHASE B: Update execution record with final result."""
        try:
            from aicmo.cam.db_models import CronExecutionDB
            session = SessionLocal()
            try:
                exec_record = session.query(CronExecutionDB).filter(
                    CronExecutionDB.execution_id == execution_id
                ).first()
                
                if exec_record:
                    exec_record.status = result.status.value
                    exec_record.outcome = result.outcome
                    exec_record.started_at = result.started_at
                    exec_record.completed_at = result.completed_at
                    exec_record.duration_seconds = result.duration_seconds
                    exec_record.leads_processed = result.leads_processed
                    exec_record.leads_succeeded = result.leads_succeeded
                    exec_record.leads_failed = result.leads_failed
                    exec_record.error_message = result.error_message
                    session.commit()
                    logger.info(f"✅ Execution updated: {execution_id} → {result.outcome}")
            finally:
                session.close()
        except Exception as e:
            logger.error(f"⚠️ Could not update execution record: {e}")

    def run_harvest(
        self,
        max_leads: int = 100,
        campaign_id: Optional[int] = None,
        scheduled_time: Optional[datetime] = None,
    ) -> JobResult:
        """
        Run harvest job: discover and insert new leads.
        
        PHASE B HARDENING: Idempotent execution with duplicate prevention.
        """
        scheduled_time = scheduled_time or datetime.now()
        execution_id = self._generate_execution_id(JobType.HARVEST, campaign_id, scheduled_time)
        
        start_time = datetime.now()
        result = JobResult(
            job_type=JobType.HARVEST,
            status=JobStatus.RUNNING,
            started_at=start_time,
            completed_at=None,
            duration_seconds=0,
            execution_id=execution_id,
            campaign_id=campaign_id,
        )

        # PHASE B: Check for duplicate execution
        should_execute, existing_id = self._check_and_record_execution(
            execution_id, JobType.HARVEST, campaign_id, scheduled_time
        )
        
        if not should_execute:
            # Duplicate execution - skip and report as skipped
            result.completed_at = datetime.now()
            result.status = JobStatus.SKIPPED
            result.outcome = "DUPLICATE_SKIPPED"
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
            self.scheduler.record_job_result(result)
            logger.info(f"⏭️ Skipped duplicate execution: {execution_id}")
            return result

        try:
            session = SessionLocal()
            try:
                if self.harvester:
                    harvested = self.harvester.run_harvest_batch(
                        session,
                        max_leads=max_leads,
                    )
                    result.leads_processed = harvested
                    result.leads_succeeded = harvested
                else:
                    result.leads_processed = 0
                    result.leads_succeeded = 0

                result.status = JobStatus.COMPLETED
                logger.info(f"✅ Harvest job completed: {result.leads_succeeded} leads discovered")

            finally:
                session.close()

        except Exception as e:
            result.status = JobStatus.FAILED
            result.error_message = str(e)
            result.outcome = "FAILURE"
            logger.error(f"❌ Harvest job failed: {str(e)}")

        result.completed_at = datetime.now()
        result.duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()
        
        # Set success outcome if not already set
        if result.outcome == "SUCCESS" and result.status == JobStatus.COMPLETED:
            result.outcome = "SUCCESS"

        self.scheduler.record_job_result(result)
        self._update_execution_result(execution_id, result)  # PHASE B: Update DB record
        return result

    def run_scoring(
        self,
        max_leads: int = 100,
        campaign_id: Optional[int] = None,
    ) -> JobResult:
        """Run scoring job: compute ICP fit and opportunity scores."""
        start_time = datetime.now()
        result = JobResult(
            job_type=JobType.SCORE,
            status=JobStatus.RUNNING,
            started_at=start_time,
            completed_at=None,
            duration_seconds=0,
        )

        try:
            session = SessionLocal()
            try:
                if self.scorer:
                    scored = self.scorer.batch_score_leads(
                        session,
                        max_leads=max_leads,
                        campaign_id=campaign_id,
                    )
                    result.leads_processed = scored
                    result.leads_succeeded = scored
                else:
                    result.leads_processed = 0
                    result.leads_succeeded = 0

                result.status = JobStatus.COMPLETED
                logger.info(f"✅ Scoring job completed: {result.leads_succeeded} leads scored")

            finally:
                session.close()

        except Exception as e:
            result.status = JobStatus.FAILED
            result.error_message = str(e)
            logger.error(f"❌ Scoring job failed: {str(e)}")

        result.completed_at = datetime.now()
        result.duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        self.scheduler.record_job_result(result)
        return result

    def run_qualification(
        self,
        max_leads: int = 100,
        campaign_id: Optional[int] = None,
    ) -> JobResult:
        """Run qualification job: filter and auto-qualify leads."""
        start_time = datetime.now()
        result = JobResult(
            job_type=JobType.QUALIFY,
            status=JobStatus.RUNNING,
            started_at=start_time,
            completed_at=None,
            duration_seconds=0,
        )

        try:
            session = SessionLocal()
            try:
                if self.qualifier:
                    qualified = self.qualifier.batch_qualify_leads(
                        session,
                        max_leads=max_leads,
                        campaign_id=campaign_id,
                    )
                    result.leads_processed = qualified
                    result.leads_succeeded = qualified
                else:
                    result.leads_processed = 0
                    result.leads_succeeded = 0

                result.status = JobStatus.COMPLETED
                logger.info(f"✅ Qualification job completed: {result.leads_succeeded} leads qualified")

            finally:
                session.close()

        except Exception as e:
            result.status = JobStatus.FAILED
            result.error_message = str(e)
            logger.error(f"❌ Qualification job failed: {str(e)}")

        result.completed_at = datetime.now()
        result.duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        self.scheduler.record_job_result(result)
        return result

    def run_routing(
        self,
        max_leads: int = 100,
        campaign_id: Optional[int] = None,
    ) -> JobResult:
        """Run routing job: assign leads to nurture sequences."""
        start_time = datetime.now()
        result = JobResult(
            job_type=JobType.ROUTE,
            status=JobStatus.RUNNING,
            started_at=start_time,
            completed_at=None,
            duration_seconds=0,
        )

        try:
            session = SessionLocal()
            try:
                if self.router:
                    routed = self.router.batch_route_leads(
                        session,
                        max_leads=max_leads,
                        campaign_id=campaign_id,
                    )
                    result.leads_processed = routed
                    result.leads_succeeded = routed
                else:
                    result.leads_processed = 0
                    result.leads_succeeded = 0

                result.status = JobStatus.COMPLETED
                logger.info(f"✅ Routing job completed: {result.leads_succeeded} leads routed")

            finally:
                session.close()

        except Exception as e:
            result.status = JobStatus.FAILED
            result.error_message = str(e)
            logger.error(f"❌ Routing job failed: {str(e)}")

        result.completed_at = datetime.now()
        result.duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        self.scheduler.record_job_result(result)
        return result

    def run_nurture(
        self,
        max_leads: int = 50,
        campaign_id: Optional[int] = None,
    ) -> JobResult:
        """Run nurture job: execute next step in email sequences."""
        start_time = datetime.now()
        result = JobResult(
            job_type=JobType.NURTURE,
            status=JobStatus.RUNNING,
            started_at=start_time,
            completed_at=None,
            duration_seconds=0,
        )

        try:
            session = SessionLocal()
            try:
                if self.nurture:
                    leads_to_nurture = self.nurture.get_leads_to_nurture(session)

                    if max_leads > 0:
                        leads_to_nurture = leads_to_nurture[:max_leads]

                    executed = 0
                    for lead in leads_to_nurture:
                        try:
                            decision = self.nurture.evaluate_lead_nurture(lead)
                            if decision.should_send:
                                self.nurture.send_email(lead, decision.template)
                                executed += 1
                        except Exception as e:
                            logger.warning(f"Failed to nurture lead {lead.id}: {str(e)}")
                            result.leads_failed += 1

                    result.leads_processed = len(leads_to_nurture)
                    result.leads_succeeded = executed
                else:
                    result.leads_processed = 0
                    result.leads_succeeded = 0

                result.status = JobStatus.COMPLETED
                logger.info(f"✅ Nurture job completed: {result.leads_succeeded} emails sent")

            finally:
                session.close()

        except Exception as e:
            result.status = JobStatus.FAILED
            result.error_message = str(e)
            logger.error(f"❌ Nurture job failed: {str(e)}")

        result.completed_at = datetime.now()
        result.duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        self.scheduler.record_job_result(result)
        return result

    def run_full_pipeline(
        self,
        max_leads_per_stage: int = 100,
        campaign_id: Optional[int] = None,
    ) -> Tuple[JobResult, JobResult, JobResult, JobResult, JobResult]:
        """Run complete daily pipeline: Harvest → Score → Qualify → Route → Nurture."""
        logger.info("=" * 80)
        logger.info("🚀 STARTING DAILY LEAD PIPELINE")
        logger.info("=" * 80)

        # Run each stage in sequence
        harvest_result = self.run_harvest(max_leads_per_stage, campaign_id)
        score_result = self.run_scoring(max_leads_per_stage, campaign_id)
        qualify_result = self.run_qualification(max_leads_per_stage, campaign_id)
        route_result = self.run_routing(max_leads_per_stage, campaign_id)
        nurture_result = self.run_nurture(max_leads_per_stage // 2, campaign_id)

        logger.info("=" * 80)
        logger.info("✅ DAILY PIPELINE COMPLETE")
        logger.info("=" * 80)
        logger.info(f"  Harvested: {harvest_result.leads_succeeded} leads")
        logger.info(f"  Scored: {score_result.leads_succeeded} leads")
        logger.info(f"  Qualified: {qualify_result.leads_succeeded} leads")
        logger.info(f"  Routed: {route_result.leads_succeeded} leads")
        logger.info(f"  Nurtured: {nurture_result.leads_succeeded} emails sent")
        logger.info("=" * 80)

        return harvest_result, score_result, qualify_result, route_result, nurture_result

    def get_scheduler_status(self) -> Dict[str, any]:
        """Get current scheduler status and upcoming jobs."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "jobs": {},
            "overall_health": "healthy",
        }

        # Check each job type
        for job_type in JobType:
            if job_type == JobType.FULL_PIPELINE:
                continue

            config = self.scheduler.get_job_config(job_type)
            metrics = self.scheduler.get_metrics(job_type)
            next_run = self.scheduler.get_next_run_time(job_type)
            hours_until = self.scheduler.get_hours_until_next_run(job_type)

            status["jobs"][job_type.value] = {
                "enabled": config.enabled if config else False,
                "scheduled_time": f"{config.run_hour:02d}:{config.run_minute:02d}" if config else "N/A",
                "next_run": next_run.isoformat() if next_run else None,
                "hours_until_next_run": round(hours_until, 2),
                "health": metrics.health_status if metrics else "unknown",
                "success_rate": round(metrics.success_rate, 2) if metrics else 0,
                "last_run": metrics.last_run_at.isoformat() if metrics and metrics.last_run_at else None,
                "consecutive_failures": metrics.consecutive_failures if metrics else 0,
            }

            # Update overall health
            if metrics and metrics.health_status == "failed":
                status["overall_health"] = "failed"
            elif status["overall_health"] != "failed" and metrics and metrics.health_status == "degraded":
                status["overall_health"] = "degraded"

        return status

    def get_cron_dashboard(self) -> Dict[str, any]:
        """Get comprehensive dashboard data for monitoring."""
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "scheduler_status": self.get_scheduler_status(),
            "job_metrics": {},
            "recent_jobs": [],
        }

        # Collect metrics for each job type
        all_metrics = self.scheduler.get_all_metrics()
        for job_type, metrics in all_metrics.items():
            if job_type == JobType.FULL_PIPELINE:
                continue

            dashboard["job_metrics"][job_type.value] = {
                "total_runs": metrics.total_runs,
                "successful_runs": metrics.successful_runs,
                "failed_runs": metrics.failed_runs,
                "success_rate": round(metrics.success_rate, 2),
                "total_leads_processed": metrics.total_leads_processed,
                "total_leads_succeeded": metrics.total_leads_succeeded,
                "lead_success_rate": round(metrics.lead_success_rate, 2),
                "average_duration_seconds": round(metrics.average_harvest_duration, 2),
                "health_status": metrics.health_status,
            }

        # Include recent job history (last 10 jobs)
        for result in self.scheduler.job_history[-10:]:
            dashboard["recent_jobs"].append({
                "job_type": result.job_type.value,
                "status": result.status.value,
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "duration_seconds": round(result.duration_seconds, 2),
                "leads_processed": result.leads_processed,
                "leads_succeeded": result.leads_succeeded,
                "leads_failed": result.leads_failed,
                "error": result.error_message,
            })

        return dashboard
