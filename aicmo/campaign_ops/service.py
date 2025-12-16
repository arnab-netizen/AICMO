"""
Campaign Operations Service - Business logic layer.

Orchestrates campaign creation, planning, calendar generation, task management,
and reporting. No direct database access; uses repo layer.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json

from aicmo.campaign_ops import repo
from aicmo.campaign_ops.models import (
    Campaign,
    CampaignStatus,
    TaskStatus,
    TaskType,
    CalendarItem,
    OperatorTask,
)
from aicmo.campaign_ops.schemas import (
    CampaignCreate,
    CampaignRead,
    CampaignPlanCreate,
    CampaignPlanRead,
    CalendarItemCreate,
    CalendarItemRead,
    OperatorTaskRead,
    MetricEntryCreate,
    WeeklySummary,
)


class CampaignOpsService:
    """Service layer for campaign operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    # ========================================================================
    # Campaign Management
    # ========================================================================
    
    def create_campaign(self, campaign_data: CampaignCreate) -> CampaignRead:
        """Create a new campaign."""
        campaign = repo.create_campaign(
            self.session,
            name=campaign_data.name,
            client_name=campaign_data.client_name,
            venture_name=campaign_data.venture_name,
            objective=campaign_data.objective,
            platforms=campaign_data.platforms,
            start_date=campaign_data.start_date,
            end_date=campaign_data.end_date,
            cadence=campaign_data.cadence,
            primary_cta=campaign_data.primary_cta,
            lead_capture_method=campaign_data.lead_capture_method,
            status=CampaignStatus.PLANNED.value,
        )
        
        # Log creation
        repo.create_audit_log(
            self.session,
            actor="operator",
            action="created_campaign",
            entity_type="campaign",
            entity_id=campaign.id,
            after_json=self._model_to_dict(campaign),
        )
        
        return self._campaign_to_schema(campaign)
    
    def get_campaign(self, campaign_id: int) -> Optional[CampaignRead]:
        """Get campaign by ID."""
        campaign = repo.get_campaign(self.session, campaign_id)
        return self._campaign_to_schema(campaign) if campaign else None
    
    def list_campaigns(self, status: Optional[str] = None) -> List[CampaignRead]:
        """List campaigns."""
        campaigns = repo.list_campaigns(self.session, status=status)
        return [self._campaign_to_schema(c) for c in campaigns]
    
    def activate_campaign(self, campaign_id: int) -> Optional[CampaignRead]:
        """Set campaign status to ACTIVE."""
        campaign = repo.update_campaign(
            self.session,
            campaign_id,
            status=CampaignStatus.ACTIVE.value,
        )
        
        if campaign:
            repo.create_audit_log(
                self.session,
                actor="operator",
                action="activated_campaign",
                entity_type="campaign",
                entity_id=campaign_id,
            )
        
        return self._campaign_to_schema(campaign) if campaign else None
    
    # ========================================================================
    # Plan Generation
    # ========================================================================
    
    def generate_plan(
        self,
        campaign_id: int,
        angles: Optional[List[str]] = None,
        positioning: Optional[str] = None,
        messaging: Optional[Dict[str, List[str]]] = None,
        weekly_themes: Optional[List[str]] = None,
    ) -> Optional[CampaignPlanRead]:
        """
        Generate or store a campaign plan.
        
        Can be called manually (manual) or integrated with Strategy generator (aicmo).
        For now, stores what's provided. In future, can call existing Strategy module.
        """
        campaign = repo.get_campaign(self.session, campaign_id)
        if not campaign:
            return None
        
        # Get current version
        latest = repo.get_latest_plan(self.session, campaign_id)
        next_version = (latest.version + 1) if latest else 1
        
        # Create new plan
        plan = repo.create_plan(
            self.session,
            campaign_id=campaign_id,
            angles_json=angles,
            positioning_json=positioning,
            messaging_json=messaging,
            weekly_themes_json=weekly_themes,
            generated_by="manual",
            version=next_version,
        )
        
        repo.create_audit_log(
            self.session,
            actor="operator",
            action="generated_plan",
            entity_type="plan",
            entity_id=plan.id,
            after_json=self._model_to_dict(plan),
        )
        
        return self._plan_to_schema(plan)
    
    # ========================================================================
    # Calendar Generation
    # ========================================================================
    
    def generate_calendar(
        self,
        campaign_id: int,
        days_ahead: int = 14,
    ) -> List[CalendarItemRead]:
        """
        Generate calendar items from campaign cadence.
        
        Creates scheduled posts for the next N days based on platform cadence.
        """
        campaign = repo.get_campaign(self.session, campaign_id)
        if not campaign:
            return []
        
        calendar_items = []
        now = datetime.utcnow()
        
        for platform in campaign.platforms:
            posts_per_week = campaign.cadence.get(platform, 1)
            if posts_per_week <= 0:
                continue
            
            # Calculate interval between posts (in hours)
            interval_hours = (7 * 24) / posts_per_week
            
            # Schedule posts across the period
            for day in range(days_ahead):
                # Spread posts throughout the day (9am, 1pm, 5pm, etc.)
                post_count = max(1, int(posts_per_week / 7))
                for i in range(post_count):
                    hour = 9 + (i * 8)  # 9am, 5pm, etc.
                    if hour >= 24:
                        continue
                    
                    scheduled_at = now + timedelta(days=day, hours=hour - now.hour)
                    scheduled_at = scheduled_at.replace(hour=hour, minute=0, second=0, microsecond=0)
                    
                    # Skip if in the past
                    if scheduled_at <= now:
                        continue
                    
                    item = repo.create_calendar_item(
                        self.session,
                        campaign_id=campaign_id,
                        platform=platform,
                        content_type="post",
                        scheduled_at=scheduled_at,
                        title=f"{platform.capitalize()} Post - {scheduled_at.strftime('%a %I%p')}",
                        status=TaskStatus.PENDING.value,
                    )
                    calendar_items.append(self._calendar_to_schema(item))
        
        repo.create_audit_log(
            self.session,
            actor="operator",
            action="generated_calendar",
            entity_type="campaign",
            entity_id=campaign_id,
            notes=f"Generated {len(calendar_items)} calendar items for {days_ahead} days",
        )
        
        return calendar_items
    
    # ========================================================================
    # Task Generation
    # ========================================================================
    
    def generate_tasks_from_calendar(self, campaign_id: int) -> List[OperatorTaskRead]:
        """
        Create operator tasks from calendar items.
        
        For each calendar item, creates a POST task with WHERE+HOW instructions.
        """
        campaign = repo.get_campaign(self.session, campaign_id)
        if not campaign:
            return []
        
        calendar_items = repo.list_calendar_items(self.session, campaign_id)
        tasks = []
        
        from aicmo.campaign_ops.instructions import get_platform_sop
        
        for item in calendar_items:
            # Skip if already has a task
            existing_tasks = repo.list_operator_tasks(
                self.session,
                campaign_id,
                status=None,
            )
            if any(t.calendar_item_id == item.id for t in existing_tasks):
                continue
            
            # Get SOP instructions for this platform
            sop = get_platform_sop(item.platform, item.content_type)
            
            task = repo.create_operator_task(
                self.session,
                campaign_id=campaign_id,
                calendar_item_id=item.id,
                task_type=TaskType.POST.value,
                platform=item.platform,
                due_at=item.scheduled_at,
                title=f"Post to {item.platform}: {item.title}",
                instructions_text=sop,
                copy_text=item.copy_text,
                asset_ref=item.asset_ref,
                status=TaskStatus.PENDING.value,
            )
            tasks.append(self._task_to_schema(task))
        
        repo.create_audit_log(
            self.session,
            actor="operator",
            action="generated_tasks",
            entity_type="campaign",
            entity_id=campaign_id,
            notes=f"Generated {len(tasks)} operator tasks from calendar",
        )
        
        return tasks
    
    # ========================================================================
    # Task Management
    # ========================================================================
    
    def get_today_tasks(self, campaign_id: int) -> List[OperatorTaskRead]:
        """Get tasks due today."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        query = self.session.query(OperatorTask).filter(
            OperatorTask.campaign_id == campaign_id,
            OperatorTask.due_at >= today_start,
            OperatorTask.due_at < today_end,
            OperatorTask.status.in_([TaskStatus.PENDING.value, TaskStatus.DUE.value]),
        )
        
        tasks = query.order_by(OperatorTask.due_at).all()
        return [self._task_to_schema(t) for t in tasks]
    
    def get_overdue_tasks(self, campaign_id: int) -> List[OperatorTaskRead]:
        """Get overdue tasks."""
        now = datetime.utcnow()
        
        query = self.session.query(OperatorTask).filter(
            OperatorTask.campaign_id == campaign_id,
            OperatorTask.due_at < now,
            OperatorTask.status.in_([TaskStatus.PENDING.value, TaskStatus.DUE.value]),
        )
        
        tasks = query.order_by(OperatorTask.due_at).all()
        return [self._task_to_schema(t) for t in tasks]
    
    def get_upcoming_tasks(self, campaign_id: int, days_ahead: int = 7) -> List[OperatorTaskRead]:
        """Get tasks due in the next N days."""
        now = datetime.utcnow()
        future = now + timedelta(days=days_ahead)
        
        query = self.session.query(OperatorTask).filter(
            OperatorTask.campaign_id == campaign_id,
            OperatorTask.due_at >= now,
            OperatorTask.due_at <= future,
            OperatorTask.status.in_([TaskStatus.PENDING.value, TaskStatus.DUE.value]),
        )
        
        tasks = query.order_by(OperatorTask.due_at).all()
        return [self._task_to_schema(t) for t in tasks]
    
    def mark_task_complete(
        self,
        task_id: int,
        proof_type: str,
        proof_value: str,
    ) -> Optional[OperatorTaskRead]:
        """Mark a task as complete with proof."""
        task = repo.mark_task_done(
            self.session,
            task_id,
            proof_type=proof_type,
            proof_value=proof_value,
        )
        
        if task:
            repo.create_audit_log(
                self.session,
                actor="operator",
                action="completed_task",
                entity_type="task",
                entity_id=task_id,
                notes=f"Proof type: {proof_type}",
            )
            
            # Auto-create follow-up tasks if POST task
            if task.task_type == TaskType.POST.value:
                self._create_followup_tasks(task)
        
        return self._task_to_schema(task) if task else None
    
    def _create_followup_tasks(self, completed_post_task: OperatorTask) -> None:
        """
        Auto-create follow-up tasks after a POST is completed.
        
        Creates ENGAGE tasks at +2h and +24h to handle comments and engagement.
        """
        now = datetime.utcnow()
        
        # 2-hour engagement check
        repo.create_operator_task(
            self.session,
            campaign_id=completed_post_task.campaign_id,
            task_type=TaskType.ENGAGE.value,
            platform=completed_post_task.platform,
            due_at=now + timedelta(hours=2),
            title=f"Check comments on {completed_post_task.platform} post",
            instructions_text=f"Review and reply to early comments on your post.\nCopy to use: {self._get_generic_reply_script()}",
            status=TaskStatus.PENDING.value,
        )
        
        # 24-hour engagement check
        repo.create_operator_task(
            self.session,
            campaign_id=completed_post_task.campaign_id,
            task_type=TaskType.ENGAGE.value,
            platform=completed_post_task.platform,
            due_at=now + timedelta(hours=24),
            title=f"Follow-up on {completed_post_task.platform} post performance",
            instructions_text=f"Check final engagement metrics and DM interested prospects.\nSample reply: {self._get_generic_reply_script()}",
            status=TaskStatus.PENDING.value,
        )
    
    def _get_generic_reply_script(self) -> str:
        """Generic reply template."""
        return "Thanks for your interest! Happy to discuss this further. Feel free to reach out with questions."
    
    # ========================================================================
    # Reporting
    # ========================================================================
    
    def generate_weekly_summary(self, campaign_id: int) -> WeeklySummary:
        """Generate weekly campaign summary."""
        campaign = repo.get_campaign(self.session, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Calculate week boundaries
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7)
        
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_end.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count tasks
        all_week_tasks = self.session.query(OperatorTask).filter(
            OperatorTask.campaign_id == campaign_id,
            OperatorTask.due_at >= week_start,
            OperatorTask.due_at < week_end,
        ).all()
        
        tasks_planned = len(all_week_tasks)
        tasks_completed = len([t for t in all_week_tasks if t.status == TaskStatus.DONE.value])
        tasks_overdue = len([t for t in all_week_tasks if t.status == TaskStatus.OVERDUE.value])
        
        # Get metrics
        metrics = repo.list_metric_entries(
            self.session,
            campaign_id,
            start_date=week_start,
            end_date=week_end,
        )
        
        metrics_summary = {}
        for metric in metrics:
            platform = metric.platform
            if platform not in metrics_summary:
                metrics_summary[platform] = {}
            metrics_summary[platform][metric.metric_name] = metric.metric_value
        
        # Find top platform by engagement
        top_platform = None
        if metrics_summary:
            platform_engagement = {}
            for platform, metrics_dict in metrics_summary.items():
                engagement = metrics_dict.get("engagement", 0) + metrics_dict.get("clicks", 0)
                platform_engagement[platform] = engagement
            top_platform = max(platform_engagement, key=platform_engagement.get)
        
        # Generate notes
        notes = f"""
