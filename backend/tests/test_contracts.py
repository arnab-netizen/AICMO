"""
Tests for validation/contracts layer.

Ensures validators correctly enforce non-empty fields, no placeholders, and proper structure.
"""

import pytest
from datetime import datetime, date, timedelta

from aicmo.core.contracts import (
    ensure_non_empty_string,
    ensure_non_empty_list,
    ensure_no_placeholders,
    ensure_min_length,
    validate_strategy_doc,
    validate_creative_assets,
    validate_media_plan,
    validate_performance_dashboard,
    validate_pm_task,
    validate_approval_request,
    validate_pitch_deck,
    validate_brand_core,
    PLACEHOLDER_STRINGS,
)

from aicmo.domain.strategy import StrategyDoc, StrategyPillar
from aicmo.creatives.domain import CreativeAsset
from aicmo.domain.execution import CreativeVariant
from aicmo.media.domain import MediaCampaignPlan, MediaChannel, MediaChannelType, MediaObjective
from aicmo.analytics.domain import PerformanceDashboard
from aicmo.pm.domain import Task, TaskStatus, TaskPriority
from aicmo.portal.domain import ApprovalRequest, AssetType, ApprovalStatus
from aicmo.pitch.domain import PitchDeck, PitchSection
from aicmo.brand.domain import BrandCore


# Tests for generic helpers
class TestGenericHelpers:
    def test_ensure_non_empty_string_valid(self):
        """Valid non-empty string passes"""
        result = ensure_non_empty_string("Hello World", "test_field")
        assert result == "Hello World"
    
    def test_ensure_non_empty_string_empty_fails(self):
        """Empty string raises ValueError"""
        with pytest.raises(ValueError, match="test_field cannot be empty"):
            ensure_non_empty_string("", "test_field")
    
    def test_ensure_non_empty_string_whitespace_fails(self):
        """Whitespace-only string raises ValueError"""
        with pytest.raises(ValueError, match="test_field cannot be empty"):
            ensure_non_empty_string("   ", "test_field")
    
    def test_ensure_non_empty_list_valid(self):
        """Valid non-empty list passes"""
        result = ensure_non_empty_list([1, 2, 3], "test_list")
        assert result == [1, 2, 3]
    
    def test_ensure_non_empty_list_empty_fails(self):
        """Empty list raises ValueError"""
        with pytest.raises(ValueError, match="test_list cannot be empty"):
            ensure_non_empty_list([], "test_list")
    
    def test_ensure_no_placeholders_valid(self):
        """Text without placeholders passes"""
        result = ensure_no_placeholders("This is real content", "test_context")
        assert result == "This is real content"
    
    def test_ensure_no_placeholders_tbd_fails(self):
        """Text with TBD placeholder raises ValueError"""
        with pytest.raises(ValueError, match="contains placeholder text"):
            ensure_no_placeholders("This is TBD for now", "test_context")
    
    def test_ensure_no_placeholders_not_specified_fails(self):
        """Text with 'Not specified' placeholder raises ValueError"""
        with pytest.raises(ValueError, match="contains placeholder text"):
            ensure_no_placeholders("The value is Not specified", "test_context")
    
    def test_ensure_min_length_valid(self):
        """Text meeting minimum length passes"""
        result = ensure_min_length("Hello World", 5, "test_field")
        assert result == "Hello World"
    
    def test_ensure_min_length_too_short_fails(self):
        """Text below minimum length raises ValueError"""
        with pytest.raises(ValueError, match="test_field must be at least"):
            ensure_min_length("Hi", 10, "test_field")


# Tests for StrategyDoc validation
class TestStrategyDocValidation:
    def test_validate_strategy_doc_valid(self):
        """Valid StrategyDoc passes validation"""
        doc = StrategyDoc(
            brand_name="Test Brand",
            industry="Technology",
            executive_summary="This is a comprehensive marketing strategy designed to increase brand awareness and drive customer engagement through targeted digital campaigns across multiple channels.",
            situation_analysis="Current market analysis showing opportunities",
            strategy_narrative="Strategy details with comprehensive approach",
            pillars=[
                StrategyPillar(name="Digital Marketing", description="Focus on digital channels", kpi_impact="20% increase"),
                StrategyPillar(name="Brand Building", description="Strengthen brand identity", kpi_impact="15% lift")
            ],
            primary_goal="Growth",
            timeline="Q1 2025",
            status="DRAFT"
        )
        
        result = validate_strategy_doc(doc)
        assert result == doc
    
    def test_validate_strategy_doc_empty_summary_fails(self):
        """StrategyDoc with empty summary fails"""
        doc = StrategyDoc(
            brand_name="Test Brand",
            industry="Technology",
            executive_summary="",
            situation_analysis="Analysis",
            strategy_narrative="Strategy",
            pillars=[StrategyPillar(name="Digital", description="Desc", kpi_impact="Impact")],
            primary_goal="Growth",
            timeline="Q1",
            status="DRAFT"
        )
        
        with pytest.raises(ValueError, match="executive_summary cannot be empty"):
            validate_strategy_doc(doc)
    
    def test_validate_strategy_doc_empty_pillars_fails(self):
        """StrategyDoc with empty pillars list fails"""
        doc = StrategyDoc(
            brand_name="Test Brand",
            industry="Technology",
            executive_summary="This is a comprehensive summary with enough text to pass minimum length validation",
            situation_analysis="Analysis",
            strategy_narrative="Strategy",
            pillars=[],
            primary_goal="Growth",
            timeline="Q1",
            status="DRAFT"
        )
        
        with pytest.raises(ValueError, match="pillars cannot be empty"):
            validate_strategy_doc(doc)


