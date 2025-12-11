"""
Phase 14 — Operator Dashboard Models

Read-only domain models for the operator dashboard.

These dataclasses represent the current state of:
- Brand (LBB, analytics, risk signals)
- Task queue (pending, approved, executing, completed)
- Execution schedule (upcoming, overdue)
- Feedback loop (anomalies, suggestions)
- Automation settings (mode, dry_run flag)

All models are immutable snapshots for display purposes.
No heavy logic; pure data carriers for the UI.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class BrandStatusView:
    """
    Current state of a brand.
    
    Includes:
    - Brand identity (name, persona, tone)
    - Performance indicators (top channels, risk flags)
    - Last updated timestamp
    """
    
    brand_id: str
    """Brand UUID."""
    
    brand_name: Optional[str] = None
    """Display name from LBB."""
    
    key_persona: Optional[str] = None
    """Primary persona from LBB."""
    
    primary_tone: Optional[str] = None
    """Tone of voice from LBB."""
    
    top_channels: List[str] = field(default_factory=list)
    """
    Ranked channels by performance (from analytics + LBB).
    Example: ['LinkedIn', 'Email', 'Twitter']
    """
    
    risk_flags: List[str] = field(default_factory=list)
    """
    Detected issues or gaps.
    Example: ['email_underperforming', 'no_recent_campaigns', 'low_engagement']
    """
    
    last_updated_at: Optional[datetime] = None
    """When was brand state last refreshed?"""


@dataclass
class TaskQueueView:
    """
    Current task queue state for a brand.
    
    Summarizes:
    - Task counts by status
    - Recent task list (minimal info)
    """
    
    brand_id: str
    """Brand UUID."""
    
    pending: int = 0
    """Tasks in 'proposed' or 'pending_review' status."""
    
    approved: int = 0
    """Tasks approved for execution."""
    
    running: int = 0
    """Currently executing tasks."""
    
    completed: int = 0
    """Successfully completed tasks."""
    
    failed: int = 0
    """Failed task executions."""
    
    recent_tasks: List[Dict[str, Any]] = field(default_factory=list)
    """
    Last N tasks (default: 10).
    Each dict contains:
    - id: task_id
    - type: task_type
    - status: current status
    - reason: brief description
    - created_at: timestamp
    """


@dataclass
class ScheduleView:
    """
    Upcoming scheduled executions for a brand.
    
    Tracks:
    - Next N scheduled tasks
    - Overdue tasks
    - Next scheduler tick time
    """
    
    brand_id: str
    """Brand UUID."""
    
    upcoming: List[Dict[str, Any]] = field(default_factory=list)
    """
    Next scheduled tasks (default: next 10).
    Each dict contains:
    - scheduled_id: UUID
    - task_id: UUID
    - task_type: string
    - run_at: datetime
    - status: "scheduled", "in_progress", etc.
    """
    
    overdue: List[Dict[str, Any]] = field(default_factory=list)
    """
    Tasks that were scheduled but didn't execute yet.
    Same structure as upcoming.
    """
    
    next_tick_at: Optional[datetime] = None
    """When will scheduler next check for due tasks?"""


@dataclass
class FeedbackView:
    """
    Latest feedback loop state for a brand.
    
    Captures:
    - Last performance snapshot time
    - Detected anomalies
    - Summary of last run
    """
    
    brand_id: str
    """Brand UUID."""
    
    last_snapshot_at: Optional[datetime] = None
    """When was the last performance snapshot captured?"""
    
    last_anomalies: List[str] = field(default_factory=list)
    """
    Detected anomalies from last run.
    Example: ['email_open_rate_dropped', 'social_engagement_falling']
    """
    
    last_run_summary: Optional[Dict[str, Any]] = None
    """
    Summary from last feedback cycle run.
    Example:
    {
        "task_count": 3,
        "anomalies_detected": 2,
        "notes": "Email performance concerning, proposed retry",
    }
    """


@dataclass
class AutomationModeView:
    """
    Current automation settings for a brand.
    
    Controls:
    - Execution mode (manual, review_first, full_auto)
    - dry_run flag
    - Notes/reason for current settings
    """
    
    brand_id: str
    """Brand UUID."""
    
    mode: str = "review_first"
    """
    Automation mode:
    - "manual": operator must explicitly trigger everything
    - "review_first": operator approves before execution
    - "full_auto": auto-approve & execute safe tasks
    """
    
    dry_run: bool = True
    """If True, no external APIs are called. Drafts/previews only."""
    
    notes: Optional[str] = None
    """Reason for current settings or status notes."""


@dataclass
class OperatorDashboardView:
    """
    Complete operator dashboard state snapshot.
    
    Aggregates:
    - Brand status & health
    - Task queue state
    - Schedule/timeline
    - Feedback & anomalies
    - Automation controls
    
    This is the top-level view returned by OperatorDashboardService.
    """
    
    brand_id: str
    """Brand UUID."""
    
    brand_status: BrandStatusView
    """Current brand state (LBB, analytics)."""
    
    task_queue: TaskQueueView
    """Task queue counts and recent list."""
    
    schedule: ScheduleView
    """Upcoming scheduled executions."""
    
    feedback: FeedbackView
    """Latest feedback loop results."""
    
    automation: AutomationModeView
    """Current automation settings."""
    
    # Metadata
    snapshot_at: datetime = field(default_factory=datetime.utcnow)
    """When was this dashboard snapshot created?"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "brand_id": self.brand_id,
            "brand_status": {
                "brand_id": self.brand_status.brand_id,
                "brand_name": self.brand_status.brand_name,
                "key_persona": self.brand_status.key_persona,
                "primary_tone": self.brand_status.primary_tone,
                "top_channels": self.brand_status.top_channels,
                "risk_flags": self.brand_status.risk_flags,
                "last_updated_at": self.brand_status.last_updated_at.isoformat()
                    if self.brand_status.last_updated_at else None,
            },
            "task_queue": {
                "brand_id": self.task_queue.brand_id,
                "pending": self.task_queue.pending,
                "approved": self.task_queue.approved,
                "running": self.task_queue.running,
                "completed": self.task_queue.completed,
                "failed": self.task_queue.failed,
                "recent_tasks": self.task_queue.recent_tasks,
            },
            "schedule": {
                "brand_id": self.schedule.brand_id,
                "upcoming": self.schedule.upcoming,
                "overdue": self.schedule.overdue,
                "next_tick_at": self.schedule.next_tick_at.isoformat()
                    if self.schedule.next_tick_at else None,
            },
            "feedback": {
                "brand_id": self.feedback.brand_id,
                "last_snapshot_at": self.feedback.last_snapshot_at.isoformat()
                    if self.feedback.last_snapshot_at else None,
                "last_anomalies": self.feedback.last_anomalies,
                "last_run_summary": self.feedback.last_run_summary,
            },
            "automation": {
                "brand_id": self.automation.brand_id,
                "mode": self.automation.mode,
                "dry_run": self.automation.dry_run,
                "notes": self.automation.notes,
            },
            "snapshot_at": self.snapshot_at.isoformat(),
        }
