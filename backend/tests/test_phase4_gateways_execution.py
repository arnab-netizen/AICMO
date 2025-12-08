"""
Phase 4 tests: Gateways and Execution.

Tests for:
- Gateway interfaces and adapters (Instagram, LinkedIn, Twitter, Email)
- ExecutionService orchestration
- Status tracking and error handling
- Full workflow integration with execution
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from aicmo.domain import (
    ClientIntake,
    ContentItem,
    ExecutionStatus,
    ExecutionResult,
    PublishStatus,
)
from aicmo.gateways import (
    InstagramPoster,
    LinkedInPoster,
    TwitterPoster,
    EmailAdapter,
    ExecutionService,
    execute_content_item,
)
from aicmo.strategy.service import generate_strategy
from aicmo.creatives.service import generate_creatives

# Import backend models for mocking
from aicmo.io.client_reports import MarketingPlanView, StrategyPillar as BackendPillar


class TestPhase4GatewayAdapters:
    """Test gateway adapter implementations."""
    
    @pytest.mark.asyncio
    async def test_instagram_poster_success(self):
        """Test Instagram poster with valid credentials."""
        poster = InstagramPoster(access_token="test_token", account_id="test_account")
        
        content = ContentItem(
            project_id=1,
            platform="instagram",
            body_text="Check out our latest product!",
            caption="New product launch 🚀",
            hook="Transform your workflow",
            asset_type="reel",
        )
        
        result = await poster.post(content)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.platform == "instagram"
        assert result.platform_post_id.startswith("ig_")
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_instagram_poster_missing_credentials(self):
        """Test Instagram poster fails without credentials."""
        poster = InstagramPoster()  # No credentials
        
        content = ContentItem(
            project_id=1,
            platform="instagram",
            body_text="Test post",
        )
        
        result = await poster.post(content)
        
        assert result.status == ExecutionStatus.FAILED
        assert "Missing Instagram credentials" in result.error_message
    
    @pytest.mark.asyncio
    async def test_linkedin_poster_success(self):
        """Test LinkedIn poster with valid credentials."""
        poster = LinkedInPoster(access_token="test_token")
        
        content = ContentItem(
            project_id=2,
            platform="linkedin",
            body_text="Excited to share our Q4 results!",
            hook="Leadership insights",
            cta="Learn more",
        )
        
        result = await poster.post(content)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.platform == "linkedin"
        assert result.platform_post_id.startswith("li_")
    
    @pytest.mark.asyncio
    async def test_twitter_poster_success(self):
        """Test Twitter poster with valid credentials."""
        poster = TwitterPoster(
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_token_secret="token_secret",
        )
        
        content = ContentItem(
            project_id=3,
            platform="twitter",
            body_text="Quick update on our latest feature!",
            hook="Breaking news",
            asset_type="thread",
        )
        
        result = await poster.post(content)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.platform == "twitter"
        assert result.platform_post_id.startswith("tw_")
    
    @pytest.mark.asyncio
    async def test_email_adapter_success(self):
        """Test email adapter sends successfully."""
        adapter = EmailAdapter(api_key="test_key")
        
        result = await adapter.send_email(
            to_email="customer@example.com",
            subject="Your weekly newsletter",
            html_body="<h1>Hello!</h1><p>Check out our latest content.</p>",
            metadata={"campaign": "newsletter_2024"},
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.platform == "email"
        assert result.platform_post_id.startswith("email_")
    
    @pytest.mark.asyncio
    async def test_email_adapter_invalid_recipient(self):
        """Test email adapter fails with invalid recipient."""
        adapter = EmailAdapter(api_key="test_key")
        
        result = await adapter.send_email(
            to_email="invalid-email",
            subject="Test",
            html_body="<p>Test</p>",
        )
        
        assert result.status == ExecutionStatus.FAILED
        assert "Invalid recipient email" in result.error_message


class TestPhase4ExecutionService:
    """Test ExecutionService orchestration."""
    
    @pytest.mark.asyncio
    async def test_execution_service_instagram(self):
        """Test ExecutionService routes to Instagram gateway."""
        instagram = InstagramPoster(access_token="token", account_id="account")
        service = ExecutionService(instagram_poster=instagram)
        
        content = ContentItem(
            project_id=10,
            platform="instagram",
            body_text="Test content",
        )
        
        result = await service.execute(content)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.platform == "instagram"
    
    @pytest.mark.asyncio
    async def test_execution_service_linkedin(self):
        """Test ExecutionService routes to LinkedIn gateway."""
        linkedin = LinkedInPoster(access_token="token")
        service = ExecutionService(linkedin_poster=linkedin)
        
        content = ContentItem(
            project_id=11,
            platform="linkedin",
            body_text="Test content",
        )
        
        result = await service.execute(content)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.platform == "linkedin"
    
    @pytest.mark.asyncio
    async def test_execution_service_no_gateway(self):
        """Test ExecutionService fails gracefully when gateway missing."""
        service = ExecutionService()  # No gateways registered
        
        content = ContentItem(
            project_id=12,
            platform="facebook",  # Unsupported platform
            body_text="Test content",
        )
        
        result = await service.execute(content)
        
        assert result.status == ExecutionStatus.FAILED
        assert "No gateway registered" in result.error_message
    
    @pytest.mark.asyncio
    async def test_execution_service_batch(self):
        """Test ExecutionService executes multiple items."""
        instagram = InstagramPoster(access_token="token", account_id="account")
        linkedin = LinkedInPoster(access_token="token")
        service = ExecutionService(
            instagram_poster=instagram,
            linkedin_poster=linkedin,
        )
        
        items = [
            ContentItem(project_id=20, platform="instagram", body_text="IG post"),
            ContentItem(project_id=20, platform="linkedin", body_text="LI post"),
            ContentItem(project_id=20, platform="twitter", body_text="TW post"),  # Will fail
        ]
        
        results = await service.execute_batch(items)
        
        assert len(results) == 3
        assert results[0].status == ExecutionStatus.SUCCESS  # Instagram
        assert results[1].status == ExecutionStatus.SUCCESS  # LinkedIn
        assert results[2].status == ExecutionStatus.FAILED  # Twitter (no gateway)
    
    @pytest.mark.asyncio
    async def test_execution_service_register_gateway(self):
        """Test dynamic gateway registration."""
        service = ExecutionService()
        
        # Initially no gateways
        assert len(service.get_registered_platforms()) == 0
        
        # Register Instagram
        instagram = InstagramPoster(access_token="token", account_id="account")
        service.register_gateway("instagram", instagram)
        
        assert "instagram" in service.get_registered_platforms()
        assert len(service.get_registered_platforms()) == 1
    
    @pytest.mark.asyncio
    async def test_execution_service_validate_gateways(self):
        """Test gateway credential validation."""
        instagram = InstagramPoster(access_token="token", account_id="account")
        linkedin = LinkedInPoster()  # Missing credentials
        
        service = ExecutionService(
            instagram_poster=instagram,
            linkedin_poster=linkedin,
        )
        
        validation = await service.validate_all_gateways()
        
        assert validation["instagram"] is True  # Has credentials
        assert validation["linkedin"] is False  # Missing credentials


@pytest.mark.asyncio
async def test_phase4_full_workflow_integration():
    """
    Test full workflow: Intake → Strategy → Creatives → Execution.
    
    Verifies end-to-end flow including gateway execution.
    """
    # Mock strategy generation (mock at import location)
    mock_marketing_plan = MarketingPlanView(
        executive_summary="Test summary",
        situation_analysis="Test analysis",
        strategy="Test narrative",
        pillars=[
            BackendPillar(name="Pillar 1", description="Headline 1", kpi_impact="Body 1"),
            BackendPillar(name="Pillar 2", description="Headline 2", kpi_impact="Body 2"),
        ]
    )
    
    with patch("backend.generators.marketing_plan.generate_marketing_plan", new=AsyncMock(return_value=mock_marketing_plan)):
        # 1. Create intake
        intake = ClientIntake(
            brand_name="TechCorp",
            industry="SaaS",
            target_audience="B2B developers",
            primary_goal="lead_generation",
        )
        
        # 2. Generate strategy
        strategy = await generate_strategy(intake)
        assert len(strategy.pillars) == 2
        
        # 3. Generate creatives for Instagram and LinkedIn
        library = await generate_creatives(
            intake=intake,
            strategy=strategy,
            platforms=["instagram", "linkedin"],
        )
        
        # 4. Convert to content items
        items = library.to_content_items(
            project_id=100,
            scheduled_date="2024-12-20",
        )
        
        # Should have 4 items (2 platforms × 2 pillars)
        assert len(items) == 4
        
        # 5. Set up execution service with gateways
        instagram = InstagramPoster(access_token="token", account_id="account")
        linkedin = LinkedInPoster(access_token="token")
        
        execution_service = ExecutionService(
            instagram_poster=instagram,
            linkedin_poster=linkedin,
        )
        
        # 6. Execute all items
        results = await execution_service.execute_batch(items)
        
        # All should succeed
        assert len(results) == 4
        assert all(r.status == ExecutionStatus.SUCCESS for r in results)
        
        # Verify platform routing
        ig_results = [r for r in results if r.platform == "instagram"]
        li_results = [r for r in results if r.platform == "linkedin"]
        
        assert len(ig_results) == 2
        assert len(li_results) == 2
        
        # All should have platform post IDs
        assert all(r.platform_post_id for r in results)


@pytest.mark.asyncio
async def test_execute_content_item_convenience_function():
    """Test standalone execute_content_item function."""
    instagram = InstagramPoster(access_token="token", account_id="account")
    service = ExecutionService(instagram_poster=instagram)
    
    content = ContentItem(
        project_id=200,
        platform="instagram",
        body_text="Quick test",
    )
    
    result = await execute_content_item(content, service)
    
    assert result.status == ExecutionStatus.SUCCESS
    assert result.platform == "instagram"
