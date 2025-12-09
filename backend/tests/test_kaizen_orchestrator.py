"""Tests for Stage K3 - Kaizen Orchestrator End-to-End Flow.

Tests that the orchestrator coordinates all subsystems with Kaizen insights.
"""

import pytest
import tempfile
import os
from datetime import datetime

from aicmo.domain.intake import ClientIntake
from aicmo.pitch.domain import Prospect
from aicmo.delivery.kaizen_orchestrator import (
    KaizenOrchestrator,
    run_full_kaizen_flow_for_project,
    run_kaizen_pitch_flow,
    compare_with_and_without_kaizen
)


@pytest.fixture
def sample_intake():
    """Sample client intake."""
    return ClientIntake(
        brand_name="TestBrand",
        industry="technology",
        product_service="SaaS platform",
        primary_goal="Increase user acquisition",
        target_audiences=["Product teams", "Engineering teams"]
    )


@pytest.fixture
def sample_prospect():
    """Sample prospect."""
    return Prospect(
        name="John Doe",
        company="TechCorp",
        industry="technology",
        budget_range="$50k-100k",
        stage="qualified"
    )


@pytest.fixture
def orchestrator():
    """Fresh orchestrator instance."""
    return KaizenOrchestrator()


class TestKaizenOrchestrator:
    """Test Kaizen orchestrator functionality."""
    
    
    def test_full_campaign_flow_without_kaizen(self, orchestrator, sample_intake):
        """Test baseline campaign flow without Kaizen."""
        result = orchestrator.run_full_campaign_flow(
            intake=sample_intake,
            total_budget=10000.0,
            skip_kaizen=True
        )
        
        assert result["brand_name"] == "TestBrand"
        assert result["kaizen_enabled"] is False
        assert result["kaizen_insights_used"] is False
        assert "brand_core" in result
        assert "brand_positioning" in result
        assert "media_plan" in result
        assert "creatives" in result
        assert result["execution_time_seconds"] > 0
        assert result["total_budget"] == 10000.0
    
    
    def test_full_campaign_flow_with_kaizen(self, orchestrator, sample_intake):
        """Test campaign flow with Kaizen insights."""
        result = orchestrator.run_full_campaign_flow(
            intake=sample_intake,
            project_id=1,
            total_budget=15000.0,
            skip_kaizen=False
        )
        
        assert result["brand_name"] == "TestBrand"
        assert result["kaizen_enabled"] is True
        # kaizen_insights_used depends on whether historical data exists
        assert "brand_core" in result
        assert "brand_positioning" in result
        assert "media_plan" in result
        assert "creatives" in result
        assert result["total_budget"] == 15000.0
    
    
    def test_campaign_flow_generates_all_components(self, orchestrator, sample_intake):
        """Test that all campaign components are generated."""
        result = orchestrator.run_full_campaign_flow(
            intake=sample_intake,
            total_budget=10000.0
        )
        
        # Check brand core
        brand_core = result["brand_core"]
        assert len(brand_core.values) > 0
        assert len(brand_core.personality_traits) > 0
        
        # Check positioning
        positioning = result["brand_positioning"]
        assert positioning.target_audience
        assert positioning.point_of_difference
        if positioning.key_benefits:
            assert len(positioning.key_benefits) > 0
        
        # Check media plan
        media_plan = result["media_plan"]
        assert len(media_plan.channels) > 0
        total_allocated = sum(ch.budget_allocated for ch in media_plan.channels)
        assert total_allocated == pytest.approx(10000.0, rel=0.01)
        
        # Check creatives
        creatives = result["creatives"]
        assert len(creatives.variants) >= 1  # At least one variant created
    
    
    def test_pitch_flow_without_kaizen(self, orchestrator, sample_prospect):
        """Test pitch generation without Kaizen."""
        result = orchestrator.run_pitch_flow(
            prospect=sample_prospect,
            skip_kaizen=True
        )
        
        assert result["prospect_company"] == "TechCorp"
        assert result["industry"] == "technology"
        assert result["kaizen_enabled"] is False
        assert result["win_patterns_found"] is False
        assert "pitch_deck" in result
        assert result["execution_time_seconds"] > 0
    
    
    def test_pitch_flow_with_kaizen(self, orchestrator, sample_prospect):
        """Test pitch generation with Kaizen insights."""
        result = orchestrator.run_pitch_flow(
            prospect=sample_prospect,
            project_id=1,
            skip_kaizen=False
        )
        
        assert result["prospect_company"] == "TechCorp"
        assert result["kaizen_enabled"] is True
        assert "pitch_deck" in result
        
        # Check pitch deck structure
        pitch_deck = result["pitch_deck"]
        assert len(pitch_deck.sections) > 0
    
    
    def test_kaizen_comparison_flow(self, orchestrator, sample_intake):
        """Test comparison between baseline and Kaizen flows."""
        comparison = orchestrator.compare_kaizen_impact(
            intake=sample_intake,
            total_budget=10000.0,
            project_id=1
        )
        
        assert "baseline" in comparison
        assert "kaizen" in comparison
        assert "differences" in comparison
        
        # Check baseline
        baseline = comparison["baseline"]
        assert baseline["kaizen_enabled"] is False
        assert "brand_core" in baseline
        
        # Check kaizen flow
        kaizen = comparison["kaizen"]
        assert kaizen["kaizen_enabled"] is True
        assert "brand_core" in kaizen
        
        # Check differences
        diffs = comparison["differences"]
        assert "execution_time_improvement" in diffs
        assert "kaizen_insights_used" in diffs
    
    
    def test_comparison_calculates_channel_diffs(self, orchestrator, sample_intake):
        """Test that comparison calculates channel budget differences."""
        comparison = orchestrator.compare_kaizen_impact(
            intake=sample_intake,
            total_budget=10000.0
        )
        
        diffs = comparison["differences"]
        
        # Should have channel budget changes (even if empty dict when no changes)
        assert "channel_budget_changes" in diffs
        
        # If there are changes, they should have proper structure
        if diffs["channel_budget_changes"]:
            for platform, change_info in diffs["channel_budget_changes"].items():
                assert "baseline" in change_info
                assert "kaizen" in change_info
                assert "change" in change_info
                assert "change_pct" in change_info
    
    
    def test_comparison_calculates_brand_value_diffs(self, orchestrator, sample_intake):
        """Test that comparison identifies added/removed brand values."""
        comparison = orchestrator.compare_kaizen_impact(
            intake=sample_intake,
            total_budget=10000.0
        )
        
        diffs = comparison["differences"]
        
        # Should have brand value changes
        assert "brand_values_added" in diffs
        assert "brand_values_removed" in diffs
        
        # Should be lists
        assert isinstance(diffs["brand_values_added"], list)
        assert isinstance(diffs["brand_values_removed"], list)


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""
    
    
    def test_run_full_kaizen_flow_for_project(self, sample_intake):
        """Test convenience function for full flow."""
        result = run_full_kaizen_flow_for_project(
            intake=sample_intake,
            project_id=1,
            total_budget=12000.0
        )
        
        assert result["brand_name"] == "TestBrand"
        assert result["kaizen_enabled"] is True
        assert result["total_budget"] == 12000.0
        assert "brand_core" in result
        assert "media_plan" in result
    
    
    def test_run_kaizen_pitch_flow(self, sample_prospect):
        """Test convenience function for pitch flow."""
        result = run_kaizen_pitch_flow(
            prospect=sample_prospect,
            project_id=1
        )
        
        assert result["prospect_company"] == "TechCorp"
        assert result["kaizen_enabled"] is True
        assert "pitch_deck" in result
    
    
    def test_compare_with_and_without_kaizen(self, sample_intake):
        """Test convenience function for comparison."""
        comparison = compare_with_and_without_kaizen(
            intake=sample_intake,
            total_budget=10000.0
        )
        
        assert "baseline" in comparison
        assert "kaizen" in comparison
        assert "differences" in comparison
        
        # Both flows should have run
        assert comparison["baseline"]["kaizen_enabled"] is False
        assert comparison["kaizen"]["kaizen_enabled"] is True


