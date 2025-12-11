"""
Phase 10 — Agency Auto-Brain (AAB)

Automatically detects what work needs to be done and proposes solutions.

The Agency Auto-Brain is a meta-generator that:
1. Scans a brief to detect implicit "tasks" (SWOT needed? Personas needed? etc.)
2. Looks at what's already been generated
3. Proposes the next step(s) to complete the brief
4. Can auto-execute those tasks or present them for approval

Use Cases:
- "I just uploaded a brief" → AAB detects: "You need SWOT, personas, messaging"
- "I've generated SWOT" → AAB detects: "Next: generate personas, then messaging"
- "I'm done with strategy" → AAB proposes: "Now do social calendar, creative directions"
- "I only have 10 minutes" → AAB prioritizes: "Quick win: Generate social calendar"

Task Hierarchy:
1. Core Discovery: SWOT, Personas (foundation)
2. Strategy Development: Messaging, Positioning (strategy)
3. Creative Execution: Creative Directions, Variants (creative)
4. Tactical Execution: Social Calendar, Video Briefs (tactics)
5. Measurement: KPIs, Success Metrics (measurement)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Priority levels for auto-brain tasks."""
    CRITICAL = 1  # Blocks other work
    HIGH = 2  # Should do soon
    MEDIUM = 3  # Normal priority
    LOW = 4  # Nice to have
    OPTIONAL = 5  # Only if time permits


class TaskType(Enum):
    """Types of tasks the Auto-Brain can detect."""
    # Core Discovery (foundation)
    SWOT_ANALYSIS = "swot_analysis"
    PERSONA_GENERATION = "persona_generation"
    AUDIENCE_RESEARCH = "audience_research"
    
    # Strategy Development
    MESSAGING_PILLARS = "messaging_pillars"
    BRAND_POSITIONING = "brand_positioning"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    
    # Creative Execution
    CREATIVE_DIRECTIONS = "creative_directions"
    CREATIVE_VARIANTS = "creative_variants"
    BRAND_GUIDELINES = "brand_guidelines"
    
    # Tactical Execution
    SOCIAL_CALENDAR = "social_calendar"
    VIDEO_BRIEFS = "video_briefs"
    EMAIL_CAMPAIGNS = "email_campaigns"
    
    # Measurement
    KPI_DEFINITION = "kpi_definition"
    SUCCESS_METRICS = "success_metrics"
    ANALYTICS_SETUP = "analytics_setup"


class TaskStatus(Enum):
    """Status of a task."""
    PROPOSED = "proposed"  # AAB detected it, not yet started
    IN_PROGRESS = "in_progress"  # User started it
    COMPLETED = "completed"  # Done
    SKIPPED = "skipped"  # User chose not to do it
    BLOCKED = "blocked"  # Can't do it yet (dependency not met)


@dataclass
class TaskDependency:
    """A task that must be completed before another task."""
    task_type: TaskType
    reason: str  # Why is this a dependency? (e.g., "Need personas to create messaging")


@dataclass
class AutoBrainTask:
    """
    A task detected by the Agency Auto-Brain.
    
    Tasks are discovered based on:
    - Brief content and goals
    - What's already been generated
    - Industry best practices
    - Time constraints
    """
    
    task_id: str  # UUID
    task_type: TaskType
    title: str  # Human-readable title
    description: str  # What should be done?
    
    # Priority and status
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PROPOSED
    
    # Dependencies
    dependencies: List[TaskDependency] = field(default_factory=list)
    blocking_tasks: List[str] = field(default_factory=list)  # task_ids that depend on this
    
    # Effort and time
    estimated_minutes: int = 5  # How long to complete?
    min_estimated_minutes: int = 5
    max_estimated_minutes: int = 30
    
    # Why was this task detected?
    detection_reason: str = ""  # "Brief mentions 'personality', so personas needed"
    confidence: float = 0.8  # How confident are we this task is needed? (0.0-1.0)
    
    # Which generator(s) would handle this?
    related_generators: List[str] = field(default_factory=list)  # ["persona_generator", ...]
    
    # Additional context
    context: Dict[str, Any] = field(default_factory=dict)  # Any additional info
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.name,
            "status": self.status.name,
            "dependencies": [asdict(d) for d in self.dependencies],
            "blocking_tasks": self.blocking_tasks,
            "estimated_minutes": self.estimated_minutes,
            "min_estimated_minutes": self.min_estimated_minutes,
            "max_estimated_minutes": self.max_estimated_minutes,
            "detection_reason": self.detection_reason,
            "confidence": self.confidence,
            "related_generators": self.related_generators,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "skipped_at": self.skipped_at.isoformat() if self.skipped_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoBrainTask":
        data = data.copy()
        data["task_type"] = TaskType(data["task_type"])
        data["priority"] = TaskPriority[data["priority"]]
        data["status"] = TaskStatus[data["status"]]
        data["dependencies"] = [
            TaskDependency(
                task_type=TaskType(d["task_type"]),
                reason=d["reason"]
            )
            for d in data.get("dependencies", [])
        ]
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        if data.get("skipped_at"):
            data["skipped_at"] = datetime.fromisoformat(data["skipped_at"])
        return cls(**data)


