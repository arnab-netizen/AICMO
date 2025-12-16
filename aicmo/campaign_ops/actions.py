"""
Campaign Operations AOL Action Handlers

Handles autonomy orchestration events for campaign management:
- CAMPAIGN_TICK: Update task statuses, escalate overdue
- ESCALATE_OVERDUE_TASKS: Create escalation tasks
- WEEKLY_CAMPAIGN_SUMMARY: Generate and store weekly reports

All handlers are SAFE MODE (no posting, no external calls).
Purely database updates and task/escalation creation.
"""

import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from aicmo.campaign_ops import repo
from aicmo.campaign_ops.service import CampaignOpsService
from aicmo.orchestration.queue import ActionQueue
from aicmo.orchestration.models import AOLAction

logger = logging.getLogger(__name__)


# ============================================================================
# AOL Action Handlers
# ============================================================================

def handle_campaign_tick(
    session: Session,
    action_id: int,
    payload: dict,
    proof_mode: bool = True,
) -> None:
    """
    CAMPAIGN_TICK handler - Update campaign task statuses and detect overdue.
    
    Payload:
    {
      "campaign_id": 5,
      "idempotency_key": "campaign_tick_5_2025-12-16",
    }
    
    Actions:
    1. Find all tasks for campaign
    2. Update PENDING -> DUE if due_at is in past hour
    3. Update PENDING -> OVERDUE if due_at > 1 hour past
    4. If overdue tasks exist, enqueue ESCALATE_OVERDUE_TASKS
    """
    try:
        campaign_id = payload.get("campaign_id")
        if not campaign_id:
            error_msg = "Missing campaign_id in payload"
            ActionQueue.log_execution(session, action_id, "ERROR", error_msg)
            ActionQueue.mark_failed(session, action_id, error_msg)
            return
        
        # Get all active tasks for campaign
        from aicmo.campaign_ops.models import OperatorTask, TaskStatus
        
        tasks = session.query(OperatorTask).filter(
            OperatorTask.campaign_id == campaign_id,
            OperatorTask.status.in_([TaskStatus.PENDING.value, TaskStatus.DUE.value]),
        ).all()
        
        now = datetime.utcnow()
        updated_count = 0
        overdue_count = 0
        
        for task in tasks:
            # Check if task is overdue
            if task.due_at < now and task.status != TaskStatus.OVERDUE.value:
                task.status = TaskStatus.OVERDUE.value
                task.updated_at = now
                updated_count += 1
                overdue_count += 1
            
            # Check if task is due soon (within next hour)
            elif task.due_at < now + timedelta(hours=1) and task.status == TaskStatus.PENDING.value:
                task.status = TaskStatus.DUE.value
                task.updated_at = now
                updated_count += 1
        
        session.commit()
        
        notes = f"Updated {updated_count} tasks, {overdue_count} overdue"
        
        # If overdue tasks, trigger escalation
        if overdue_count > 0:
            ActionQueue.enqueue_action(
                session,
                action_type="ESCALATE_OVERDUE_TASKS",
                payload={"campaign_id": campaign_id, "task_count": overdue_count},
                idempotency_key=f"escalate_{campaign_id}_{now.isoformat()}",
            )
            notes += " | Escalation queued"
        
        ActionQueue.log_execution(session, action_id, "SUCCESS", notes)
        ActionQueue.mark_success(session, action_id, notes)
        
        logger.info(f"[CAMPAIGN_TICK] {notes}")
    
    except Exception as e:
        error_msg = f"Campaign tick failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        ActionQueue.log_execution(session, action_id, "ERROR", error_msg)
        ActionQueue.mark_retry(session, action_id, error_msg)


