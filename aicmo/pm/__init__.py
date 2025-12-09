"""Project and resource management module.

Stage PM: Project & Resource Management
"""

from aicmo.pm.domain import (
    TaskStatus,
    TaskPriority,
    ResourceType,
    Task,
    Resource,
    ResourceAllocation,
    CapacityPlan,
    ProjectTimeline,
    ProjectBudget,
    TeamWorkload,
    ProjectRisk,
    ProjectDashboard,
)

from aicmo.pm.service import (
    create_project_task,
    allocate_resource_to_project,
    generate_capacity_plan,
    generate_project_timeline,
    generate_project_dashboard,
    update_task_status,
    assign_task,
)

__all__ = [
    # Enums
    "TaskStatus",
    "TaskPriority",
    "ResourceType",
    
    # Domain models
    "Task",
    "Resource",
    "ResourceAllocation",
    "CapacityPlan",
    "ProjectTimeline",
    "ProjectBudget",
    "TeamWorkload",
    "ProjectRisk",
    "ProjectDashboard",
    
    # Service functions
    "create_project_task",
    "allocate_resource_to_project",
    "generate_capacity_plan",
    "generate_project_timeline",
    "generate_project_dashboard",
    "update_task_status",
    "assign_task",
]
