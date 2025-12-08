"""
Execution service for publishing content through gateway adapters.

Orchestrates content delivery through social media, email, and CRM gateways
with status tracking and error handling.
"""

from typing import Dict, Optional, List
from datetime import datetime
from ..domain.execution import ContentItem, ExecutionResult, ExecutionStatus, PublishStatus
from .interfaces import SocialPoster, EmailSender
from .social import InstagramPoster, LinkedInPoster, TwitterPoster
from .email import EmailAdapter


class ExecutionService:
    """
    Service for executing content delivery through gateways.
    
    Manages:
    - Gateway selection based on platform
    - Execution attempts with status tracking
    - Error handling and retry logic
    """
    
    def __init__(
        self,
        instagram_poster: Optional[InstagramPoster] = None,
        linkedin_poster: Optional[LinkedInPoster] = None,
        twitter_poster: Optional[TwitterPoster] = None,
        email_adapter: Optional[EmailAdapter] = None,
    ):
        """
        Initialize execution service with gateway adapters.
        
        Args:
            instagram_poster: Instagram posting adapter
            linkedin_poster: LinkedIn posting adapter
            twitter_poster: Twitter posting adapter
            email_adapter: Email delivery adapter
        """
        self.gateways: Dict[str, SocialPoster | EmailAdapter] = {}
        
        if instagram_poster:
            self.gateways["instagram"] = instagram_poster
        if linkedin_poster:
            self.gateways["linkedin"] = linkedin_poster
        if twitter_poster:
            self.gateways["twitter"] = twitter_poster
        if email_adapter:
            self.gateways["email"] = email_adapter
    
    def register_gateway(self, platform: str, gateway: SocialPoster | EmailAdapter) -> None:
        """
        Register a gateway adapter for a platform.
        
        Args:
            platform: Platform name (e.g., "instagram", "email")
            gateway: Gateway adapter instance
        """
        self.gateways[platform] = gateway
    
    async def execute(self, content: ContentItem) -> ExecutionResult:
        """
        Execute content delivery through the appropriate gateway.
        
        Args:
            content: Content item to publish
            
        Returns:
            ExecutionResult with status and platform response
        """
        platform = content.platform.lower()
        
        # Check if gateway is registered
        if platform not in self.gateways:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                platform=platform,
                error_message=f"No gateway registered for platform: {platform}",
                executed_at=datetime.utcnow(),
            )
        
        gateway = self.gateways[platform]
        
        # Execute through gateway
        try:
            result = await gateway.post(content)
            return result
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                platform=platform,
                error_message=f"Gateway execution error: {str(e)}",
                executed_at=datetime.utcnow(),
            )
    
    async def execute_batch(self, items: List[ContentItem]) -> List[ExecutionResult]:
        """
        Execute multiple content items in batch.
        
        Args:
            items: List of content items to publish
            
        Returns:
            List of execution results (one per item)
        """
        results = []
        for item in items:
            result = await self.execute(item)
            results.append(result)
        return results
    
    async def validate_all_gateways(self) -> Dict[str, bool]:
        """
        Validate credentials for all registered gateways.
        
        Returns:
            Dict mapping platform name to validation status
        """
        validation_results = {}
        
        for platform, gateway in self.gateways.items():
            try:
                if isinstance(gateway, SocialPoster):
                    is_valid = await gateway.validate_credentials()
                elif isinstance(gateway, EmailAdapter):
                    is_valid = await gateway.validate_configuration()
                else:
                    is_valid = False
                
                validation_results[platform] = is_valid
            except Exception:
                validation_results[platform] = False
        
        return validation_results
    
    def get_registered_platforms(self) -> List[str]:
        """
        Get list of registered platform names.
        
        Returns:
            List of platform names with registered gateways
        """
        return list(self.gateways.keys())


async def execute_content_item(
    content: ContentItem,
    execution_service: ExecutionService,
) -> ExecutionResult:
    """
    Convenience function to execute a single content item.
    
    Args:
        content: Content item to publish
        execution_service: Configured execution service
        
    Returns:
        ExecutionResult with status and details
    """
    return await execution_service.execute(content)