def handle_escalate_overdue_tasks(
    session: Session,
    action_id: int,
    payload: dict,
    proof_mode: bool = True,
) -> None:
    """
    ESCALATE_OVERDUE_TASKS handler - Create an escalation task for operator.
    
    Payload:
    {
      "campaign_id": 5,
      "task_count": 3,
    }
    
    Actions:
    1. Create a high-priority REVIEW task
    2. Set as DUE immediately
    3. Include list of overdue tasks in instructions
    4. Log escalation in audit
    """
    try:
        campaign_id = payload.get("campaign_id")
        if not campaign_id:
            error_msg = "Missing campaign_id in payload"
            ActionQueue.log_execution(session, action_id, "ERROR", error_msg)
            ActionQueue.mark_failed(session, action_id, error_msg)
            return
        
        from aicmo.campaign_ops.models import OperatorTask, TaskStatus, TaskType
        
        # Get overdue tasks
        overdue_tasks = session.query(OperatorTask).filter(
            OperatorTask.campaign_id == campaign_id,
            OperatorTask.status == TaskStatus.OVERDUE.value,
        ).all()
        
        if not overdue_tasks:
            ActionQueue.log_execution(session, action_id, "SUCCESS", "No overdue tasks to escalate")
            ActionQueue.mark_success(session, action_id, "No overdue tasks")
            return
        
        # Build task instructions listing overdue items
        overdue_list = "\n".join([
            f"  - {t.title} (due: {t.due_at.strftime('%Y-%m-%d %H:%M')})"
            for t in overdue_tasks
        ])
        
        instructions = f"""⚠️ ESCALATION: {len(overdue_tasks)} OVERDUE TASKS

Review and resolve the following overdue tasks immediately:

{overdue_list}

ACTION ITEMS:
1. For each task below, either:
   a) COMPLETE it and mark DONE with proof, OR
   b) BLOCK it with reason if cannot be completed, OR
   c) RESCHEDULE it if circumstances changed

2. Mark this escalation task as DONE once all overdue tasks are addressed.

IMPACT:
- Overdue tasks affect campaign execution timeline
- Each day delayed reduces engagement window
- Client communication may be impacted
"""
        
        # Create escalation task (high priority, due NOW)
        now = datetime.utcnow()
        escalation_task = repo.create_operator_task(
            session,
            campaign_id=campaign_id,
            task_type=TaskType.REVIEW.value,
            platform="internal",
            due_at=now,  # Due immediately
            title=f"⚠️ ESCALATION: {len(overdue_tasks)} Overdue Tasks",
            instructions_text=instructions,
            status=TaskStatus.DUE.value,  # Mark as DUE so it shows up
        )
        
        # Log escalation
        repo.create_audit_log(
            session,
            actor="aol_daemon",
            action="escalated_overdue_tasks",
            entity_type="campaign",
            entity_id=campaign_id,
            notes=f"Created escalation task {escalation_task.id} for {len(overdue_tasks)} overdue tasks",
        )
        
        notes = f"Created escalation task {escalation_task.id} for {len(overdue_tasks)} overdue items"
        ActionQueue.log_execution(session, action_id, "SUCCESS", notes)
        ActionQueue.mark_success(session, action_id, notes)
        
        logger.warning(f"[ESCALATE_OVERDUE] {notes}")
    
    except Exception as e:
        error_msg = f"Escalation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        ActionQueue.log_execution(session, action_id, "ERROR", error_msg)
        ActionQueue.mark_retry(session, action_id, error_msg)


def handle_weekly_campaign_summary(
    session: Session,
    action_id: int,
    payload: dict,
    proof_mode: bool = True,
) -> None:
    """
    WEEKLY_CAMPAIGN_SUMMARY handler - Generate and store weekly report.
    
    Payload:
    {
      "campaign_id": 5,
      "week_start": "2025-12-01T00:00:00",
    }
    
    Actions:
    1. Generate weekly summary using CampaignOpsService
    2. Store summary as audit log
    3. Create a REVIEW task with summary for operator
    """
    try:
        campaign_id = payload.get("campaign_id")
        if not campaign_id:
            error_msg = "Missing campaign_id in payload"
            ActionQueue.log_execution(session, action_id, "ERROR", error_msg)
            ActionQueue.mark_failed(session, action_id, error_msg)
            return
        
        service = CampaignOpsService(session)
        
        # Generate summary
        summary = service.generate_weekly_summary(campaign_id)
        
        # Log as audit
        repo.create_audit_log(
            session,
            actor="aol_daemon",
            action="generated_weekly_summary",
            entity_type="campaign",
            entity_id=campaign_id,
            after_json={
                "week_start": summary.week_start.isoformat(),
                "week_end": summary.week_end.isoformat(),
                "tasks_planned": summary.tasks_planned,
                "tasks_completed": summary.tasks_completed,
                "tasks_overdue": summary.tasks_overdue,
            },
            notes=summary.notes[:200],  # First 200 chars
        )
        
        # Create summary task for operator
        now = datetime.utcnow()
        from aicmo.campaign_ops.models import TaskType, TaskStatus
        
        repo.create_operator_task(
            session,
            campaign_id=campaign_id,
            task_type=TaskType.ANALYZE.value,
            platform="internal",
            due_at=now,
            title="📊 Weekly Campaign Summary",
            instructions_text=f"Review this week's performance:\n\n{summary.notes}",
            status=TaskStatus.PENDING.value,
        )
        
        notes = f"Generated weekly summary for week {summary.week_start.strftime('%Y-%m-%d')}"
        ActionQueue.log_execution(session, action_id, "SUCCESS", notes)
        ActionQueue.mark_success(session, action_id, notes)
        
        logger.info(f"[WEEKLY_SUMMARY] {notes}")
    
    except Exception as e:
        error_msg = f"Summary generation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        ActionQueue.log_execution(session, action_id, "ERROR", error_msg)
        ActionQueue.mark_retry(session, action_id, error_msg)
