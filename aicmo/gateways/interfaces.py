"""
Abstract gateway interfaces for external service integrations.

Defines contracts that concrete adapters must implement for:
- Social media posting (Instagram, LinkedIn, Twitter)
- Email delivery
- CRM synchronization
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..domain.execution import ContentItem, ExecutionResult


class SocialPoster(ABC):
    """
    Abstract interface for social media posting adapters.
    
    Each platform (Instagram, LinkedIn, Twitter) implements this interface
    to handle platform-specific API calls, authentication, and formatting.
    """
    
    @abstractmethod
    async def post(self, content: ContentItem) -> ExecutionResult:
        """
        Post content to the social media platform.
        
        Args:
            content: The content item to post
            
        Returns:
            ExecutionResult with status, platform_post_id, and any errors
        """
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """
        Check if API credentials are valid and accessible.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the name of the platform (e.g., 'instagram', 'linkedin').
        
        Returns:
            Platform name as lowercase string
        """
        pass


class EmailSender(ABC):
    """
    Abstract interface for email delivery adapters.
    
    Supports various email service providers (SendGrid, Mailgun, SES, etc.)
    with consistent interface for sending marketing emails.
    """
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Send an email through the provider.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML content of the email
            from_email: Sender email address (uses default if not provided)
            from_name: Sender display name
            metadata: Additional tracking metadata
            
        Returns:
            ExecutionResult with status, message_id, and any errors
        """
        pass
    
    @abstractmethod
    async def validate_configuration(self) -> bool:
        """
        Check if email service is properly configured.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass


class CRMSyncer(ABC):
    """
    Abstract interface for CRM synchronization adapters.
    
    Handles syncing contact data, campaign results, and engagement metrics
    to CRM systems (HubSpot, Salesforce, etc.).
    """
    
    @abstractmethod
    async def sync_contact(
        self,
        email: str,
        properties: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Create or update a contact in the CRM.
        
        Args:
            email: Contact email address (unique identifier)
            properties: Contact properties to sync
            
        Returns:
            ExecutionResult with status, crm_contact_id, and any errors
        """
        pass
    
    @abstractmethod
    async def log_engagement(
        self,
        contact_email: str,
        engagement_type: str,
        content_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Log a contact engagement event in the CRM.
        
        Args:
            contact_email: Contact who engaged
            engagement_type: Type of engagement (view, click, reply, etc.)
            content_id: ID of the content they engaged with
            metadata: Additional engagement data
            
        Returns:
            ExecutionResult with status and any errors
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Check if CRM connection is active and valid.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass
