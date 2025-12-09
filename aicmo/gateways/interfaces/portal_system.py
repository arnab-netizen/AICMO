"""Client portal system interface.

Stage CP: Client Portal & Approvals
Abstract interface for portal backends and notification systems.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from aicmo.portal.domain import (
    ApprovalRequest,
    ClientFeedback,
    PortalNotification,
    ApprovalStatus,
)


class PortalSystem(ABC):
    """
    Abstract interface for client portal systems.
    
    Stage CP: Skeleton interface - implement concrete adapters for:
    - Custom React/Next.js portal
    - WordPress client portal plugins
    - Asana/Monday.com (for approval workflows)
    - Frame.io (video review)
    - Figma/InVision (design review)
    - SharePoint/Google Drive (document collaboration)
    - etc.
    
    Future: Add real portal system integration here.
    """
    
    @abstractmethod
    def create_approval_request(
        self,
        request: ApprovalRequest
    ) -> str:
        """
        Create a new approval request in the portal.
        
        Args:
            request: Approval request details
            
        Returns:
            Request ID
            
        Raises:
            NotImplementedError: Stage CP skeleton
        """
        raise NotImplementedError("Stage CP: Portal system integration pending")
    
    @abstractmethod
    def get_approval_status(
        self,
        request_id: str
    ) -> ApprovalStatus:
        """
        Get current approval status.
        
        Args:
            request_id: Approval request ID
            
        Returns:
            Current approval status
            
        Raises:
            NotImplementedError: Stage CP skeleton
        """
        raise NotImplementedError("Stage CP: Status tracking integration pending")
    
    @abstractmethod
    def submit_feedback(
        self,
        feedback: ClientFeedback
    ) -> str:
        """
        Submit client feedback on an asset.
        
        Args:
            feedback: Client feedback details
            
        Returns:
            Feedback ID
            
        Raises:
            NotImplementedError: Stage CP skeleton
        """
        raise NotImplementedError("Stage CP: Feedback system integration pending")
    
    @abstractmethod
    def send_notification(
        self,
        notification: PortalNotification
    ) -> bool:
        """
        Send notification to portal user.
        
        Args:
            notification: Notification details
            
        Returns:
            True if sent successfully
            
        Raises:
            NotImplementedError: Stage CP skeleton
        """
        raise NotImplementedError("Stage CP: Notification system integration pending")
    
    @abstractmethod
    def get_pending_approvals(
        self,
        brand_name: str,
        reviewer_email: Optional[str] = None
    ) -> List[ApprovalRequest]:
        """
        Get pending approval requests.
        
        Args:
            brand_name: Brand to filter by
            reviewer_email: Optional reviewer filter
            
        Returns:
            List of pending approval requests
            
        Raises:
            NotImplementedError: Stage CP skeleton
        """
        raise NotImplementedError("Stage CP: Approval query integration pending")
    
    @abstractmethod
    def upload_asset_version(
        self,
        request_id: str,
        file_path: str,
        version_notes: str
    ) -> str:
        """
        Upload a new version of an asset.
        
        Args:
            request_id: Approval request ID
            file_path: Path to new asset version
            version_notes: Notes about changes
            
        Returns:
            Version ID
            
        Raises:
            NotImplementedError: Stage CP skeleton
        """
        raise NotImplementedError("Stage CP: Asset upload integration pending")
