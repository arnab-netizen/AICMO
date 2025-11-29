"""Test persona card generation and field validation."""
import pytest
from backend.industry_config import (
    IndustryPersonaConfig,
    convert_industry_persona_to_persona_card,
)
from aicmo.io.client_reports import PersonaCard


def test_convert_industry_persona_to_persona_card():
    """Test that IndustryPersonaConfig converts to valid PersonaCard."""
    industry_persona: IndustryPersonaConfig = {
        "name": "Instagram-Savvy Foodie",
        "role": "Content Creator / Influencer",
        "age_range": "18-35",
        "primary_pain_points": [
            "Finding Instagrammable food experiences",
            "Staying on top of trends",
        ],
        "primary_goals": [
            "Discover new places to eat",
            "Build personal brand",
        ],
        "decision_factors": [
            "Visual appeal",
            "Trending/unique concept",
        ],
        "channel_preference": "Instagram",
    }

    # Convert to PersonaCard
    persona_card = convert_industry_persona_to_persona_card(industry_persona)

    # Verify all required fields are present
    assert isinstance(persona_card, PersonaCard)
    assert persona_card.name == "Instagram-Savvy Foodie"
    assert persona_card.demographics is not None
    assert persona_card.demographics != ""
    assert persona_card.psychographics is not None
    assert persona_card.psychographics != ""
    assert persona_card.pain_points == [
        "Finding Instagrammable food experiences",
        "Staying on top of trends",
    ]
    assert persona_card.primary_platforms == ["Instagram"]
    assert persona_card.tone_preference == "Professional"


def test_persona_card_has_all_required_fields():
    """Test that PersonaCard model validates all required fields."""
    persona = PersonaCard(
        name="Test Persona",
        demographics="Professional, 35-45",
        psychographics="Values efficiency and results",
        pain_points=["Problem 1"],
        triggers=["Trigger 1"],
        objections=["Objection 1"],
        content_preferences=["Case studies"],
        primary_platforms=["LinkedIn"],
        tone_preference="Professional",
    )

    # Should not raise validation error
    assert persona.name == "Test Persona"
    assert persona.demographics == "Professional, 35-45"
    assert persona.psychographics == "Values efficiency and results"


def test_persona_card_validation_fails_without_demographics():
    """Test that PersonaCard requires demographics field."""
    with pytest.raises(Exception):  # Should raise validation error
        PersonaCard(
            name="Test",
            # Missing demographics
            psychographics="Values results",
            pain_points=[],
            triggers=[],
            objections=[],
            content_preferences=[],
            primary_platforms=[],
            tone_preference="Professional",
        )


def test_persona_card_validation_fails_without_psychographics():
    """Test that PersonaCard requires psychographics field."""
    with pytest.raises(Exception):  # Should raise validation error
        PersonaCard(
            name="Test",
            demographics="Professional",
            # Missing psychographics
            pain_points=[],
            triggers=[],
            objections=[],
            content_preferences=[],
            primary_platforms=[],
            tone_preference="Professional",
        )