# Tests for CreativeAsset validation
class TestCreativeAssetsValidation:
    def test_validate_creative_assets_valid(self):
        """Valid creative assets pass validation"""
        assets = [
            CreativeVariant(
                platform="instagram",
                format="post",
                hook="Attention-grabbing hook here",
                caption="This is a compelling caption that tells a story and engages the audience effectively"
            ),
            CreativeVariant(
                platform="linkedin",
                format="article",
                hook="Professional hook for LinkedIn",
                caption="Professional content for business audience with clear value proposition"
            )
        ]
        
        result = validate_creative_assets(assets)
        assert result == assets
    
    def test_validate_creative_assets_empty_list_fails(self):
        """Empty creative assets list fails"""
        with pytest.raises(ValueError, match="creative_assets cannot be empty"):
            validate_creative_assets([])
    
    def test_validate_creative_assets_placeholder_in_caption_fails(self):
        """Creative assets with placeholder in caption fails"""
        assets = [
            CreativeVariant(
                platform="instagram",
                format="post",
                hook="Valid hook here",
                caption="TBD - Needs to be written later"
            )
        ]
        
        with pytest.raises(ValueError, match="contains placeholder text"):
            validate_creative_assets(assets)
    
    def test_validate_creative_assets_caption_too_short_fails(self):
        """Creative assets with caption too short fails"""
        assets = [
            CreativeVariant(
                platform="instagram",
                format="post",
                hook="Valid hook here",
                caption="Too short"
            )
        ]
        
        with pytest.raises(ValueError, match="must be at least 20 characters"):
            validate_creative_assets(assets)


# Tests for MediaCampaignPlan validation
class TestMediaPlanValidation:
    def test_validate_media_plan_valid(self):
        """Valid media plan passes validation"""
        plan = MediaCampaignPlan(
            campaign_name="Test Campaign",
            brand_name="Test Brand",
            objective=MediaObjective.AWARENESS,
            total_budget=10000.0,
            flight_start=datetime.now(),
            flight_end=datetime.now() + timedelta(days=30),
            channels=[
                MediaChannel(
                    channel_type=MediaChannelType.SOCIAL,
                    platform="Facebook Ads",
                    budget_allocated=5000.0
                ),
                MediaChannel(
                    channel_type=MediaChannelType.SEARCH,
                    platform="Google Ads",
                    budget_allocated=5000.0
                )
            ],
            target_audiences=["Tech professionals"],
            key_messages=["Message 1"],
            created_at=datetime.now()
        )
        
        result = validate_media_plan(plan)
        assert result == plan
    
    def test_validate_media_plan_empty_channels_fails(self):
        """Media plan with empty channels fails"""
        plan = MediaCampaignPlan(
            campaign_name="Test Campaign",
            brand_name="Test Brand",
            objective=MediaObjective.AWARENESS,
            total_budget=10000.0,
            flight_start=datetime.now(),
            flight_end=datetime.now() + timedelta(days=30),
            channels=[],
            target_audiences=["Tech professionals"],
            key_messages=["Message 1"],
            created_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="channels cannot be empty"):
            validate_media_plan(plan)
    
    def test_validate_media_plan_zero_budget_fails(self):
        """Media plan with zero total budget fails"""
        plan = MediaCampaignPlan(
            campaign_name="Test Campaign",
            brand_name="Test Brand",
            objective=MediaObjective.AWARENESS,
            total_budget=0.0,
            flight_start=datetime.now(),
            flight_end=datetime.now() + timedelta(days=30),
            channels=[
                MediaChannel(
                    channel_type=MediaChannelType.SOCIAL,
                    platform="Facebook",
                    budget_allocated=1000.0
                )
            ],
            target_audiences=["Tech professionals"],
            key_messages=["Message 1"],
            created_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="Total budget must be positive"):
            validate_media_plan(plan)


