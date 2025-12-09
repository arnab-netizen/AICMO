"""
Echo/dummy gateway adapters for testing.

Stage 3: Provides mock implementations that always succeed
without making actual API calls.
"""

from datetime import datetime
import uuid

from ..domain.execution import ContentItem, ExecutionResult, ExecutionStatus
from .interfaces import SocialPoster


class EchoSocialPoster(SocialPoster):
    """
    Echo social poster that simulates successful posting.
    
    Stage 3: Used for testing execution pipeline without
    actual social media API calls.
    """
    
    def __init__(self, platform: str = "echo"):
        """
        Initialize echo poster.
        
        Args:
            platform: Platform name for identification
        """
        self.platform = platform
    
    async def post(self, content: ContentItem) -> ExecutionResult:
        """
        Simulate successful post.
        
        Args:
            content: Content to "post"
            
        Returns:
            ExecutionResult with SUCCESS status and mock ID
        """
        mock_id = f"{self.platform}_{uuid.uuid4().hex[:8]}"
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform=self.platform,
            platform_post_id=mock_id,
            executed_at=datetime.utcnow()
        )
    
    async def validate_credentials(self) -> bool:
        """
        Echo adapter always validates successfully.
        
        Returns:
            True (always valid)
        """
        return True
    
    def get_platform_name(self) -> str:
        """
        Get platform name.
        
        Returns:
            Platform name string
        """
        return self.platform