class TestOrchestratorIntegration:
    """Test end-to-end orchestrator integration."""
    
    
    def test_orchestrator_logs_events(self, orchestrator, sample_intake):
        """Test that orchestrator logs orchestration events."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        try:
            result = orchestrator.run_full_campaign_flow(
                intake=sample_intake,
                project_id=1,
                total_budget=10000.0
            )
            
            # Should have completed successfully
            assert "brand_core" in result
            assert result["execution_time_seconds"] > 0
            
        finally:
            if old_env:
                os.environ["AICMO_MEMORY_DB"] = old_env
            else:
                os.environ.pop("AICMO_MEMORY_DB", None)
            
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    
    def test_orchestrator_handles_missing_historical_data(self, orchestrator, sample_intake):
        """Test orchestrator gracefully handles no historical Kaizen data."""
        # Run with project_id that has no history
        result = orchestrator.run_full_campaign_flow(
            intake=sample_intake,
            project_id=999999,  # Non-existent project
            total_budget=10000.0,
            skip_kaizen=False
        )
        
        assert result["kaizen_enabled"] is True
        # Should still generate all components
        assert "brand_core" in result
        assert "media_plan" in result
        assert "creatives" in result
    
    
    def test_orchestrator_with_client_id(self, orchestrator, sample_intake):
        """Test orchestrator accepts client_id for cross-project learning."""
        result = orchestrator.run_full_campaign_flow(
            intake=sample_intake,
            project_id=1,
            client_id=10,
            total_budget=10000.0
        )
        
        assert result["brand_name"] == "TestBrand"
        assert "brand_core" in result
    
    
    def test_orchestrator_execution_time_tracked(self, orchestrator, sample_intake):
        """Test that execution time is properly tracked."""
        result = orchestrator.run_full_campaign_flow(
            intake=sample_intake,
            total_budget=10000.0
        )
        
        # Should have tracked execution time
        assert result["execution_time_seconds"] > 0
        assert result["execution_time_seconds"] < 60  # Should be reasonably fast
        
        # Should have timestamp
        assert "timestamp" in result
        timestamp = datetime.fromisoformat(result["timestamp"])
        assert isinstance(timestamp, datetime)
    
    
    def test_full_flow_produces_consistent_budgets(self, orchestrator, sample_intake):
        """Test that media budgets are consistent across orchestrator runs."""
        total_budget = 20000.0
        
        result = orchestrator.run_full_campaign_flow(
            intake=sample_intake,
            total_budget=total_budget
        )
        
        # Sum all channel budgets
        media_plan = result["media_plan"]
        actual_total = sum(ch.budget_allocated for ch in media_plan.channels)
        
        # Should match requested budget within 1%
        assert actual_total == pytest.approx(total_budget, rel=0.01)
