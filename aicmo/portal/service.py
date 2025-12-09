"""Client portal and approval service.

Stage CP: Client Portal & Approvals
Service layer for approval workflows, feedback management, and client collaboration.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from aicmo.domain.intake import ClientIntake
from aicmo.portal.domain import (
    ApprovalRequest,
    ClientFeedback,
    AssetVersion,
    ApprovalWorkflow,
    PortalAccess,
    PortalNotification,
    ApprovalSummary,
    ApprovalStatus,
    AssetType,
    FeedbackPriority,
)
from aicmo.memory.engine import log_event
from aicmo.learning.event_types import EventType

logger = logging.getLogger(__name__)


def create_approval_request(
    intake: ClientIntake,
    asset_type: AssetType,
    asset_name: str,
    asset_url: str,
    requested_by: str,
    reviewers: List[str],
    due_days: int = 3
) -> ApprovalRequest:
    """
    Create a new approval request for client review.
    
    Stage CP: Skeleton for approval workflow.
    Future: Integrate with portal backend and notification system.
    
    Args:
        intake: Client intake data
        asset_type: Type of asset
        asset_name: Name of asset
        asset_url: URL to asset
        requested_by: User requesting approval
        reviewers: List of reviewer emails
        due_days: Days until approval due
        
    Returns:
        ApprovalRequest ready for submission
    """
    logger.info(f"Creating approval request for {asset_name} ({intake.brand_name})")
    
    request = ApprovalRequest(
        request_id=str(uuid.uuid4()),
        brand_name=intake.brand_name,
        asset_type=asset_type,
        asset_name=asset_name,
        asset_url=asset_url,
        asset_version=1,
        status=ApprovalStatus.PENDING,
        requested_by=requested_by,
        requested_at=datetime.now(),
        assigned_reviewers=reviewers,
        due_date=datetime.now() + timedelta(days=due_days)
    )
    
    # Validate approval request before returning (G1: contracts layer)
    from aicmo.core.contracts import validate_approval_request
    request = validate_approval_request(request)
    
    # Learning: Log approval request creation
    log_event(
        EventType.CLIENT_APPROVAL_REQUESTED.value,
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "asset_type": asset_type.value,
            "asset_name": asset_name,
            "num_reviewers": len(reviewers)
        },
        tags=["portal", "approval", "workflow"]
    )
    
    logger.info(f"Approval request created: {request.request_id}")
    return request


def submit_client_feedback(
    approval_request_id: str,
    brand_name: str,
    reviewer_name: str,
    reviewer_email: str,
    feedback_text: str,
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
) -> ClientFeedback:
    """
    Submit client feedback on an asset.
    
    Stage CP: Skeleton for feedback collection.
    Future: Integrate with feedback management system.
    
    Args:
        approval_request_id: ID of approval request
        brand_name: Brand name
        reviewer_name: Name of reviewer
        reviewer_email: Email of reviewer
        feedback_text: Feedback content
        priority: Feedback priority
        
    Returns:
        ClientFeedback record
    """
    logger.info(f"Submitting feedback from {reviewer_name} for {brand_name}")
    
    feedback = ClientFeedback(
        feedback_id=str(uuid.uuid4()),
        approval_request_id=approval_request_id,
        brand_name=brand_name,
        reviewer_name=reviewer_name,
        reviewer_email=reviewer_email,
        feedback_text=feedback_text,
        priority=priority,
        is_addressed=False,
        created_at=datetime.now()
    )
    
    # Learning: Log feedback submission
    log_event(
        EventType.CLIENT_COMMENT_RECEIVED.value,
        project_id=brand_name,
        details={
            "brand_name": brand_name,
            "reviewer": reviewer_name,
            "priority": priority.value,
            "approval_request_id": approval_request_id
        },
        tags=["portal", "feedback", "client"]
    )
    
    logger.info(f"Feedback submitted: {feedback.feedback_id}")
    return feedback


def create_asset_version(
    approval_request_id: str,
    version_number: int,
    asset_url: str,
    change_summary: str,
    changed_by: str,
    addressed_feedback_ids: Optional[List[str]] = None
) -> AssetVersion:
    """
    Create a new version of an asset based on feedback.
    
    Stage CP: Skeleton for version control.
    Future: Integrate with asset storage system.
    
    Args:
        approval_request_id: Original approval request
        version_number: Version number
        asset_url: URL to new version
        change_summary: Summary of changes made
        changed_by: User who made changes
        addressed_feedback_ids: Feedback items addressed
        
    Returns:
        AssetVersion record
    """
    logger.info(f"Creating asset version {version_number} for request {approval_request_id}")
    
    version = AssetVersion(
        version_id=str(uuid.uuid4()),
        approval_request_id=approval_request_id,
        version_number=version_number,
        asset_url=asset_url,
        change_summary=change_summary,
        changed_by=changed_by,
        created_at=datetime.now(),
        addressed_feedback_ids=addressed_feedback_ids or []
    )
    
    # Learning: Log version creation
    log_event(
        EventType.CLIENT_APPROVAL_RESPONDED.value,
        project_id=approval_request_id,
        details={
            "approval_request_id": approval_request_id,
            "version_number": version_number,
            "feedback_addressed": len(addressed_feedback_ids) if addressed_feedback_ids else 0
        },
        tags=["portal", "version", "revision"]
    )
    
    logger.info(f"Asset version created: {version.version_id}")
    return version


def grant_portal_access(
    brand_name: str,
    user_email: str,
    user_name: str,
    user_role: str,
    can_approve: bool = False,
    expiry_days: Optional[int] = None
) -> PortalAccess:
    """
    Grant portal access to a client user.
    
    Stage CP: Skeleton for access management.
    Future: Integrate with authentication system.
    
    Args:
        brand_name: Brand name
        user_email: User email
        user_name: User name
        user_role: User role (client, stakeholder, etc.)
        can_approve: Whether user can approve assets
        expiry_days: Days until access expires
        
    Returns:
        PortalAccess record
    """
    logger.info(f"Granting portal access to {user_email} for {brand_name}")
    
    access = PortalAccess(
        access_id=str(uuid.uuid4()),
        brand_name=brand_name,
        user_email=user_email,
        user_name=user_name,
        user_role=user_role,
        can_approve=can_approve,
        can_comment=True,
        can_download=True,
        is_active=True,
        granted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=expiry_days) if expiry_days else None
    )
    
    # Learning: Log access grant
    log_event(
        EventType.CLIENT_PORTAL_ACCESSED.value,
        project_id=brand_name,
        details={
            "brand_name": brand_name,
            "user_email": user_email,
            "user_role": user_role,
            "can_approve": can_approve
        },
        tags=["portal", "access", "security"]
    )
    
    logger.info(f"Portal access granted: {access.access_id}")
    return access


def generate_approval_summary(
    intake: ClientIntake,
    days_back: int = 30
) -> ApprovalSummary:
    """
    Generate approval summary for a brand.
    
    Stage CP: Skeleton with placeholder metrics.
    Future: Query actual approval data from portal backend.
    
    Args:
        intake: Client intake data
        days_back: Days of history to summarize
        
    Returns:
        ApprovalSummary with metrics
    """
    logger.info(f"Generating approval summary for {intake.brand_name}")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Stage CP: Generate placeholder metrics
    total_requests = 24
    pending = 3
    approved = 18
    rejected = 1
    changes_requested = 2
    
    summary = ApprovalSummary(
        summary_id=str(uuid.uuid4()),
        brand_name=intake.brand_name,
        start_date=start_date,
        end_date=end_date,
        total_requests=total_requests,
        pending_approvals=pending,
        approved_count=approved,
        rejected_count=rejected,
        changes_requested_count=changes_requested,
        avg_approval_time_hours=36.5,
        overdue_requests=1,
        requests_by_type={
            "creative": 10,
            "copy": 6,
            "report": 5,
            "strategy_document": 3
        },
        approval_rate_by_type={
            "creative": 0.80,
            "copy": 0.83,
            "report": 1.0,
            "strategy_document": 0.67
        },
        generated_at=datetime.now()
    )
    
    # Learning: Log summary generation
    log_event(
        EventType.CLIENT_APPROVAL_APPROVED.value,
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "total_requests": total_requests,
            "approval_rate": approved / total_requests if total_requests > 0 else 0,
            "avg_approval_hours": summary.avg_approval_time_hours
        },
        tags=["portal", "approval", "summary"]
    )
    
    logger.info(f"Approval summary generated: {total_requests} requests, {approved} approved")
    return summary


# ═══════════════════════════════════════════════════════════════════════
# Helper Functions (Stage CP: Placeholder implementations)
# ═══════════════════════════════════════════════════════════════════════


def send_approval_notification(
    request: ApprovalRequest,
    reviewer_email: str
) -> PortalNotification:
    """
    Send approval request notification.
    
    Stage CP: Skeleton for notifications.
    Future: Integrate with email/SMS system.
    """
    logger.info(f"Sending approval notification to {reviewer_email}")
    
    notification = PortalNotification(
        notification_id=str(uuid.uuid4()),
        brand_name=request.brand_name,
        recipient_email=reviewer_email,
        notification_type="approval_requested",
        title=f"Review Requested: {request.asset_name}",
        message=f"You have been asked to review {request.asset_name}. Due: {request.due_date}",
        link_url=request.asset_url,
        is_read=False,
        is_sent=False,
        created_at=datetime.now()
    )
    
    return notification


def approve_request(
    request: ApprovalRequest,
    reviewer_name: str,
    approval_notes: Optional[str] = None
) -> ApprovalRequest:
    """
    Approve an approval request.
    
    Stage CP: Helper to update approval status.
    """
    logger.info(f"Approving request {request.request_id}")
    
    request.status = ApprovalStatus.APPROVED
    request.reviewed_by = reviewer_name
    request.reviewed_at = datetime.now()
    request.approval_notes = approval_notes
    
    return request


def request_changes(
    request: ApprovalRequest,
    reviewer_name: str,
    change_notes: str
) -> ApprovalRequest:
    """
    Request changes to an asset.
    
    Stage CP: Helper to request revisions.
    """
    logger.info(f"Requesting changes for {request.request_id}")
    
    request.status = ApprovalStatus.CHANGES_REQUESTED
    request.reviewed_by = reviewer_name
    request.reviewed_at = datetime.now()
    request.approval_notes = change_notes
    
    return request
