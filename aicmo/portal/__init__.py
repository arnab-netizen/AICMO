"""Client portal and approvals module.

Stage CP: Client Portal & Approvals
"""

from aicmo.portal.domain import (
    ApprovalStatus,
    AssetType,
    FeedbackPriority,
    ApprovalRequest,
    ClientFeedback,
    AssetVersion,
    ApprovalWorkflow,
    PortalAccess,
    PortalNotification,
    CollaborationSession,
    ApprovalSummary,
)

from aicmo.portal.service import (
    create_approval_request,
    submit_client_feedback,
    create_asset_version,
    grant_portal_access,
    generate_approval_summary,
    send_approval_notification,
    approve_request,
    request_changes,
)

__all__ = [
    # Enums
    "ApprovalStatus",
    "AssetType",
    "FeedbackPriority",
    
    # Domain models
    "ApprovalRequest",
    "ClientFeedback",
    "AssetVersion",
    "ApprovalWorkflow",
    "PortalAccess",
    "PortalNotification",
    "CollaborationSession",
    "ApprovalSummary",
    
    # Service functions
    "create_approval_request",
    "submit_client_feedback",
    "create_asset_version",
    "grant_portal_access",
    "generate_approval_summary",
    "send_approval_notification",
    "approve_request",
    "request_changes",
]
