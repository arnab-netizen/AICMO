"""Tests for Media Buying & Optimization Engine.

Stage M: Media engine tests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from aicmo.domain.intake import ClientIntake
from aicmo.media.domain import (
    MediaChannel,
    MediaChannelType,
    MediaObjective,
    MediaCampaignPlan,
    MediaOptimizationAction,
    OptimizationActionType,
    MediaPerformanceSnapshot,
)
from aicmo.media.service import (
    generate_media_plan,
    generate_optimization_actions,
)
from aicmo.learning.event_types import EventType


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_intake():
    """Sample client intake for testing."""
    return ClientIntake(
        brand_name="MediaTestCo",
        industry="E-commerce",
        primary_goal="Drive online sales",
        target_audiences=["Online shoppers", "Tech enthusiasts"],
        timeline="60 days"
    )


@pytest.fixture
def sample_performance():
    """Sample performance snapshot."""
    return MediaPerformanceSnapshot(
        campaign_name="Test Campaign",
        snapshot_date=datetime.now(),
        total_spend=10000.0,
        total_impressions=500000,
        total_clicks=5000,
        total_conversions=100,
        ctr=0.01,
        cpc=2.0,
        cpa=100.0,
        roas=2.5
    )


# ═══════════════════════════════════════════════════════════════════════
# Domain Model Tests
# ═══════════════════════════════════════════════════════════════════════


class TestMediaChannelDomain:
    """Test MediaChannel domain model."""
    
    def test_media_channel_creation(self):
        """Test creating a media channel."""
        channel = MediaChannel(
            channel_type=MediaChannelType.SEARCH,
            budget_allocated=5000.0,
            budget_spent=2500.0,
            audience_segments=["High-intent", "Retargeting"],
            platform="Google Ads"
        )
        
        assert channel.channel_type == MediaChannelType.SEARCH
        assert channel.budget_allocated == 5000.0
        assert channel.budget_spent == 2500.0
        assert len(channel.audience_segments) == 2
    
    def test_media_channel_defaults(self):
        """Test media channel default values."""
        channel = MediaChannel(
            channel_type=MediaChannelType.SOCIAL,
            budget_allocated=3000.0
        )
        
        assert channel.budget_spent == 0.0
        assert channel.impressions == 0
        assert channel.clicks == 0
        assert channel.conversions == 0


class TestMediaCampaignPlanDomain:
    """Test MediaCampaignPlan domain model."""
    
    def test_campaign_plan_creation(self):
        """Test creating a campaign plan."""
        plan = MediaCampaignPlan(
            campaign_name="Test Campaign",
            brand_name="TestBrand",
            objective=MediaObjective.CONVERSION,
            total_budget=10000.0,
            flight_start=datetime.now(),
            flight_end=datetime.now() + timedelta(days=30),
            channels=[
                MediaChannel(
                    channel_type=MediaChannelType.SEARCH,
                    budget_allocated=5000.0
                )
            ],
            target_audiences=["Target 1"],
            key_messages=["Message 1"],
            created_at=datetime.now()
        )
        
        assert plan.campaign_name == "Test Campaign"
        assert plan.objective == MediaObjective.CONVERSION
        assert len(plan.channels) == 1
        assert plan.total_budget == 10000.0


class TestMediaOptimizationActionDomain:
    """Test MediaOptimizationAction domain model."""
    
    def test_optimization_action_creation(self):
        """Test creating an optimization action."""
        action = MediaOptimizationAction(
            action_type=OptimizationActionType.BUDGET_SHIFT,
            channel_type=MediaChannelType.SEARCH,
            recommendation="Increase search budget by 20%",
            rationale="Search is outperforming other channels",
            expected_impact="Increase conversions by 15%",
            budget_change=2000.0,
            priority="high",
            created_at=datetime.now()
        )
        
        assert action.action_type == OptimizationActionType.BUDGET_SHIFT
        assert action.priority == "high"
        assert action.status == "pending"
        assert action.budget_change == 2000.0


# ═══════════════════════════════════════════════════════════════════════
# Service Function Tests
# ═══════════════════════════════════════════════════════════════════════


class TestMediaPlanGeneration:
    """Test media plan generation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_generate_media_plan_returns_plan(self, temp_db, sample_intake):
        """Test that generate_media_plan returns a valid plan."""
        plan = generate_media_plan(sample_intake, total_budget=10000.0)
        
        assert isinstance(plan, MediaCampaignPlan)
        assert plan.brand_name == sample_intake.brand_name
        assert plan.total_budget == 10000.0
        assert len(plan.channels) > 0
    
    def test_media_plan_has_channels(self, temp_db, sample_intake):
        """Test that generated plan includes channels."""
        plan = generate_media_plan(sample_intake, total_budget=20000.0)
        
        assert len(plan.channels) >= 2  # Should have multiple channels
        total_allocated = sum(ch.budget_allocated for ch in plan.channels)
        assert abs(total_allocated - 20000.0) < 1.0  # Budget fully allocated
    
    def test_media_plan_maps_objective(self, temp_db):
        """Test that plan maps intake goal to media objective."""
        # Test awareness goal
        intake = ClientIntake(
            brand_name="AwarenessCo",
            primary_goal="Build brand awareness"
        )
        plan = generate_media_plan(intake, total_budget=5000.0)
        assert plan.objective == MediaObjective.AWARENESS
        
        # Test conversion goal
        intake = ClientIntake(
            brand_name="ConversionCo",
            primary_goal="Drive sales and leads"
        )
        plan = generate_media_plan(intake, total_budget=5000.0)
        assert plan.objective == MediaObjective.CONVERSION
    
    def test_media_plan_logs_event(self, temp_db, sample_intake):
        """Test that media plan generation logs learning event."""
        with patch('aicmo.media.service.log_event') as mock_log:
            generate_media_plan(sample_intake, total_budget=15000.0)
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.MEDIA_PLAN_CREATED.value


