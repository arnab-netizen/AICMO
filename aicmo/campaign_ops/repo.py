"""
Campaign Operations Repository - Data access layer.

Pure CRUD functions for persistence. No business logic.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, inspect

from aicmo.campaign_ops.models import (
    Campaign,
    CampaignPlan,
    CalendarItem,
    OperatorTask,
    MetricEntry,
    OperatorAuditLog,
    CampaignStatus,
    TaskStatus,
)

# CAMPAIGN_OPS_FIX_START
def _verify_tables_exist(session: Session) -> None:
    """
    Verify all Campaign Ops tables exist in the database.
    
    Raises:
        RuntimeError: If any required tables are missing
    
    This is called on first repo operation to fail fast if migration wasn't applied.
    """
    inspector = inspect(session.bind)
    all_tables = inspector.get_table_names()
    
    required_tables = [
        'campaign_ops_campaigns',
        'campaign_ops_plans',
        'campaign_ops_calendar_items',
        'campaign_ops_operator_tasks',
        'campaign_ops_metric_entries',
        'campaign_ops_audit_log',
    ]
    
    missing = [t for t in required_tables if t not in all_tables]
    
    if missing:
        from aicmo.core.db_diagnostics import format_db_identity
        raise RuntimeError(
            f"Campaign Ops tables missing from database.\n"
            f"Missing tables: {', '.join(missing)}\n"
            f"Database: {format_db_identity()}\n"
            f"Fix: Run 'bash scripts/apply_campaign_ops_migrations.sh'\n"
            f"Or: cd /workspaces/AICMO && alembic upgrade head"
        )

# Guard to ensure tables are checked on first repo access
_tables_verified = False

def _ensure_tables_verified(session: Session) -> None:
    """Ensure tables exist before any repo operation."""
    global _tables_verified
    if not _tables_verified:
        _verify_tables_exist(session)
        _tables_verified = True
# CAMPAIGN_OPS_FIX_END


# ============================================================================
# Campaign CRUD
# ============================================================================

def create_campaign(session: Session, **kwargs) -> Campaign:
    """Create a new campaign."""
    # CAMPAIGN_OPS_FIX_START
    _ensure_tables_verified(session)
    # CAMPAIGN_OPS_FIX_END
    campaign = Campaign(**kwargs)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def get_campaign(session: Session, campaign_id: int) -> Optional[Campaign]:
    """Get campaign by ID."""
    return session.query(Campaign).filter(Campaign.id == campaign_id).first()


def get_campaign_by_name(session: Session, name: str) -> Optional[Campaign]:
    """Get campaign by name."""
    return session.query(Campaign).filter(Campaign.name == name).first()


def list_campaigns(session: Session, status: Optional[str] = None) -> List[Campaign]:
    """List campaigns, optionally filtered by status."""
    query = session.query(Campaign)
    if status:
        query = query.filter(Campaign.status == status)
    return query.order_by(desc(Campaign.created_at)).all()


def update_campaign(session: Session, campaign_id: int, **kwargs) -> Optional[Campaign]:
    """Update campaign fields."""
    campaign = get_campaign(session, campaign_id)
    if not campaign:
        return None
    
    for key, value in kwargs.items():
        if value is not None:
            setattr(campaign, key, value)
    
    campaign.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(campaign)
    return campaign


def delete_campaign(session: Session, campaign_id: int) -> bool:
    """Delete campaign (cascades to related records)."""
    campaign = get_campaign(session, campaign_id)
    if not campaign:
        return False
    
    session.delete(campaign)
    session.commit()
    return True


# ============================================================================
# Campaign Plan CRUD
# ============================================================================

def create_plan(session: Session, campaign_id: int, **kwargs) -> CampaignPlan:
    """Create a campaign plan."""
    plan = CampaignPlan(campaign_id=campaign_id, **kwargs)
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def get_latest_plan(session: Session, campaign_id: int) -> Optional[CampaignPlan]:
    """Get latest plan for a campaign."""
    return (
        session.query(CampaignPlan)
        .filter(CampaignPlan.campaign_id == campaign_id)
        .order_by(desc(CampaignPlan.version))
        .first()
    )


def list_plans(session: Session, campaign_id: int) -> List[CampaignPlan]:
    """List all plans for a campaign."""
    return (
        session.query(CampaignPlan)
        .filter(CampaignPlan.campaign_id == campaign_id)
        .order_by(desc(CampaignPlan.version))
        .all()
    )


# ============================================================================
# Calendar Item CRUD
# ============================================================================

def create_calendar_item(session: Session, campaign_id: int, **kwargs) -> CalendarItem:
    """Create a calendar item."""
    item = CalendarItem(campaign_id=campaign_id, **kwargs)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def get_calendar_item(session: Session, item_id: int) -> Optional[CalendarItem]:
    """Get calendar item by ID."""
    return session.query(CalendarItem).filter(CalendarItem.id == item_id).first()


def list_calendar_items(
    session: Session,
    campaign_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[CalendarItem]:
    """List calendar items for a campaign, optionally filtered by date range."""
    query = session.query(CalendarItem).filter(CalendarItem.campaign_id == campaign_id)
    
    if start_date:
        query = query.filter(CalendarItem.scheduled_at >= start_date)
    if end_date:
        query = query.filter(CalendarItem.scheduled_at <= end_date)
    
    return query.order_by(CalendarItem.scheduled_at).all()


def update_calendar_item(session: Session, item_id: int, **kwargs) -> Optional[CalendarItem]:
    """Update a calendar item."""
    item = get_calendar_item(session, item_id)
    if not item:
        return None
    
    for key, value in kwargs.items():
        if value is not None:
            setattr(item, key, value)
    
    item.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(item)
    return item


# ============================================================================
# Operator Task CRUD
# ============================================================================

def create_operator_task(session: Session, campaign_id: int, **kwargs) -> OperatorTask:
    """Create an operator task."""
    task = OperatorTask(campaign_id=campaign_id, **kwargs)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_operator_task(session: Session, task_id: int) -> Optional[OperatorTask]:
    """Get operator task by ID."""
    return session.query(OperatorTask).filter(OperatorTask.id == task_id).first()


def list_operator_tasks(
    session: Session,
    campaign_id: int,
    status: Optional[str] = None,
) -> List[OperatorTask]:
    """List operator tasks for a campaign, optionally filtered by status."""
    query = session.query(OperatorTask).filter(OperatorTask.campaign_id == campaign_id)
    
    if status:
        query = query.filter(OperatorTask.status == status)
    
    return query.order_by(OperatorTask.due_at).all()


def list_tasks_by_status_and_date(
    session: Session,
    campaign_id: int,
    status: str,
    before_date: Optional[datetime] = None,
) -> List[OperatorTask]:
    """List tasks with specific status, optionally before a date."""
    query = session.query(OperatorTask).filter(
        and_(
            OperatorTask.campaign_id == campaign_id,
            OperatorTask.status == status,
        )
    )
    
    if before_date:
        query = query.filter(OperatorTask.due_at <= before_date)
    
    return query.order_by(OperatorTask.due_at).all()


def update_operator_task(session: Session, task_id: int, **kwargs) -> Optional[OperatorTask]:
    """Update an operator task."""
    task = get_operator_task(session, task_id)
    if not task:
        return None
    
    for key, value in kwargs.items():
        if value is not None:
            setattr(task, key, value)
    
    task.updated_at = datetime.utcnow()
    
    # Auto-set completed_at if marking as DONE
    if kwargs.get("status") == TaskStatus.DONE.value and not task.completed_at:
        task.completed_at = datetime.utcnow()
    
    session.commit()
    session.refresh(task)
    return task


def mark_task_done(
    session: Session,
    task_id: int,
    proof_type: str,
    proof_value: str,
) -> Optional[OperatorTask]:
    """Mark a task as DONE with completion proof."""
    return update_operator_task(
        session,
        task_id,
        status=TaskStatus.DONE.value,
        completion_proof_type=proof_type,
        completion_proof_value=proof_value,
        completed_at=datetime.utcnow(),
    )


# ============================================================================
# Metric Entry CRUD
# ============================================================================

def create_metric_entry(session: Session, campaign_id: int, **kwargs) -> MetricEntry:
    """Create a metric entry."""
    entry = MetricEntry(campaign_id=campaign_id, **kwargs)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def list_metric_entries(
    session: Session,
    campaign_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[MetricEntry]:
    """List metric entries for a campaign."""
    query = session.query(MetricEntry).filter(MetricEntry.campaign_id == campaign_id)
    
    if start_date:
        query = query.filter(MetricEntry.date >= start_date)
    if end_date:
        query = query.filter(MetricEntry.date <= end_date)
    
    return query.order_by(MetricEntry.date).all()


# ============================================================================
# Audit Log CRUD
# ============================================================================

def create_audit_log(
    session: Session,
    actor: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    before_json: Optional[dict] = None,
    after_json: Optional[dict] = None,
    notes: Optional[str] = None,
) -> OperatorAuditLog:
    """Create an audit log entry."""
    log = OperatorAuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before_json,
        after_json=after_json,
        notes=notes,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def list_audit_logs(
    session: Session,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    limit: int = 100,
) -> List[OperatorAuditLog]:
    """List audit logs."""
    query = session.query(OperatorAuditLog)
    
    if entity_type:
        query = query.filter(OperatorAuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(OperatorAuditLog.entity_id == entity_id)
    
    return query.order_by(desc(OperatorAuditLog.created_at)).limit(limit).all()
