"""Project and resource management service.

Stage PM: Project & Resource Management
Service layer for task management, resource allocation, and capacity planning.
"""

import logging
from typing import List, Optional
from datetime import datetime, date, timedelta
import uuid

from aicmo.domain.intake import ClientIntake
from aicmo.pm.domain import (
    Task,
    Resource,
    ResourceAllocation,
    CapacityPlan,
    ProjectTimeline,
    ProjectBudget,
    TeamWorkload,
    ProjectDashboard,
    TaskStatus,
    TaskPriority,
    ResourceType,
)
from aicmo.memory.engine import log_event
from aicmo.learning.event_types import EventType

logger = logging.getLogger(__name__)


def create_project_task(
    intake: ClientIntake,
    project_id: str,
    title: str,
    description: str,
    assigned_to: Optional[str] = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    due_days: int = 7,
    estimated_hours: Optional[float] = None
) -> Task:
    """
    Create a new project task.
    
    Stage PM: Skeleton for task creation.
    Future: Integrate with PM system APIs.
    
    Args:
        intake: Client intake data
        project_id: Project ID
        title: Task title
        description: Task description
        assigned_to: User to assign task to
        priority: Task priority
        due_days: Days until due
        estimated_hours: Estimated hours to complete
        
    Returns:
        Task record
    """
    logger.info(f"Creating task '{title}' for project {project_id}")
    
    task = Task(
        task_id=str(uuid.uuid4()),
        brand_name=intake.brand_name,
        project_id=project_id,
        title=title,
        description=description,
        status=TaskStatus.NOT_STARTED,
        priority=priority,
        assigned_to=assigned_to,
        created_at=datetime.now(),
        due_date=date.today() + timedelta(days=due_days),
        estimated_hours=estimated_hours
    )
    
    # Validate task before returning (G1: contracts layer)
    from aicmo.core.contracts import validate_pm_task
    task = validate_pm_task(task)
    
    # Learning: Log task creation
    log_event(
        EventType.PM_TASK_SCHEDULED.value,
        project_id=project_id,
        details={
            "brand_name": intake.brand_name,
            "project_id": project_id,
            "task_title": title,
            "priority": priority.value,
            "assigned_to": assigned_to or "unassigned"
        },
        tags=["pm", "task", "creation"]
    )
    
    logger.info(f"Task created: {task.task_id}")
    return task


def allocate_resource_to_project(
    intake: ClientIntake,
    project_id: str,
    resource_id: str,
    resource_name: str,
    start_date: date,
    end_date: date,
    allocated_hours: float
) -> ResourceAllocation:
    """
    Allocate a resource to a project.
    
    Stage PM: Skeleton for resource allocation.
    Future: Integrate with resource management systems.
    
    Args:
        intake: Client intake data
        project_id: Project ID
        resource_id: Resource ID
        resource_name: Resource name
        start_date: Allocation start date
        end_date: Allocation end date
        allocated_hours: Hours allocated
        
    Returns:
        ResourceAllocation record
    """
    logger.info(f"Allocating {resource_name} to project {project_id}")
    
    allocation = ResourceAllocation(
        allocation_id=str(uuid.uuid4()),
        brand_name=intake.brand_name,
        project_id=project_id,
        resource_id=resource_id,
        resource_name=resource_name,
        start_date=start_date,
        end_date=end_date,
        allocated_hours=allocated_hours,
        is_active=True,
        created_at=datetime.now()
    )
    
    # Learning: Log resource allocation
    log_event(
        EventType.PM_RESOURCE_ALLOCATED.value,
        project_id=project_id,
        details={
            "brand_name": intake.brand_name,
            "project_id": project_id,
            "resource_name": resource_name,
            "allocated_hours": allocated_hours
        },
        tags=["pm", "resource", "allocation"]
    )
    
    logger.info(f"Resource allocated: {allocation.allocation_id}")
    return allocation


def generate_capacity_plan(
    start_date: date,
    end_date: date,
    resources: Optional[List[Resource]] = None
) -> CapacityPlan:
    """
    Generate capacity plan for team.
    
    Stage PM: Skeleton with placeholder metrics.
    Future: Query actual resource data from PM systems.
    
    Args:
        start_date: Planning period start
        end_date: Planning period end
        resources: List of resources (optional, uses placeholder if None)
        
    Returns:
        CapacityPlan with metrics
    """
    logger.info(f"Generating capacity plan from {start_date} to {end_date}")
    
    # Stage PM: Generate placeholder capacity metrics
    weeks = (end_date - start_date).days / 7
    total_available = 40.0 * weeks * 10  # 10 people, 40 hrs/week
    total_allocated = total_available * 0.75  # 75% utilization
    
    plan = CapacityPlan(
        plan_id=str(uuid.uuid4()),
        start_date=start_date,
        end_date=end_date,
        total_available_hours=total_available,
        total_allocated_hours=total_allocated,
        total_utilization_percent=75.0,
        capacity_by_type=_generate_capacity_by_type(),
        over_allocated_resources=[],
        under_utilized_resources=["res-3", "res-7"],
        hiring_needs=["designer", "copywriter"],
        generated_at=datetime.now()
    )
    
    # Learning: Log capacity planning
    log_event(
        EventType.PM_CAPACITY_ALERT.value,
        project_id="capacity_planning",
        details={
            "weeks": weeks,
            "utilization_percent": plan.total_utilization_percent,
            "hiring_needs": len(plan.hiring_needs)
        },
        tags=["pm", "capacity", "planning"]
    )
    
    logger.info(f"Capacity plan generated: {plan.total_utilization_percent:.1f}% utilization")
    return plan