# Tests for PerformanceDashboard validation
class TestPerformanceDashboardValidation:
    def test_validate_performance_dashboard_valid(self):
        """Valid performance dashboard passes validation"""
        dashboard = PerformanceDashboard(
            dashboard_id="test-123",
            brand_name="Test Brand",
            current_period_start=datetime.now() - timedelta(days=7),
            current_period_end=datetime.now(),
            current_metrics={"impressions": 10000, "clicks": 500, "conversions": 25},
            previous_period_metrics={"impressions": 8000, "clicks": 400},
            percent_changes={"impressions": 25.0, "clicks": 25.0},
            goals={"conversions": 50},
            goal_progress={"conversions": 50.0},
            trending_up=["impressions"],
            trending_down=[],
            critical_issues=[],
            opportunities=["Increase budget on high-performing channels"],
            last_updated=datetime.now()
        )
        
        result = validate_performance_dashboard(dashboard)
        assert result == dashboard
    
    def test_validate_performance_dashboard_empty_metrics_fails(self):
        """Performance dashboard with empty metrics fails"""
        dashboard = PerformanceDashboard(
            dashboard_id="test-123",
            brand_name="Test Brand",
            current_period_start=datetime.now() - timedelta(days=7),
            current_period_end=datetime.now(),
            current_metrics={},
            previous_period_metrics={},
            percent_changes={},
            goals={},
            goal_progress={},
            trending_up=[],
            trending_down=[],
            critical_issues=[],
            opportunities=[],
            last_updated=datetime.now()
        )
        
        with pytest.raises(ValueError, match="current_metrics cannot be empty"):
            validate_performance_dashboard(dashboard)


# Tests for Task validation
class TestPMTaskValidation:
    def test_validate_pm_task_valid(self):
        """Valid PM task passes validation"""
        task = Task(
            task_id="task-123",
            brand_name="Test Brand",
            project_id="proj-1",
            title="Complete marketing strategy",
            description="Develop comprehensive strategy document",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            created_at=datetime.now(),
            due_date=date.today() + timedelta(days=7)
        )
        
        result = validate_pm_task(task)
        assert result == task
    
    def test_validate_pm_task_empty_title_fails(self):
        """PM task with empty title fails"""
        task = Task(
            task_id="task-123",
            brand_name="Test Brand",
            project_id="proj-1",
            title="",
            description="Description",
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.MEDIUM,
            created_at=datetime.now(),
            due_date=date.today() + timedelta(days=7)
        )
        
        with pytest.raises(ValueError, match="task.title cannot be empty"):
            validate_pm_task(task)
    
    def test_validate_pm_task_placeholder_in_title_fails(self):
        """PM task with placeholder in title fails"""
        task = Task(
            task_id="task-123",
            brand_name="Test Brand",
            project_id="proj-1",
            title="TBD - Need to define task",
            description="Description",
            status=TaskStatus.NOT_STARTED,
            priority=TaskPriority.MEDIUM,
            created_at=datetime.now(),
            due_date=date.today() + timedelta(days=7)
        )
        
        with pytest.raises(ValueError, match="contains placeholder text"):
            validate_pm_task(task)


# Tests for ApprovalRequest validation
class TestApprovalRequestValidation:
    def test_validate_approval_request_valid(self):
        """Valid approval request passes validation"""
        request = ApprovalRequest(
            request_id="req-123",
            brand_name="Test Brand",
            asset_type=AssetType.CREATIVE,
            asset_name="Facebook Ad Campaign",
            asset_url="https://example.com/asset",
            asset_version=1,
            status=ApprovalStatus.PENDING,
            requested_by="john@example.com",
            requested_at=datetime.now(),
            assigned_reviewers=["client@example.com"],
            due_date=datetime.now() + timedelta(days=3),
            submission_notes="Please review the new creative assets for Facebook campaign targeting tech professionals"
        )
        
        result = validate_approval_request(request)
        assert result == request
    
    def test_validate_approval_request_empty_title_fails(self):
        """Approval request with empty asset name fails"""
        request = ApprovalRequest(
            request_id="req-123",
            brand_name="Test Brand",
            asset_type=AssetType.CREATIVE,
            asset_name="",
            asset_url="https://example.com",
            asset_version=1,
            status=ApprovalStatus.PENDING,
            requested_by="john@example.com",
            requested_at=datetime.now(),
            assigned_reviewers=["client@example.com"],
            due_date=datetime.now() + timedelta(days=3)
        )
        
        with pytest.raises(ValueError, match="approval_request.asset_name cannot be empty"):
            validate_approval_request(request)
    
    def test_validate_approval_request_placeholder_fails(self):
        """Approval request with placeholder in submission notes fails"""
        request = ApprovalRequest(
            request_id="req-123",
            brand_name="Test Brand",
            asset_type=AssetType.CREATIVE,
            asset_name="Valid Asset Name",
            asset_url="https://example.com",
            asset_version=1,
            status=ApprovalStatus.PENDING,
            requested_by="john@example.com",
            requested_at=datetime.now(),
            assigned_reviewers=["client@example.com"],
            due_date=datetime.now() + timedelta(days=3),
            submission_notes="TBD - Need to add notes"
        )
        
        with pytest.raises(ValueError, match="contains placeholder text"):
            validate_approval_request(request)


