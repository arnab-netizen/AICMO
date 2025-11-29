"""
Regression test for PersonaCard validation tolerance.

Ensures that AICMOOutputReport can handle partial persona data
without throwing ValidationError. This prevents 500s when LLM returns
incomplete persona_cards.

Fixes: FIX #8 – Make persona fields tolerant (no more 500s)
"""
import pytest
from aicmo.io.client_reports import AICMOOutputReport, PersonaCard


def test_persona_card_allows_missing_fields():
    """PersonaCard should have safe defaults for optional fields."""
    # Test that we can create a PersonaCard with only the required 'name' field
    persona = PersonaCard(name="Test Persona")
    
    assert persona.name == "Test Persona"
    assert persona.demographics == ""
    assert persona.psychographics == ""
    assert persona.tone_preference == ""
    assert persona.pain_points == []
    assert persona.triggers == []
    assert persona.objections == []
    assert persona.content_preferences == []
    assert persona.primary_platforms == []


def test_output_report_allows_partial_persona_cards():
    """AICMOOutputReport should accept persona_cards with missing fields."""
    data = {
        "marketing_plan": {
            "executive_summary": "Test summary",
            "situation_analysis": "Test analysis",
            "strategy": "Test strategy",
        },
        "campaign_blueprint": {
            "big_idea": "Test idea",
            "objective": {"primary": "Test objective"},
            "audience_persona": {
                "name": "Test Audience",
                "description": "Test description",
            },
        },
        "social_calendar": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "posts": [],
        },
        # persona_cards is present but missing demographics, goals, etc.
        "persona_cards": [
            {
                "name": "Remote Worker Rachel",
                "summary": "Remote worker who visits coffee shops weekdays.",
                # deliberately missing demographics/psychographics/tone_preference...
            }
        ],
    }

    # This should NOT raise ValidationError
    report = AICMOOutputReport(**data)
    assert len(report.persona_cards) == 1
    
    persona = report.persona_cards[0]
    assert persona.name == "Remote Worker Rachel"
    # These should exist and be defaulted, not raise ValidationError
    assert persona.demographics == ""
    assert persona.psychographics == ""
    assert persona.tone_preference == ""
    assert persona.pain_points == []


def test_output_report_partial_personas_with_some_fields():
    """AICMOOutputReport should preserve present fields and default missing ones."""
    data = {
        "marketing_plan": {
            "executive_summary": "Test",
            "situation_analysis": "Test",
            "strategy": "Test",
        },
        "campaign_blueprint": {
            "big_idea": "Test",
            "objective": {"primary": "Test"},
            "audience_persona": {"name": "Test", "description": "Test"},
        },
        "social_calendar": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "posts": [],
        },
        "persona_cards": [
            {
                "name": "Decision Maker David",
                "demographics": "45-55, C-suite executive",
                "pain_points": ["Legacy systems slowing innovation"],
                # Missing: psychographics, tone_preference, triggers, etc.
            }
        ],
    }

    report = AICMOOutputReport(**data)
    persona = report.persona_cards[0]
    
    # Preserved fields
    assert persona.name == "Decision Maker David"
    assert persona.demographics == "45-55, C-suite executive"
    assert persona.pain_points == ["Legacy systems slowing innovation"]
    
    # Defaulted fields
    assert persona.psychographics == ""
    assert persona.tone_preference == ""
    assert persona.triggers == []
    assert persona.objections == []


def test_output_report_empty_persona_cards_list():
    """AICMOOutputReport should accept empty persona_cards list."""
    data = {
        "marketing_plan": {
            "executive_summary": "Test",
            "situation_analysis": "Test",
            "strategy": "Test",
        },
        "campaign_blueprint": {
            "big_idea": "Test",
            "objective": {"primary": "Test"},
            "audience_persona": {"name": "Test", "description": "Test"},
        },
        "social_calendar": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "posts": [],
        },
        "persona_cards": [],
    }

    report = AICMOOutputReport(**data)
    assert report.persona_cards == []


def test_output_report_persona_cards_omitted():
    """AICMOOutputReport should default persona_cards to empty list if omitted."""
    data = {
        "marketing_plan": {
            "executive_summary": "Test",
            "situation_analysis": "Test",
            "strategy": "Test",
        },
        "campaign_blueprint": {
            "big_idea": "Test",
            "objective": {"primary": "Test"},
            "audience_persona": {"name": "Test", "description": "Test"},
        },
        "social_calendar": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "posts": [],
        },
        # persona_cards field completely omitted
    }

    report = AICMOOutputReport(**data)
    assert report.persona_cards == []


def test_persona_card_serialization_with_defaults():
    """PersonaCard with defaults should serialize cleanly."""
    persona = PersonaCard(
        name="Basic Persona",
        demographics="25-35, urban professional",
    )
    
    serialized = persona.model_dump()
    assert serialized["name"] == "Basic Persona"
    assert serialized["demographics"] == "25-35, urban professional"
    assert serialized["psychographics"] == ""
    assert serialized["tone_preference"] == ""
    assert serialized["pain_points"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-W", "ignore::DeprecationWarning"])
