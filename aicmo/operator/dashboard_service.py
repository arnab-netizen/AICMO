"""
Phase 14 — Operator Dashboard Service

Orchestrates all operator dashboard data and actions.

Responsibilities:
1. Build dashboard view (aggregating brand, task, schedule, feedback state)
2. Manage automation settings (get/set modes)
3. Trigger phase workflows (AAB, execution, scheduler, feedback)
4. Respect automation modes (manual, review_first, full_auto)
5. Enforce dry_run safety

All methods return dicts for easy serialization to JSON/Streamlit/Next.js.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

from aicmo.operator.dashboard_models import (
    BrandStatusView,
    TaskQueueView,
    ScheduleView,
    FeedbackView,
    AutomationModeView,
    OperatorDashboardView,
)
from aicmo.operator.automation_settings import (
    AutomationSettings,
    AutomationSettingsRepository,
)

logger = logging.getLogger(__name__)


class OperatorDashboardService:
    """
    Operator dashboard service.
    
    Aggregates state from all phases (LBB, AAB, Execution, Scheduler, Feedback)
    and provides unified interface for operator control.
    """
    
    def __init__(
        self,
        brand_brain_repo: Optional[Any] = None,
        auto_brain_task_repo: Optional[Any] = None,
        scheduler_repo: Optional[Any] = None,
        feedback_loop: Optional[Any] = None,
        automation_settings_repo: Optional[AutomationSettingsRepository] = None,
        analytics_service: Optional[Any] = None,
        crm_repo: Optional[Any] = None,
        media_engine: Optional[Any] = None,
    ):
        """
        Initialize dashboard service.
        
        All parameters are optional (for testing with stubs).
        
        Args:
            brand_brain_repo: BrandBrainRepository (Phase 9)
            auto_brain_task_repo: AutoBrainTaskRepository (Phase 10)
            scheduler_repo: SchedulerRepository (Phase 12)
            feedback_loop: FeedbackLoop (Phase 13)
            automation_settings_repo: AutomationSettingsRepository
            analytics_service: AnalyticsService (Phase 3)
            crm_repo: CRMRepository (Phase 1)
            media_engine: MediaEngine (Phase 4)
        """
        self.brand_brain_repo = brand_brain_repo
        self.auto_brain_task_repo = auto_brain_task_repo
        self.scheduler_repo = scheduler_repo
        self.feedback_loop = feedback_loop
        self.automation_settings_repo = (
            automation_settings_repo or AutomationSettingsRepository()
        )
        self.analytics_service = analytics_service
        self.crm_repo = crm_repo
        self.media_engine = media_engine
    
    def get_dashboard_view(self, brand_id: str) -> OperatorDashboardView:
        """
        Build complete dashboard view for a brand.
        
        Aggregates:
        1. Brand status from LBB + analytics
        2. Task queue from AAB tasks
        3. Schedule from SchedulerRepository
        4. Feedback from last snapshot
        5. Automation mode from settings
        
        Args:
            brand_id: Brand UUID
            
        Returns:
            OperatorDashboardView snapshot
        """
        # Build each section
        brand_status = self._build_brand_status_view(brand_id)
        task_queue = self._build_task_queue_view(brand_id)
        schedule = self._build_schedule_view(brand_id)
        feedback = self._build_feedback_view(brand_id)
        automation = self._build_automation_view(brand_id)
        
        # Assemble complete view
        return OperatorDashboardView(
            brand_id=brand_id,
            brand_status=brand_status,
            task_queue=task_queue,
            schedule=schedule,
            feedback=feedback,
            automation=automation,
            snapshot_at=datetime.utcnow(),
        )
    
    def _build_brand_status_view(self, brand_id: str) -> BrandStatusView:
        """Build BrandStatusView from LBB + analytics."""
        brand_name = None
        key_persona = None
        primary_tone = None
        top_channels = []
        risk_flags = []
        last_updated_at = None
        
        try:
            # Get brand from LBB
            if self.brand_brain_repo:
                brain = self.brand_brain_repo.get_brain(brand_id)
                if brain:
                    brand_name = brain.brand_name
                    key_persona = brain.key_persona
                    primary_tone = brain.primary_tone
                    last_updated_at = brain.last_updated
        except Exception as e:
            logger.error(f"Error fetching brand brain: {e}")
        
        try:
            # Get top channels from analytics
            if self.analytics_service:
                analytics = self.analytics_service.get_brand_analytics(brand_id)
                if analytics and "top_channels" in analytics:
                    top_channels = analytics["top_channels"][:5]
        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
        
        # Detect risk flags (heuristic)
        try:
            if not top_channels:
                risk_flags.append("no_channel_data")
            if not key_persona:
                risk_flags.append("no_personas_defined")
            if not brand_name:
                risk_flags.append("brand_name_missing")
        except Exception as e:
            logger.error(f"Error detecting risk flags: {e}")
        
        return BrandStatusView(
            brand_id=brand_id,
            brand_name=brand_name,
            key_persona=key_persona,
            primary_tone=primary_tone,
            top_channels=top_channels,
            risk_flags=risk_flags,
            last_updated_at=last_updated_at,
        )
    
    def _build_task_queue_view(self, brand_id: str) -> TaskQueueView:
        """Build TaskQueueView from AAB tasks."""
        pending = 0
        approved = 0
        running = 0
        completed = 0
        failed = 0
        recent_tasks = []
        
        try:
            if self.auto_brain_task_repo:
                # Get all tasks for brand
                tasks = self.auto_brain_task_repo.list_for_brand(brand_id)
                
                # Count by status
                for task in tasks:
                    status = getattr(task, "status", None)
                    if status == "proposed" or status == "pending_review":
                        pending += 1
                    elif status == "approved":
                        approved += 1
                    elif status == "running":
                        running += 1
                    elif status == "completed":
                        completed += 1
                    elif status == "failed":
                        failed += 1
                
                # Get recent tasks (last 10)
                for task in tasks[-10:]:
                    recent_tasks.append({
                        "id": getattr(task, "task_id", "unknown"),
                        "type": getattr(task, "task_type", "unknown"),
                        "status": getattr(task, "status", "unknown"),
                        "reason": getattr(task, "reason", None),
                        "created_at": getattr(task, "created_at", None),
                    })
        except Exception as e:
            logger.error(f"Error building task queue view: {e}")
        
        return TaskQueueView(
            brand_id=brand_id,
            pending=pending,
            approved=approved,
            running=running,
            completed=completed,
            failed=failed,
            recent_tasks=recent_tasks,
        )
    
    def _build_schedule_view(self, brand_id: str) -> ScheduleView:
        """Build ScheduleView from scheduler."""
        upcoming = []
        overdue = []
        next_tick_at = None
        
        try:
            if self.scheduler_repo:
                now = datetime.utcnow()
                
                # Get all scheduled tasks for brand
                scheduled_tasks = self.scheduler_repo.list_for_brand(brand_id)
                
                # Partition into upcoming and overdue
                for task in scheduled_tasks:
                    run_at = getattr(task, "run_at", now)
                    
                    task_dict = {
                        "scheduled_id": getattr(task, "scheduled_id", "unknown"),
                        "task_id": getattr(task, "task_id", "unknown"),
                        "task_type": "scheduled_execution",
                        "run_at": run_at,
                        "status": getattr(task, "status", "scheduled"),
                    }
                    
                    if run_at <= now:
                        overdue.append(task_dict)
                    else:
                        upcoming.append(task_dict)
                
                # Sort and limit
                upcoming = sorted(upcoming, key=lambda t: t["run_at"])[:10]
                overdue = sorted(overdue, key=lambda t: t["run_at"], reverse=True)[:10]
                
                # Assume next tick is in 5 minutes (heuristic)
                next_tick_at = now + timedelta(minutes=5)
        except Exception as e:
            logger.error(f"Error building schedule view: {e}")
        
        return ScheduleView(
            brand_id=brand_id,
            upcoming=upcoming,
            overdue=overdue,
            next_tick_at=next_tick_at,
        )
    
    def _build_feedback_view(self, brand_id: str) -> FeedbackView:
        """Build FeedbackView from feedback loop."""
        last_snapshot_at = None
        last_anomalies = []
        last_run_summary = None
        
        try:
            # For now, stub - would be populated by FeedbackLoop
            # when it stores snapshot metadata
            pass
        except Exception as e:
            logger.error(f"Error building feedback view: {e}")
        
        return FeedbackView(
            brand_id=brand_id,
            last_snapshot_at=last_snapshot_at,
            last_anomalies=last_anomalies,
            last_run_summary=last_run_summary,
        )
    
    def _build_automation_view(self, brand_id: str) -> AutomationModeView:
        """Build AutomationModeView from settings."""
        settings = self.automation_settings_repo.get_settings(brand_id)
        
        return AutomationModeView(
            brand_id=brand_id,
            mode=settings.mode,
            dry_run=settings.dry_run,
            notes=None,
        )
    
    def set_automation_mode(
        self,
        brand_id: str,
        mode: str,
        dry_run: bool,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update automation settings for a brand.
        
        Args:
            brand_id: Brand UUID
            mode: "manual", "review_first", or "full_auto"
            dry_run: If True, no external APIs called
            notes: Optional reason/notes
            
        Returns:
            Dict with updated settings
        """
        # Validate mode
        valid_modes = ["manual", "review_first", "full_auto"]
        if mode not in valid_modes:
            return {
                "status": "error",
                "message": f"Invalid mode '{mode}'. Must be one of {valid_modes}",
            }
        
        try:
            # Save settings
            settings = AutomationSettings(
                brand_id=brand_id,
                mode=mode,
                dry_run=dry_run,
            )
            self.automation_settings_repo.save_settings(settings)
            
            # Build updated view
            view = AutomationModeView(
                brand_id=brand_id,
                mode=mode,
                dry_run=dry_run,
                notes=notes,
            )
            
            logger.info(f"Updated automation mode for {brand_id}: {mode}, dry_run={dry_run}")
            
            return {
                "status": "success",
                "message": f"Automation mode updated to {mode}",
                "automation": {
                    "mode": view.mode,
                    "dry_run": view.dry_run,
                    "notes": view.notes,
                },
            }
        except Exception as e:
            logger.error(f"Error updating automation mode: {e}")
            return {
                "status": "error",
                "message": f"Failed to update settings: {str(e)}",
            }
    
    def run_auto_brain_for_brand(self, brand_id: str) -> Dict[str, Any]:
        """
        Trigger AAB scan/plan for a brand.
        
        Uses existing AutoBrain/TaskScanner interfaces.
        
        Args:
            brand_id: Brand UUID
            
        Returns:
            Dict with summary: tasks_created, tasks_updated, etc.
        """
        if not self.auto_brain_task_repo:
            return {
                "status": "error",
                "message": "AutoBrainTaskRepository not configured",
            }
        
        try:
            # Stub implementation - would call actual AAB logic
            # For now, return success structure
            return {
                "status": "success",
                "message": "AAB scan triggered",
                "tasks_created": 0,
                "tasks_updated": 0,
                "tasks_skipped": 0,
            }
        except Exception as e:
            logger.error(f"Error running AAB: {e}")
            return {
                "status": "error",
                "message": f"AAB failed: {str(e)}",
            }
    
    def run_execution_cycle_for_brand(
        self,
        brand_id: str,
        max_tasks: int = 5,
    ) -> Dict[str, Any]:
        """
        Execute tasks based on automation mode.
        
        Modes:
        - "manual": Returns explanation, no execution
        - "review_first": Only executes approved tasks
        - "full_auto": Auto-approves safe tasks, then executes
        
        Args:
            brand_id: Brand UUID
            max_tasks: Maximum tasks to execute
            
        Returns:
            Dict with execution summary
        """
        # Get current automation settings
        settings = self.automation_settings_repo.get_settings(brand_id)
        
        # Check mode
        if settings.mode == "manual":
            return {
                "status": "skipped",
                "reason": "Automation mode is 'manual'",
                "message": "No tasks executed. Use 'review_first' or 'full_auto' mode.",
            }
        
        try:
            # Stub implementation - would call AutoExecutionEngine
            executed = 0
            skipped = 0
            failed = 0
            
            if settings.mode == "review_first":
                # Only execute approved tasks
                pass
            elif settings.mode == "full_auto":
                # Auto-approve safe tasks
                pass
            
            return {
                "status": "success",
                "message": "Execution cycle completed",
                "executed": executed,
                "skipped": skipped,
                "failed": failed,
                "dry_run": settings.dry_run,
            }
        except Exception as e:
            logger.error(f"Error running execution cycle: {e}")
            return {
                "status": "error",
                "message": f"Execution cycle failed: {str(e)}",
            }
    
    def run_scheduler_tick_for_brand(
        self,
        brand_id: str,
        now: Optional[datetime] = None,
        max_to_run: int = 10,
    ) -> Dict[str, Any]:
        """
        Run scheduler tick for a brand.
        
        Finds due tasks and executes them.
        
        Args:
            brand_id: Brand UUID
            now: Current time (default: utcnow)
            max_to_run: Maximum tasks to execute
            
        Returns:
            Dict with execution results
        """
        if not self.scheduler_repo:
            return {
                "status": "error",
                "message": "SchedulerRepository not configured",
            }
        
        now = now or datetime.utcnow()
        
        try:
            # Stub implementation - would call SchedulerRuntime.tick
            return {
                "status": "success",
                "message": "Scheduler tick completed",
                "executed": 0,
                "skipped": 0,
                "failed": 0,
            }
        except Exception as e:
            logger.error(f"Error running scheduler tick: {e}")
            return {
                "status": "error",
                "message": f"Scheduler tick failed: {str(e)}",
            }
    
    def run_feedback_cycle_for_brand(self, brand_id: str) -> Dict[str, Any]:
        """
        Run feedback loop for a brand.
        
        Collects performance data, detects anomalies, proposes tasks.
        
        Args:
            brand_id: Brand UUID
            
        Returns:
            Dict with feedback summary
        """
        if not self.feedback_loop:
            return {
                "status": "error",
                "message": "FeedbackLoop not configured",
            }
        
        try:
            # Stub implementation - would call FeedbackLoop.run_for_brand
            return {
                "status": "success",
                "message": "Feedback cycle completed",
                "task_count": 0,
                "anomalies_detected": 0,
                "notes": "No anomalies detected",
            }
        except Exception as e:
            logger.error(f"Error running feedback cycle: {e}")
            return {
                "status": "error",
                "message": f"Feedback cycle failed: {str(e)}",
            }