# Tests for PitchDeck validation
class TestPitchDeckValidation:
    def test_validate_pitch_deck_valid(self):
        """Valid pitch deck passes validation"""
        deck = PitchDeck(
            prospect_id=123,
            title="Marketing Strategy for TechCorp",
            subtitle="Comprehensive digital marketing approach",
            sections=[
                PitchSection(title="Problem", content="Current challenges in the market", slide_type="text", order=1),
                PitchSection(title="Solution", content="Our proposed marketing strategy", slide_type="text", order=2)
            ],
            executive_summary="Summary here",
            key_benefits=["Benefit 1", "Benefit 2"],
            target_duration_minutes=30
        )
        
        result = validate_pitch_deck(deck)
        assert result == deck
    
    def test_validate_pitch_deck_empty_slides_fails(self):
        """Pitch deck with empty sections fails"""
        deck = PitchDeck(
            prospect_id=123,
            title="Marketing Strategy",
            subtitle="Subtitle",
            sections=[],
            executive_summary="Summary",
            key_benefits=["Benefit"],
            target_duration_minutes=30
        )
        
        with pytest.raises(ValueError, match="pitch_deck.sections cannot be empty"):
            validate_pitch_deck(deck)
    
    def test_validate_pitch_deck_placeholder_in_slide_fails(self):
        """Pitch deck with placeholder in slide content fails"""
        deck = PitchDeck(
            prospect_id=123,
            title="Marketing Strategy",
            subtitle="Subtitle",
            sections=[
                PitchSection(title="Problem", content="TBD - Add problem statement", slide_type="text", order=1)
            ],
            executive_summary="Summary",
            key_benefits=["Benefit"],
            target_duration_minutes=30
        )
        
        with pytest.raises(ValueError, match="contains placeholder text"):
            validate_pitch_deck(deck)


# Tests for BrandCore validation
class TestBrandCoreValidation:
    def test_validate_brand_core_valid(self):
        """Valid brand core passes validation"""
        brand = BrandCore(
            brand_name="TechCorp",
            purpose="To empower businesses through technology",
            vision="A world where technology serves humanity",
            mission="Deliver innovative solutions that drive business growth",
            values=["Innovation", "Integrity", "Customer-centricity"],
            personality_traits=["Professional", "Innovative"],
            voice_characteristics=["Confident", "Clear"]
        )
        
        result = validate_brand_core(brand)
        assert result == brand
    
    def test_validate_brand_core_empty_mission_fails(self):
        """Brand core with empty mission fails"""
        brand = BrandCore(
            brand_name="TechCorp",
            purpose="Purpose here",
            vision="Vision here",
            mission="",
            values=["Innovation"],
            personality_traits=["Professional"],
            voice_characteristics=["Confident"]
        )
        
        with pytest.raises(ValueError, match="mission cannot be empty"):
            validate_brand_core(brand)
    
    def test_validate_brand_core_placeholder_in_mission_fails(self):
        """Brand core with placeholder in mission fails"""
        brand = BrandCore(
            brand_name="TechCorp",
            purpose="Purpose here",
            vision="Vision here",
            mission="TBD - Mission to be defined",
            values=["Innovation"],
            personality_traits=["Professional"],
            voice_characteristics=["Confident"]
        )
        
        with pytest.raises(ValueError, match="contains placeholder text"):
            validate_brand_core(brand)
    
    def test_validate_brand_core_empty_values_fails(self):
        """Brand core with empty values list fails"""
        brand = BrandCore(
            brand_name="TechCorp",
            purpose="Purpose here",
            vision="Vision here",
            mission="Mission here",
            values=[],
            personality_traits=["Professional"],
            voice_characteristics=["Confident"]
        )
        
        with pytest.raises(ValueError, match="brand.values cannot be empty"):
            validate_brand_core(brand)