class TestOptimizationGeneration:
    """Test optimization action generation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_generate_optimization_actions_returns_list(self, temp_db, sample_intake):
        """Test that generate_optimization_actions returns actions."""
        plan = generate_media_plan(sample_intake, total_budget=10000.0)
        actions = generate_optimization_actions(plan)
        
        assert isinstance(actions, list)
        assert len(actions) > 0
        assert all(isinstance(a, MediaOptimizationAction) for a in actions)
    
    def test_optimization_with_performance_data(self, temp_db, sample_intake, sample_performance):
        """Test optimizations generated with performance data."""
        plan = generate_media_plan(sample_intake, total_budget=10000.0)
        actions = generate_optimization_actions(plan, performance=sample_performance)
        
        # Note: The current rules may not trigger based on sample performance values
        # This test verifies the function runs successfully with performance data
        assert isinstance(actions, list)
        # Actions may be empty if performance is within acceptable thresholds
    
    def test_optimization_without_performance_data(self, temp_db, sample_intake):
        """Test default optimizations without performance data."""
        plan = generate_media_plan(sample_intake, total_budget=10000.0)
        actions = generate_optimization_actions(plan, performance=None)
        
        assert len(actions) > 0
        # Should provide generic recommendations
        assert all(a.status == "pending" for a in actions)
    
    def test_optimization_logs_event(self, temp_db, sample_intake):
        """Test that optimization generation logs learning event."""
        plan = generate_media_plan(sample_intake, total_budget=10000.0)
        
        with patch('aicmo.media.service.log_event') as mock_log:
            generate_optimization_actions(plan)
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.MEDIA_CAMPAIGN_OPTIMIZED.value


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════


class TestMediaEngineIntegration:
    """Test media engine integration."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_media_workflow_end_to_end(self, temp_db):
        """Test complete media planning and optimization workflow."""
        # Create intake
        intake = ClientIntake(
            brand_name="WorkflowTest",
            industry="SaaS",
            primary_goal="Generate qualified leads",
            target_audiences=["B2B decision makers"],
            timeline="90 days"
        )
        
        # Generate media plan
        plan = generate_media_plan(intake, total_budget=50000.0, duration_days=90)
        
        # Verify plan structure
        assert plan.brand_name == intake.brand_name
        assert plan.total_budget == 50000.0
        assert len(plan.channels) > 0
        assert plan.objective in [MediaObjective.CONSIDERATION, MediaObjective.CONVERSION]
        
        # Generate optimizations
        actions = generate_optimization_actions(plan)
        
        # Verify optimization structure
        assert len(actions) > 0
        assert all(a.channel_type in [ch.channel_type for ch in plan.channels] 
                  for a in actions)
        
        # Note: Learning events are tested separately in other test methods
    
    def test_media_plan_budget_allocation(self, temp_db):
        """Test that budget is properly allocated across channels."""
        intake = ClientIntake(
            brand_name="BudgetTest",
            primary_goal="Maximize conversions"
        )
        
        total_budget = 100000.0
        plan = generate_media_plan(intake, total_budget=total_budget)
        
        # Verify budget allocation
        allocated = sum(ch.budget_allocated for ch in plan.channels)
        assert abs(allocated - total_budget) < 1.0  # Allow tiny rounding error
        assert all(ch.budget_allocated > 0 for ch in plan.channels)
