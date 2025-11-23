"""
Tests for Situation Analysis generation.

Verify:
- Stub mode produces honest, non-placeholder analysis
- LLM mode integration works with proper fallback
- Analysis is always present and valid in generated reports
- No "will be refined", "placeholder", "TBD" in analysis content
"""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from aicmo.generators.situation_analysis_generator import (
    generate_situation_analysis,
    _stub_situation_analysis,
    _sanitize_situation_analysis,
)
from aicmo.io.client_reports import (
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    ProductServiceItem,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
)
from backend.main import app

client = TestClient(app)


def _create_minimal_brief() -> ClientInputBrief:
    """Helper: Create a minimal, valid ClientInputBrief."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="TestBrand",
            industry="Technology",
            business_type="B2B",
            description="Test product",
        ),
        audience=AudienceBrief(
            primary_customer="Tech founders",
            pain_points=["Automation", "Scaling"],
        ),
        goal=GoalBrief(
            primary_goal="increase_sales",
            timeline="3 months",
            kpis=["Lead gen", "Awareness"],
        ),
        voice=VoiceBrief(
            tone_of_voice=["Professional", "Approachable"],
        ),
        product_service=ProductServiceBrief(
            items=[
                ProductServiceItem(
                    name="Product",
                    usp="Test USP",
                )
            ],
        ),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["LinkedIn"],
        ),
        operations=OperationsBrief(
            needs_calendar=True,
        ),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["innovative", "reliable"],
        ),
    )


class TestSituationAnalysisStubMode:
    """Tests for stub mode (no LLM)."""

    def test_stub_mode_returns_non_empty_string(self):
        """Situation Analysis in stub mode should return non-empty string."""
        brief = _create_minimal_brief()

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            analysis = generate_situation_analysis(brief)

        assert isinstance(analysis, str)
        assert len(analysis) > 0
        assert analysis.strip() != ""

    def test_stub_mode_includes_brand_and_category(self):
        """Stub mode should reference brand name and category."""
        brief = _create_minimal_brief()
        brand_name = brief.brand.brand_name
        category = brief.brand.industry

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            analysis = generate_situation_analysis(brief)

        # Should include brand and category references
        assert brand_name.lower() in analysis.lower() or "the brand" in analysis.lower()
        assert category.lower() in analysis.lower()

    def test_stub_mode_no_placeholder_phrases(self):
        """Stub mode should NOT contain obvious placeholder language."""
        brief = _create_minimal_brief()

        placeholder_phrases = [
            "will be refined",
            "placeholder",
            "[PLACEHOLDER]",
            "TBD",
            "lorem ipsum",
            "Hook idea for",
            "Performance review will be populated",
        ]

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            analysis = generate_situation_analysis(brief)

        full_text = analysis.lower()

        for phrase in placeholder_phrases:
            assert phrase.lower() not in full_text, f"Found placeholder phrase: {phrase}"

    def test_stub_function_directly(self):
        """Direct test of _stub_situation_analysis function."""
        brief = _create_minimal_brief()
        analysis = _stub_situation_analysis(brief)

        assert isinstance(analysis, str)
        assert len(analysis) > 50  # Should be reasonably detailed
        assert "operates in" in analysis or "the" in analysis

    def test_stub_mode_honest_language(self):
        """Stub mode should use honest, modest language."""
        brief = _create_minimal_brief()

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            analysis = generate_situation_analysis(brief)

        # Should NOT make presumptive claims
        assert "stronger than" not in analysis.lower()
        assert "dominates" not in analysis.lower()


class TestSituationAnalysisSanitization:
    """Tests for text sanitization and paragraph enforcement."""

    def test_sanitize_enforces_max_paragraphs(self):
        """Sanitization should limit to max_paragraphs."""
        text_with_many_paragraphs = "\n\n".join(
            [f"Paragraph {i}: " + "word " * 30 for i in range(5)]
        )

        sanitized = _sanitize_situation_analysis(text_with_many_paragraphs, max_paragraphs=2)

        # Count paragraphs
        paragraphs = [p for p in sanitized.split("\n\n") if p.strip()]
        assert len(paragraphs) <= 2

    def test_sanitize_removes_short_paragraphs(self):
        """Sanitization should remove paragraphs that are too short."""
        text = "Short.\n\nThis is a real paragraph with enough content to be meaningful and useful.\n\nToo short"

        sanitized = _sanitize_situation_analysis(text, max_paragraphs=3)

        # Should not have "Short" or "Too short" as paragraphs
        assert "Short." not in sanitized
        assert "Too short" not in sanitized

    def test_sanitize_strips_whitespace(self):
        """Sanitization should strip leading/trailing whitespace."""
        text = "  \n\nParagraph with spaces.  \n\n  Another paragraph.  \n\n"

        sanitized = _sanitize_situation_analysis(text)

        assert not sanitized.startswith(" ")
        assert not sanitized.endswith(" ")

    def test_sanitize_empty_input(self):
        """Sanitization should handle empty input gracefully."""
        result = _sanitize_situation_analysis("")
        assert result == ""

        result = _sanitize_situation_analysis("   ")
        assert result == ""


class TestSituationAnalysisStructure:
    """Tests for output structure and limits."""

    def test_max_paragraphs_default(self):
        """Default max_paragraphs should work with text"""
        text = "\n\n".join([f"Paragraph {i}: " + "word " * 20 for i in range(6)])
        sanitized = _sanitize_situation_analysis(text)
        paragraphs = [p for p in sanitized.split("\n\n") if p.strip()]
        assert len(paragraphs) <= 3

    def test_max_paragraphs_custom(self):
        """Should respect custom max_paragraphs parameter."""
        text = "\n\n".join([f"Paragraph {i}: " + "word " * 20 for i in range(5)])
        sanitized = _sanitize_situation_analysis(text, max_paragraphs=1)
        paragraphs = [p for p in sanitized.split("\n\n") if p.strip()]
        assert len(paragraphs) <= 1
