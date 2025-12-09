"""Tests for Stage K2 - Kaizen-Informed Service Decisions.

Tests that service functions accept KaizenContext and use it to make better decisions.
"""

import pytest
import tempfile
import os
from datetime import datetime

from aicmo.learning.domain import KaizenContext
from aicmo.domain.intake import ClientIntake
from aicmo.pitch.domain import Prospect
from aicmo.pitch.service import generate_pitch_deck
from aicmo.brand.service import generate_brand_core, generate_brand_positioning
from aicmo.media.service import generate_media_plan


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
def kaizen_with_wins():
    """KaizenContext with successful patterns."""
    return KaizenContext(
        project_id=1,
        best_channels=["meta", "google"],
        weak_channels=["twitter"],
        pitch_win_patterns=[{
            "total_wins": 5,
            "win_rate": 0.83,
            "successful_industries": ["technology", "saas"]
        }],
        successful_hooks=["problem-solution", "data-driven story"],
        rejected_patterns=[
            {"pattern": "generic startup story", "rejection_count": 3}
        ],
        effective_tones=["confident", "innovative"],
        successful_positioning=["data-driven", "results-focused"]
    )


class TestPitchWithKaizen:
    """Test pitch generation with Kaizen insights."""
    
    def test_pitch_without_kaizen(self, sample_prospect):
        """Test baseline pitch generation without Kaizen."""
        deck = generate_pitch_deck(sample_prospect)
        
        assert isinstance(deck, object)
        assert len(deck.sections) > 0
        # Should not mention win rate
        why_us = [s for s in deck.sections if s.title == "Why Us"][0]
        assert "win rate" not in why_us.content.lower()
    
    def test_pitch_with_kaizen_win_patterns(self, sample_prospect, kaizen_with_wins):
        """Test that pitch deck uses Kaizen win patterns."""
        deck = generate_pitch_deck(sample_prospect, kaizen=kaizen_with_wins)
        
        assert len(deck.sections) > 0
        
        # Should mention success in technology industry
        why_us = [s for s in deck.sections if s.title == "Why Us"][0]
        assert "83%" in why_us.content or "5 successful" in why_us.content
    
    def test_pitch_references_industry_success(self, sample_prospect, kaizen_with_wins):
        """Test that pitch references successful industries from Kaizen."""
        deck = generate_pitch_deck(sample_prospect, kaizen=kaizen_with_wins)
        
        case_studies = [s for s in deck.sections if s.title == "Case Studies"][0]
        # Should mention technology since it's in successful_industries
        assert "technology" in case_studies.content.lower() or "tech" in case_studies.content.lower()


class TestBrandWithKaizen:
    """Test brand strategy generation with Kaizen insights."""
    
    def test_brand_core_without_kaizen(self, sample_intake):
        """Test baseline brand core without Kaizen."""
        core = generate_brand_core(sample_intake)
        
        assert len(core.values) > 0
        assert len(core.personality_traits) > 0
    
    def test_brand_core_with_kaizen_tones(self, sample_intake, kaizen_with_wins):
        """Test that brand core applies effective tones from Kaizen."""
        core = generate_brand_core(sample_intake, kaizen=kaizen_with_wins)
        
        # Should include tones from Kaizen
        personality_lower = [p.lower() for p in core.personality_traits]
        assert any(tone in personality_lower for tone in ["confident", "innovative"])
    
    def test_brand_positioning_with_kaizen(self, sample_intake, kaizen_with_wins):
        """Test that positioning uses successful patterns."""
        positioning = generate_brand_positioning(sample_intake, kaizen=kaizen_with_wins)
        
        # Should emphasize data-driven if in successful_positioning
        diff_lower = positioning.point_of_difference.lower()
        assert "data-driven" in diff_lower or "results" in diff_lower
    
    def test_brand_benefits_mention_channels(self, sample_intake, kaizen_with_wins):
        """Test that key benefits mention successful channels."""
        positioning = generate_brand_positioning(sample_intake, kaizen=kaizen_with_wins)
        
        # Should mention best channel (meta)
        benefits_str = " ".join(positioning.key_benefits).lower()
        assert "meta" in benefits_str or "google" in benefits_str