def generate_project_timeline(
    intake: ClientIntake,
    project_id: str,
    project_name: str,
    target_end_date: date,
    tasks: Optional[List[Task]] = None
) -> ProjectTimeline:
    """
    Generate project timeline.
    
    Stage PM: Skeleton with placeholder timeline.
    Future: Calculate from actual task dependencies.
    
    Args:
        intake: Client intake data
        project_id: Project ID
        project_name: Project name
        target_end_date: Target completion date
        tasks: Project tasks (optional)
        
    Returns:
        ProjectTimeline with schedule
    """
    logger.info(f"Generating timeline for {project_name}")
    
    # Stage PM: Generate placeholder timeline
    total_tasks = len(tasks) if tasks else 20
    completed_tasks = int(total_tasks * 0.6) if tasks else 12
    
    timeline = ProjectTimeline(
        timeline_id=str(uuid.uuid4()),
        brand_name=intake.brand_name,
        project_id=project_id,
        project_name=project_name,
        start_date=date.today(),
        target_end_date=target_end_date,
        milestones=_generate_milestones(target_end_date),
        critical_path_tasks=["task-1", "task-5", "task-12"],
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        progress_percent=float(completed_tasks) / total_tasks * 100 if total_tasks > 0 else 0,
        is_on_track=True,
        days_ahead_behind=2,
        at_risk_tasks=["task-8"],
        generated_at=datetime.now()
    )
    
    # Learning: Log timeline generation
    log_event(
        EventType.PM_MILESTONE_REACHED.value,
        project_id=project_id,
        details={
            "brand_name": intake.brand_name,
            "project_name": project_name,
            "progress_percent": timeline.progress_percent,
            "is_on_track": timeline.is_on_track
        },
        tags=["pm", "timeline", "schedule"]
    )
    
    logger.info(f"Timeline generated: {timeline.progress_percent:.1f}% complete")
    return timeline


def generate_project_dashboard(
    brand_name: Optional[str] = None
) -> ProjectDashboard:
    """
    Generate project management dashboard.
    
    Stage PM: Skeleton with placeholder metrics.
    Future: Aggregate from PM system data.
    
    Args:
        brand_name: Optional brand filter
        
    Returns:
        ProjectDashboard with overview metrics
    """
    logger.info(f"Generating PM dashboard for {brand_name or 'all brands'}")
    
    # Stage PM: Generate placeholder dashboard metrics
    dashboard = ProjectDashboard(
        dashboard_id=str(uuid.uuid4()),
        brand_name=brand_name or "All Brands",
        active_projects=8,
        total_projects=15,
        total_tasks=120,
        completed_tasks=85,
        overdue_tasks=5,
        total_resources=12,
        available_resources=10,
        average_utilization=72.5,
        total_budget=500000.0,
        total_spent=325000.0,
        budget_variance_percent=-2.5,
        projects_on_track=6,
        projects_at_risk=2,
        projects_delayed=0,
        generated_at=datetime.now()
    )
    
    # Learning: Log dashboard generation
    log_event(
        EventType.PM_CAPACITY_ALERT.value,
        project_id="dashboard",
        details={
            "brand_name": dashboard.brand_name,
            "active_projects": dashboard.active_projects,
            "average_utilization": dashboard.average_utilization,
            "projects_at_risk": dashboard.projects_at_risk
        },
        tags=["pm", "dashboard", "overview"]
    )
    
    logger.info(f"Dashboard generated: {dashboard.active_projects} active projects")
    return dashboard


# ═══════════════════════════════════════════════════════════════════════
# Helper Functions (Stage PM: Placeholder implementations)
# ═══════════════════════════════════════════════════════════════════════


def _generate_capacity_by_type() -> dict:
    """Generate placeholder capacity by resource type."""
    return {
        "designer": {
            "available": 160.0,
            "allocated": 140.0,
            "utilization": 87.5
        },
        "copywriter": {
            "available": 120.0,
            "allocated": 85.0,
            "utilization": 70.8
        },
        "strategist": {
            "available": 80.0,
            "allocated": 70.0,
            "utilization": 87.5
        }
    }


def _generate_milestones(end_date: date) -> List[dict]:
    """Generate placeholder milestones."""
    start = date.today()
    duration = (end_date - start).days
    
    return [
        {
            "name": "Project Kickoff",
            "date": str(start),
            "status": "completed"
        },
        {
            "name": "Strategy Complete",
            "date": str(start + timedelta(days=duration // 4)),
            "status": "completed"
        },
        {
            "name": "Creative Review",
            "date": str(start + timedelta(days=duration // 2)),
            "status": "in_progress"
        },
        {
            "name": "Final Delivery",
            "date": str(end_date),
            "status": "pending"
        }
    ]


def update_task_status(
    task: Task,
    new_status: TaskStatus,
    actual_hours: Optional[float] = None
) -> Task:
    """
    Update task status.
    
    Stage PM: Helper to update task.
    """
    logger.info(f"Updating task {task.task_id} status to {new_status.value}")
    
    task.status = new_status
    
    if new_status == TaskStatus.IN_PROGRESS and not task.started_at:
        task.started_at = datetime.now()
    
    if new_status == TaskStatus.COMPLETED:
        task.completed_at = datetime.now()
        task.progress_percent = 100
        if actual_hours:
            task.actual_hours = actual_hours
    
    return task


def assign_task(
    task: Task,
    assigned_to: str,
    assigned_by: str
) -> Task:
    """
    Assign task to a resource.
    
    Stage PM: Helper to assign tasks.
    """
    logger.info(f"Assigning task {task.task_id} to {assigned_to}")
    
    task.assigned_to = assigned_to
    task.assigned_by = assigned_by
    
    return task