Weekly Campaign Summary: {campaign.name}
Week: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}

Tasks:
- Planned: {tasks_planned}
- Completed: {tasks_completed}
- Completion rate: {(tasks_completed / tasks_planned * 100) if tasks_planned > 0 else 0:.1f}%
- Overdue: {tasks_overdue}

Top Platform: {top_platform or 'N/A'}

Metrics by Platform:
{self._format_metrics(metrics_summary)}

Next Week Focus:
Review performance data above and adjust cadence/messaging as needed.
"""
        
        return WeeklySummary(
            week_start=week_start,
            week_end=week_end,
            tasks_planned=tasks_planned,
            tasks_completed=tasks_completed,
            tasks_overdue=tasks_overdue,
            top_platform=top_platform,
            metrics_summary=metrics_summary,
            notes=notes.strip(),
        )
    
    # ========================================================================
    # Helpers
    # ========================================================================
    
    def _campaign_to_schema(self, campaign: Campaign) -> CampaignRead:
        """Convert model to schema."""
        if not campaign:
            return None
        return CampaignRead(
            id=campaign.id,
            name=campaign.name,
            client_name=campaign.client_name,
            venture_name=campaign.venture_name,
            objective=campaign.objective,
            platforms=campaign.platforms or [],
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            cadence=campaign.cadence or {},
            primary_cta=campaign.primary_cta,
            lead_capture_method=campaign.lead_capture_method,
            status=campaign.status,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
    
    def _plan_to_schema(self, plan) -> CampaignPlanRead:
        if not plan:
            return None
        return CampaignPlanRead(
            id=plan.id,
            campaign_id=plan.campaign_id,
            angles_json=plan.angles_json,
            positioning_json=plan.positioning_json,
            messaging_json=plan.messaging_json,
            weekly_themes_json=plan.weekly_themes_json,
            generated_by=plan.generated_by,
            version=plan.version,
            created_at=plan.created_at,
        )
    
    def _calendar_to_schema(self, item: CalendarItem) -> CalendarItemRead:
        if not item:
            return None
        return CalendarItemRead(
            id=item.id,
            campaign_id=item.campaign_id,
            platform=item.platform,
            content_type=item.content_type,
            scheduled_at=item.scheduled_at,
            title=item.title,
            copy_text=item.copy_text,
            asset_ref=item.asset_ref,
            cta_text=item.cta_text,
            status=item.status,
            notes=item.notes,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
    
    def _task_to_schema(self, task: OperatorTask) -> OperatorTaskRead:
        if not task:
            return None
        return OperatorTaskRead(
            id=task.id,
            campaign_id=task.campaign_id,
            calendar_item_id=task.calendar_item_id,
            task_type=task.task_type,
            platform=task.platform,
            due_at=task.due_at,
            title=task.title,
            instructions_text=task.instructions_text,
            copy_text=task.copy_text,
            asset_ref=task.asset_ref,
            status=task.status,
            completion_proof_type=task.completion_proof_type,
            completion_proof_value=task.completion_proof_value,
            completed_at=task.completed_at,
            blocked_reason=task.blocked_reason,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
    
    def _model_to_dict(self, obj) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dict, with proper JSON serialization."""
        if not obj:
            return {}
        result = {}
        for c in obj.__table__.columns:
            value = getattr(obj, c.name)
            # Convert datetime to ISO format string for JSON serialization
            if isinstance(value, datetime):
                result[c.name] = value.isoformat()
            else:
                result[c.name] = value
        return result
    
    def _format_metrics(self, metrics_summary: Dict[str, Dict[str, float]]) -> str:
        """Format metrics for display."""
        lines = []
        for platform, metrics_dict in metrics_summary.items():
            lines.append(f"  {platform}:")
            for metric_name, value in metrics_dict.items():
                lines.append(f"    - {metric_name}: {value}")
        return "\n".join(lines) if lines else "  (No metrics recorded)"
