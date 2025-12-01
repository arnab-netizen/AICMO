"""
Tests for Phase 1 quality upgrade modules.

Tests creative territories, visual concepts, and genericity scoring.
"""

from backend.creative_territories import (
    CreativeTerritory,
    get_creative_territories_for_brief,
)
from backend.genericity_scoring import (
    build_anti_generic_instruction,
    count_generic_phrases,
    genericity_score,
    is_too_generic,
    repetition_score,
)
from backend.visual_concepts import VisualConcept, generate_visual_concept


class TestCreativeTerritories:
    """Test creative territories engine."""

    def test_starbucks_territories(self):
        """Test that Starbucks gets brand-specific territories."""
        brief = {
            "brand_name": "Starbucks",
            "industry": "Coffeehouse / Beverage Retail",
            "geography": "Global",
        }
        territories = get_creative_territories_for_brief(brief)

        assert len(territories) > 0
        assert any(t.id == "rituals_and_moments" for t in territories)
        assert any(t.id == "behind_the_bar" for t in territories)
        assert any(t.id == "seasonal_magic" for t in territories)

    def test_coffee_industry_territories(self):
        """Test that coffee industry gets relevant territories."""
        brief = {
            "brand_name": "Local Coffee Shop",
            "industry": "Cafe / Coffee",
            "geography": "Local",
        }
        territories = get_creative_territories_for_brief(brief)

        assert len(territories) > 0
        # Should get generic food/beverage territories
        territory_ids = [t.id for t in territories]
        assert "product_focus" in territory_ids or "process_and_craft" in territory_ids

    def test_generic_fallback_territories(self):
        """Test that unknown brands get generic territories."""
        brief = {
            "brand_name": "Unknown Brand",
            "industry": "Technology",
            "geography": "Global",
        }
        territories = get_creative_territories_for_brief(brief)

        assert len(territories) > 0
        territory_ids = [t.id for t in territories]
        assert "brand_story" in territory_ids or "customer_moments" in territory_ids

    def test_defensive_brief_handling(self):
        """Test that missing keys don't break the function."""
        brief = {}
        territories = get_creative_territories_for_brief(brief)
        assert len(territories) > 0  # Should return fallback

    def test_creative_territory_structure(self):
        """Test that CreativeTerritory has required fields."""
        territory = CreativeTerritory(
            id="test_id",
            label="Test Label",
            summary="Test summary",
            example_angles=["angle 1", "angle 2"],
        )
        assert territory.id == "test_id"
        assert territory.label == "Test Label"
        assert len(territory.example_angles) == 2


class TestVisualConcepts:
    """Test visual concept generator."""

    def test_generate_visual_concept_basic(self):
        """Test basic visual concept generation."""
        concept = generate_visual_concept(
            platform="Instagram",
            theme="morning routine",
            creative_territory_id="rituals_and_moments",
            brand_name="Starbucks",
            industry="Coffeehouse",
        )

        assert concept.shot_type
        assert concept.setting
        assert len(concept.subjects) > 0
        assert concept.mood
        assert concept.aspect_ratio

    def test_starbucks_rituals_concept(self):
        """Test Starbucks-specific ritual territory concept."""
        concept = generate_visual_concept(
            platform="Instagram",
            theme="morning coffee",
            creative_territory_id="rituals_and_moments",
            brand_name="Starbucks",
            industry="Coffeehouse",
        )

        assert "close-up" in concept.shot_type.lower()
        assert "cafe" in concept.setting.lower() or "coffee" in concept.setting.lower()

    def test_platform_aspect_ratios(self):
        """Test that different platforms get appropriate aspect ratios."""
        reel_concept = generate_visual_concept(
            platform="Instagram_reel",
            theme="test",
            creative_territory_id="product_focus",
            brand_name="Test Brand",
            industry="Food",
        )
        assert "9:16" in reel_concept.aspect_ratio

        feed_concept = generate_visual_concept(
            platform="Instagram_post",
            theme="test",
            creative_territory_id="product_focus",
            brand_name="Test Brand",
            industry="Food",
        )
        assert "1:1" in feed_concept.aspect_ratio or "4:5" in feed_concept.aspect_ratio

    def test_visual_concept_to_prompt_snippet(self):
        """Test conversion to prompt snippet."""
        concept = VisualConcept(
            shot_type="medium shot",
            setting="indoors",
            subjects=["product", "hands"],
            mood="warm",
            color_palette="earth tones",
            motion="steady",
            on_screen_text="Test text",
            aspect_ratio="1:1",
            platform_notes="Test notes",
        )

        snippet = concept.to_prompt_snippet()
        assert "medium shot" in snippet
        assert "product, hands" in snippet
        assert "warm" in snippet

    def test_visual_concept_to_dict(self):
        """Test conversion to dictionary."""
        concept = VisualConcept(
            shot_type="test",
            setting="test",
            subjects=["test"],
            mood="test",
            color_palette="test",
            motion="test",
            on_screen_text="test",
            aspect_ratio="test",
            platform_notes="test",
        )

        d = concept.to_dict()
        assert isinstance(d, dict)
        assert d["shot_type"] == "test"
        assert d["subjects"] == ["test"]