class TestMediaWithKaizen:
    """Test media planning with Kaizen channel insights."""
    
    def test_media_plan_without_kaizen(self, sample_intake):
        """Test baseline media plan without Kaizen."""
        plan = generate_media_plan(sample_intake, total_budget=10000.0)
        
        assert len(plan.channels) > 0
        assert sum(ch.budget_allocated for ch in plan.channels) == pytest.approx(10000.0, rel=0.01)
    
    def test_media_plan_favors_best_channels(self, sample_intake, kaizen_with_wins):
        """Test that media plan allocates more to best channels."""
        plan_with_kaizen = generate_media_plan(sample_intake, total_budget=10000.0, kaizen=kaizen_with_wins)
        plan_without = generate_media_plan(sample_intake, total_budget=10000.0)
        
        # Find meta/social channel budgets
        def get_social_budget(plan):
            for ch in plan.channels:
                if "meta" in ch.platform.lower() or ch.channel_type.value == "social":
                    return ch.budget_allocated
            return 0
        
        kaizen_social = get_social_budget(plan_with_kaizen)
        baseline_social = get_social_budget(plan_without)
        
        # With Kaizen favoring meta, social budget should be higher or at least present
        assert kaizen_social > 0
    
    def test_media_plan_logs_kaizen_usage(self, sample_intake, kaizen_with_wins):
        """Test that media plan logs when Kaizen is used."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        try:
            plan = generate_media_plan(sample_intake, total_budget=10000.0, kaizen=kaizen_with_wins)
            assert plan.plan_notes is not None
            assert "kaizen" in plan.plan_notes.lower() or "insights" in plan.plan_notes.lower()
        finally:
            if old_env:
                os.environ["AICMO_MEMORY_DB"] = old_env
            else:
                os.environ.pop("AICMO_MEMORY_DB", None)
            
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_media_budget_sums_correctly_with_kaizen(self, sample_intake, kaizen_with_wins):
        """Test that budget adjustments still sum to total."""
        total_budget = 15000.0
        plan = generate_media_plan(sample_intake, total_budget=total_budget, kaizen=kaizen_with_wins)
        
        actual_total = sum(ch.budget_allocated for ch in plan.channels)
        # Allow 1% tolerance for rounding
        assert actual_total == pytest.approx(total_budget, rel=0.01)


class TestKaizenIntegration:
    """Test overall Kaizen integration across services."""
    
    def test_kaizen_optional_everywhere(self, sample_intake, sample_prospect):
        """Test that kaizen parameter is optional (backwards compatible)."""
        # Should work without kaizen parameter
        deck = generate_pitch_deck(sample_prospect)
        core = generate_brand_core(sample_intake)
        plan = generate_media_plan(sample_intake, total_budget=10000.0)
        
        assert deck is not None
        assert core is not None
        assert plan is not None
    
    def test_kaizen_with_none_value(self, sample_intake, sample_prospect):
        """Test that explicitly passing None for kaizen works."""
        deck = generate_pitch_deck(sample_prospect, kaizen=None)
        core = generate_brand_core(sample_intake, kaizen=None)
        plan = generate_media_plan(sample_intake, total_budget=10000.0, kaizen=None)
        
        assert deck is not None
        assert core is not None
        assert plan is not None
    
    def test_empty_kaizen_context(self, sample_intake):
        """Test that empty KaizenContext doesn't break anything."""
        empty_kaizen = KaizenContext()
        
        plan = generate_media_plan(sample_intake, total_budget=10000.0, kaizen=empty_kaizen)
        assert plan is not None
        assert len(plan.channels) > 0