@dataclass
class AutoBrainPlan:
    """
    A complete plan generated by the Agency Auto-Brain.
    
    Contains all detected tasks, ordered by priority and dependencies.
    """
    
    plan_id: str  # UUID
    brand_id: str
    brief_id: Optional[str]
    
    # All detected tasks
    tasks: List[AutoBrainTask] = field(default_factory=list)
    
    # Plan metadata
    total_estimated_minutes: int = 0
    phase_count: int = 0  # How many "phases" of work?
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Plan status
    is_approved: bool = False
    approved_at: Optional[datetime] = None
    
    # Statistics
    critical_count: int = 0
    high_count: int = 0
    completed_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "brand_id": self.brand_id,
            "brief_id": self.brief_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "total_estimated_minutes": self.total_estimated_minutes,
            "phase_count": self.phase_count,
            "created_at": self.created_at.isoformat(),
            "is_approved": self.is_approved,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "completed_count": self.completed_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoBrainPlan":
        data = data.copy()
        data["tasks"] = [AutoBrainTask.from_dict(t) for t in data.get("tasks", [])]
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("approved_at"):
            data["approved_at"] = datetime.fromisoformat(data["approved_at"])
        return cls(**data)
    
    def get_next_task(self) -> Optional[AutoBrainTask]:
        """Get the next highest-priority task that's not blocked."""
        # Sort by priority, then by whether dependencies are met
        available = [
            t for t in self.tasks
            if t.status == TaskStatus.PROPOSED and not self._is_blocked(t)
        ]
        
        if not available:
            return None
        
        # Sort by priority (lower number = higher priority)
        return sorted(available, key=lambda t: t.priority.value)[0]
    
    def _is_blocked(self, task: AutoBrainTask) -> bool:
        """Check if a task is blocked by unmet dependencies."""
        for dep in task.dependencies:
            # Find the dependency task
            dep_task = next(
                (t for t in self.tasks if t.task_type == dep.task_type),
                None
            )
            if dep_task is None or dep_task.status != TaskStatus.COMPLETED:
                return True
        return False
    
    def get_tasks_by_phase(self) -> List[List[AutoBrainTask]]:
        """
        Organize tasks into phases.
        Phase 1: Tasks with no dependencies
        Phase 2: Tasks that depend on Phase 1, etc.
        """
        phases = []
        remaining_ids = {t.task_id for t in self.tasks}
        remaining = {t.task_id: t for t in self.tasks}
        
        while remaining_ids:
            phase_ids = [tid for tid in remaining_ids if not remaining[tid].dependencies]
            if not phase_ids:
                # Circular dependency or all remaining are blocked
                break
            
            phase = [remaining[tid] for tid in phase_ids]
            phases.append(sorted(phase, key=lambda t: t.priority.value))
            remaining_ids -= set(phase_ids)
        
        if remaining_ids:
            # Put any remaining tasks in a final phase
            phase = [remaining[tid] for tid in remaining_ids]
            phases.append(sorted(phase, key=lambda t: t.priority.value))
        
        return phases
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the plan."""
        lines = [
            f"Agency Auto-Brain Plan: {len(self.tasks)} tasks",
            f"Total estimated time: {self.total_estimated_minutes} minutes",
            f"Critical: {self.critical_count}, High: {self.high_count}",
            "",
        ]
        
        for i, phase in enumerate(self.get_tasks_by_phase(), 1):
            lines.append(f"Phase {i}:")
            for task in phase:
                lines.append(f"  [{task.priority.name}] {task.title} ({task.estimated_minutes}m)")
        
        return "\n".join(lines)