class TestGenericityScoring:
    """Test genericity scoring system."""

    def test_count_generic_phrases(self):
        """Test counting generic marketing phrases."""
        generic_text = "Don't miss this limited time offer with proven methodologies!"
        count = count_generic_phrases(generic_text)
        assert count >= 3  # Should find at least 3 generic phrases

    def test_count_generic_phrases_clean_text(self):
        """Test that clean text has no generic phrases."""
        clean_text = "Our artisan coffee is roasted fresh every morning."
        count = count_generic_phrases(clean_text)
        assert count == 0

    def test_repetition_score(self):
        """Test repetition detection."""
        repetitive = "test test test hello hello hello world world world"
        score = repetition_score(repetitive)
        assert score > 0.5  # High repetition

        unique = "the quick brown fox jumps over lazy dog"
        score_unique = repetition_score(unique)
        assert score_unique < 0.3  # Low repetition

    def test_genericity_score_high(self):
        """Test that generic text gets high score."""
        generic = (
            "Don't miss our limited time offer! We deliver tangible results with "
            "proven methodologies that drive results and measurable impact."
        )
        score = genericity_score(generic)
        assert score > 0.5

    def test_genericity_score_low(self):
        """Test that specific text gets low score."""
        specific = (
            "First sip of morning latte while rain taps against cafe window. "
            "Steam rises from ceramic mug, barista crafts next order behind mahogany counter."
        )
        score = genericity_score(specific)
        assert score < 0.3

    def test_is_too_generic(self):
        """Test the threshold-based generic detector."""
        generic = "Don't miss this limited time offer with proven methodologies!"
        assert is_too_generic(generic) is True

        specific = "Hand-pulled espresso shot brewed at exactly 92 degrees celsius."
        assert is_too_generic(specific) is False

    def test_build_anti_generic_instruction(self):
        """Test building anti-generic instructions."""
        instruction = build_anti_generic_instruction()
        assert "generic" in instruction.lower()
        assert "rewrite" in instruction.lower()

    def test_build_anti_generic_instruction_with_extras(self):
        """Test building instructions with extra requirements."""
        instruction = build_anti_generic_instruction(
            [
                "Keep the same table structure.",
                "Maintain brand voice.",
            ]
        )
        assert "table structure" in instruction
        assert "brand voice" in instruction
        assert "generic" in instruction.lower()

    def test_genericity_score_empty_text(self):
        """Test that empty text returns 0 score."""
        assert genericity_score("") == 0.0
        assert genericity_score("   ") == 0.0

    def test_is_too_generic_custom_threshold(self):
        """Test custom threshold for genericity detection."""
        text = "Some moderately generic marketing language here."
        # With high threshold, should not be too generic
        assert is_too_generic(text, threshold=0.8) is False
        # With low threshold, might be too generic
        # (actual result depends on the text, just testing the threshold works)
        result = is_too_generic(text, threshold=0.1)
        assert isinstance(result, bool)
