"""
Social media posting adapters.

Concrete implementations of SocialPoster interface for:
- Instagram
- LinkedIn  
- Twitter

Each adapter handles platform-specific API interactions, authentication,
and content formatting.
"""

from typing import Optional
from datetime import datetime
from ..domain.execution import ContentItem, ExecutionResult, ExecutionStatus
from .interfaces import SocialPoster


class InstagramPoster(SocialPoster):
    """
    Instagram posting adapter using Instagram Graph API.
    
    Supports:
    - Feed posts (images, carousels)
    - Reels (video content)
    - Stories
    """
    
    def __init__(self, access_token: Optional[str] = None, account_id: Optional[str] = None):
        """
        Initialize Instagram poster with credentials.
        
        Args:
            access_token: Instagram Graph API access token
            account_id: Instagram Business Account ID
        """
        self.access_token = access_token
        self.account_id = account_id
        self._platform = "instagram"
    
    async def post(self, content: ContentItem) -> ExecutionResult:
        """
        Post content to Instagram.
        
        Mock implementation - returns success for testing.
        Production would call Instagram Graph API.
        """
        if not self.access_token or not self.account_id:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                platform=self._platform,
                error_message="Missing Instagram credentials (access_token or account_id)",
                executed_at=datetime.utcnow(),
            )
        
        # Mock successful post
        mock_post_id = f"ig_{content.project_id}_{content.id or 'draft'}"
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform=self._platform,
            platform_post_id=mock_post_id,
            executed_at=datetime.utcnow(),
            metadata={
                "caption": content.caption or content.body_text,
                "asset_type": content.asset_type,
                "hook": content.hook,
            }
        )
    
    async def validate_credentials(self) -> bool:
        """Check if Instagram credentials are valid."""
        # Mock validation - always True if credentials exist
        return bool(self.access_token and self.account_id)
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return self._platform


class LinkedInPoster(SocialPoster):
    """
    LinkedIn posting adapter using LinkedIn API.
    
    Supports:
    - Text posts
    - Image posts
    - Article shares
    - Company page posts
    """
    
    def __init__(self, access_token: Optional[str] = None, person_urn: Optional[str] = None):
        """
        Initialize LinkedIn poster with credentials.
        
        Args:
            access_token: LinkedIn OAuth 2.0 access token
            person_urn: LinkedIn person URN (e.g., urn:li:person:xyz)
        """
        self.access_token = access_token
        self.person_urn = person_urn
        self._platform = "linkedin"
    
    async def post(self, content: ContentItem) -> ExecutionResult:
        """
        Post content to LinkedIn.
        
        Mock implementation - returns success for testing.
        Production would call LinkedIn API v2.
        """
        if not self.access_token:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                platform=self._platform,
                error_message="Missing LinkedIn access token",
                executed_at=datetime.utcnow(),
            )
        
        # Mock successful post
        mock_post_id = f"li_{content.project_id}_{content.id or 'draft'}"
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform=self._platform,
            platform_post_id=mock_post_id,
            executed_at=datetime.utcnow(),
            metadata={
                "text": content.body_text,
                "hook": content.hook,
                "cta": content.cta,
                "tone": "professional",  # LinkedIn defaults to professional
            }
        )
    
    async def validate_credentials(self) -> bool:
        """Check if LinkedIn credentials are valid."""
        # Mock validation - always True if access_token exists
        return bool(self.access_token)
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return self._platform


class TwitterPoster(SocialPoster):
    """
    Twitter (X) posting adapter using Twitter API v2.
    
    Supports:
    - Tweets (text + media)
    - Threads (multiple connected tweets)
    - Replies
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
    ):
        """
        Initialize Twitter poster with OAuth 1.0a credentials.
        
        Args:
            api_key: Twitter API key (consumer key)
            api_secret: Twitter API secret (consumer secret)
            access_token: User access token
            access_token_secret: User access token secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self._platform = "twitter"
    
    async def post(self, content: ContentItem) -> ExecutionResult:
        """
        Post content to Twitter.
        
        Mock implementation - returns success for testing.
        Production would call Twitter API v2.
        """
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                platform=self._platform,
                error_message="Missing Twitter credentials (requires api_key, api_secret, access_token, access_token_secret)",
                executed_at=datetime.utcnow(),
            )
        
        # Mock successful post
        mock_post_id = f"tw_{content.project_id}_{content.id or 'draft'}"
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            platform=self._platform,
            platform_post_id=mock_post_id,
            executed_at=datetime.utcnow(),
            metadata={
                "text": content.body_text[:280],  # Twitter character limit
                "hook": content.hook,
                "is_thread": content.asset_type == "thread",
            }
        )
    
    async def validate_credentials(self) -> bool:
        """Check if Twitter credentials are valid."""
        # Mock validation - always True if all credentials exist
        return all([self.api_key, self.api_secret, self.access_token, self.access_token_secret])
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return self._platform
