"""Project and resource management domain models.

Stage PM: Project & Resource Management
Skeleton implementation for task management, resource allocation, and capacity planning.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from aicmo.domain.base import AicmoBaseModel


class TaskStatus(str, Enum):
    """Task status values."""
    
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ResourceType(str, Enum):
    """Resource types."""
    
    DESIGNER = "designer"
    COPYWRITER = "copywriter"
    STRATEGIST = "strategist"
    ACCOUNT_MANAGER = "account_manager"
    DEVELOPER = "developer"
    VIDEO_EDITOR = "video_editor"
    PROJECT_MANAGER = "project_manager"


class Task(AicmoBaseModel):
    """
    A project task.
    
    Stage PM: Skeleton for task management.
    """
    
    task_id: str
    brand_name: str
    project_id: str
    
    # Task details
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # Assignment
    assigned_to: Optional[str] = None  # User ID or email
    assigned_by: Optional[str] = None
    
    # Timing
    created_at: datetime
    due_date: Optional[date] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Estimation
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    
    # Dependencies
    depends_on: List[str] = []  # Task IDs
    blocks: List[str] = []  # Task IDs this blocks
    
    # Progress
    progress_percent: int = 0
    
    # Metadata
    tags: List[str] = []


class Resource(AicmoBaseModel):
    """
    A team resource/person.
    
    Stage PM: Skeleton for resource tracking.
    """
    
    resource_id: str
    
    # Resource details
    name: str
    email: str
    resource_type: ResourceType
    role: str
    
    # Availability
    is_available: bool = True
    capacity_hours_per_week: float = 40.0
    
    # Skills
    skills: List[str] = []
    seniority_level: Optional[str] = None  # junior, mid, senior, lead
    
    # Cost
    hourly_rate: Optional[float] = None
    
    # Active assignments
    current_projects: List[str] = []
    current_utilization_percent: float = 0.0


class ResourceAllocation(AicmoBaseModel):
    """
    Allocation of a resource to a project/task.
    
    Stage PM: Skeleton for resource allocation.
    """
    
    allocation_id: str
    brand_name: str
    project_id: str
    
    # Resource
    resource_id: str
    resource_name: str
    
    # Allocation details
    start_date: date
    end_date: date
    allocated_hours: float
    
    # Specific tasks
    task_ids: List[str] = []
    
    # Status
    is_active: bool = True
    created_at: datetime


class CapacityPlan(AicmoBaseModel):
    """
    Capacity planning analysis.
    
    Stage PM: Skeleton for capacity management.
    """
    
    plan_id: str
    
    # Time range
    start_date: date
    end_date: date
    
    # Overall capacity
    total_available_hours: float
    total_allocated_hours: float
    total_utilization_percent: float
    
    # By resource type
    capacity_by_type: Dict[str, Dict[str, float]] = {}  # ResourceType -> {available, allocated, utilization}
    
    # Constraints
    over_allocated_resources: List[str] = []  # Resource IDs
    under_utilized_resources: List[str] = []
    
    # Recommendations
    hiring_needs: List[str] = []  # Resource types needed
    
    # Generated
    generated_at: datetime


class ProjectTimeline(AicmoBaseModel):
    """
    Project timeline and schedule.
    
    Stage PM: Skeleton for timeline management.
    """
    
    timeline_id: str
    brand_name: str
    project_id: str
    project_name: str
    
    # Overall timeline
    start_date: date
    target_end_date: date
    actual_end_date: Optional[date] = None
    
    # Milestones
    milestones: List[Dict[str, Any]] = []  # name, date, status
    
    # Critical path
    critical_path_tasks: List[str] = []  # Task IDs
    
    # Progress
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percent: float = 0.0
    
    # Status
    is_on_track: bool = True
    days_ahead_behind: int = 0
    
    # Risks
    at_risk_tasks: List[str] = []
    
    # Generated
    generated_at: datetime


class ProjectBudget(AicmoBaseModel):
    """
    Project budget tracking.
    
    Stage PM: Skeleton for budget management.
    """
    
    budget_id: str
    brand_name: str
    project_id: str
    
    # Budget
    total_budget: float
    allocated_budget: float
    spent_budget: float
    remaining_budget: float
    
    # Breakdown
    budget_by_category: Dict[str, float] = {}  # Category -> amount
    spent_by_category: Dict[str, float] = {}
    
    # Labor costs
    labor_budget: float = 0.0
    labor_spent: float = 0.0
    
    # Status
    is_over_budget: bool = False
    budget_utilization_percent: float = 0.0
    
    # Forecast
    projected_total_cost: float = 0.0
    projected_variance: float = 0.0
    
    # Updated
    last_updated: datetime


class TeamWorkload(AicmoBaseModel):
    """
    Team workload analysis.
    
    Stage PM: Skeleton for workload balancing.
    """
    
    analysis_id: str
    
    # Time range
    start_date: date
    end_date: date
    
    # Team metrics
    total_team_capacity_hours: float
    total_allocated_hours: float
    average_utilization_percent: float
    
    # By resource
    resource_workloads: List[Dict[str, Any]] = []  # resource details + workload
    
    # Imbalances
    overloaded_resources: List[str] = []
    underutilized_resources: List[str] = []
    
    # Recommendations
    rebalancing_suggestions: List[str] = []
    
    # Generated
    generated_at: datetime


class ProjectRisk(AicmoBaseModel):
    """
    Project risk tracking.
    
    Stage PM: Skeleton for risk management.
    """
    
    risk_id: str
    brand_name: str
    project_id: str
    
    # Risk details
    risk_title: str
    risk_description: str
    risk_category: str  # schedule, budget, resource, scope, quality
    
    # Assessment
    probability: str  # low, medium, high
    impact: str  # low, medium, high
    risk_score: float  # calculated from probability x impact
    
    # Mitigation
    mitigation_plan: Optional[str] = None
    contingency_plan: Optional[str] = None
    
    # Status
    is_active: bool = True
    identified_at: datetime
    resolved_at: Optional[datetime] = None
    
    # Owner
    risk_owner: Optional[str] = None


class ProjectDashboard(AicmoBaseModel):
    """
    Project management dashboard.
    
    Stage PM: Skeleton for project overview.
    """
    
    dashboard_id: str
    brand_name: str
    
    # Projects
    active_projects: int = 0
    total_projects: int = 0
    
    # Tasks
    total_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    
    # Resources
    total_resources: int = 0
    available_resources: int = 0
    average_utilization: float = 0.0
    
    # Budget
    total_budget: float = 0.0
    total_spent: float = 0.0
    budget_variance_percent: float = 0.0
    
    # Health indicators
    projects_on_track: int = 0
    projects_at_risk: int = 0
    projects_delayed: int = 0
    
    # Generated
    generated_at: datetime
