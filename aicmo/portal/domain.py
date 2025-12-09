"""Client portal and approval domain models.

Stage CP: Client Portal & Approvals
Skeleton implementation for client collaboration, asset approvals, and feedback management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from aicmo.domain.base import AicmoBaseModel


class ApprovalStatus(str, Enum):
    """Asset approval status."""
    
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class AssetType(str, Enum):
    """Types of assets requiring approval."""
    
    CREATIVE = "creative"
    COPY = "copy"
    STRATEGY_DOCUMENT = "strategy_document"
    CAMPAIGN_PLAN = "campaign_plan"
    REPORT = "report"
    PRESENTATION = "presentation"
    WEBSITE_DESIGN = "website_design"
    VIDEO = "video"


class FeedbackPriority(str, Enum):
    """Feedback priority levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequest(AicmoBaseModel):
    """
    Request for client approval on an asset.
    
    Stage CP: Skeleton for approval workflow.
    """
    
    request_id: str
    brand_name: str
    
    # Asset details
    asset_type: AssetType
    asset_name: str
    asset_url: Optional[str] = None
    asset_version: int = 1
    
    # Approval
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str  # User who requested approval
    requested_at: datetime
    
    # Reviewers
    assigned_reviewers: List[str] = []  # User IDs or emails
    
    # Deadlines
    due_date: Optional[datetime] = None
    
    # Status tracking
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    # Notes
    submission_notes: Optional[str] = None
    approval_notes: Optional[str] = None


class ClientFeedback(AicmoBaseModel):
    """
    Client feedback on an asset.
    
    Stage CP: Skeleton for feedback collection.
    """
    
    feedback_id: str
    approval_request_id: str
    brand_name: str
    
    # Feedback details
    reviewer_name: str
    reviewer_email: str
    feedback_text: str
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    
    # Context
    feedback_on_section: Optional[str] = None  # Specific section of asset
    timestamp_in_video: Optional[float] = None  # For video feedback
    coordinates: Optional[Dict[str, float]] = None  # For visual feedback (x, y)
    
    # Status
    is_addressed: bool = False
    addressed_by: Optional[str] = None
    addressed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    # Metadata
    created_at: datetime


class AssetVersion(AicmoBaseModel):
    """
    Version of an asset in the approval process.
    
    Stage CP: Skeleton for version control.
    """
    
    version_id: str
    approval_request_id: str
    
    # Version info
    version_number: int
    asset_url: str
    
    # Changes
    change_summary: str
    changed_by: str
    created_at: datetime
    
    # Parent version
    parent_version_id: Optional[str] = None
    
    # Feedback that triggered this version
    addressed_feedback_ids: List[str] = []


class ApprovalWorkflow(AicmoBaseModel):
    """
    Multi-stage approval workflow.
    
    Stage CP: Skeleton for complex approval chains.
    """
    
    workflow_id: str
    brand_name: str
    workflow_name: str
    
    # Workflow stages
    stages: List[Dict[str, Any]] = []  # Stage definitions
    current_stage: int = 0
    
    # Overall status
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    # Asset being approved
    approval_request_id: str
    
    # Progress tracking
    started_at: datetime
    completed_at: Optional[datetime] = None


class PortalAccess(AicmoBaseModel):
    """
    Client portal access configuration.
    
    Stage CP: Skeleton for access control.
    """
    
    access_id: str
    brand_name: str
    
    # User details
    user_email: str
    user_name: str
    user_role: str  # e.g., "client", "stakeholder", "approver"
    
    # Permissions
    can_approve: bool = False
    can_comment: bool = True
    can_download: bool = True
    can_upload: bool = False
    
    # Access control
    is_active: bool = True
    granted_at: datetime
    expires_at: Optional[datetime] = None
    
    # Activity tracking
    last_login: Optional[datetime] = None
    login_count: int = 0


class PortalNotification(AicmoBaseModel):
    """
    Notification for portal users.
    
    Stage CP: Skeleton for notification system.
    """
    
    notification_id: str
    brand_name: str
    
    # Recipient
    recipient_email: str
    
    # Notification details
    notification_type: str  # e.g., "approval_requested", "feedback_received", "asset_approved"
    title: str
    message: str
    link_url: Optional[str] = None
    
    # Status
    is_read: bool = False
    is_sent: bool = False
    
    # Timestamps
    created_at: datetime
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None


class CollaborationSession(AicmoBaseModel):
    """
    Real-time collaboration session.
    
    Stage CP: Skeleton for live collaboration.
    """
    
    session_id: str
    brand_name: str
    
    # Session details
    asset_id: str
    asset_name: str
    
    # Participants
    participants: List[Dict[str, str]] = []  # name, email, role
    host: str
    
    # Session state
    is_active: bool = True
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    # Activity
    comments_count: int = 0
    decisions_made: List[str] = []


class ApprovalSummary(AicmoBaseModel):
    """
    Summary of approvals for a brand.
    
    Stage CP: Skeleton for approval dashboard.
    """
    
    summary_id: str
    brand_name: str
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Counts
    total_requests: int = 0
    pending_approvals: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    changes_requested_count: int = 0
    
    # Performance
    avg_approval_time_hours: float = 0.0
    overdue_requests: int = 0
    
    # By asset type
    requests_by_type: Dict[str, int] = {}
    approval_rate_by_type: Dict[str, float] = {}
    
    # Generated
    generated_at: datetime
