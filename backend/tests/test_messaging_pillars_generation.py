"""
Tests for Messaging Pillars generation.

Verify:
- Stub mode produces honest, modest pillars without placeholders
- LLM mode integration works with proper fallback
- Pillars are always present and valid in generated reports
- No "will be refined", "placeholder", "TBD" in pillar content
"""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from aicmo.generators.messaging_pillars_generator import (
    generate_messaging_pillars,
    _stub_messaging_pillars,
    _sanitize_messaging_pillars,
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
    StrategyPillar,
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


class TestMessagingPillarsStubMode:
    """Tests for stub mode (no LLM)."""

    def test_stub_mode_returns_non_empty_list(self):
        """Messaging Pillars in stub mode should return non-empty list."""
        brief = _create_minimal_brief()

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            pillars = generate_messaging_pillars(brief)

        assert isinstance(pillars, list)
        assert len(pillars) > 0
        assert len(pillars) <= 3  # max_pillars default

    def test_stub_mode_pillars_have_required_fields(self):
        """Each pillar should have name, description, and kpi_impact."""
        brief = _create_minimal_brief()

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            pillars = generate_messaging_pillars(brief)

        for pillar in pillars:
            assert isinstance(pillar, StrategyPillar)
            assert pillar.name and len(pillar.name) > 0
            assert pillar.description is not None
            assert pillar.kpi_impact is not None

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
            pillars = generate_messaging_pillars(brief)

        # Combine all text from pillars
        full_text = " ".join(
            [
                pillar.name + " " + (pillar.description or "") + " " + (pillar.kpi_impact or "")
                for pillar in pillars
            ]
        ).lower()

        for phrase in placeholder_phrases:
            assert phrase.lower() not in full_text, f"Found placeholder phrase: {phrase}"

    def test_stub_function_directly(self):
        """Direct test of _stub_messaging_pillars function."""
        brief = _create_minimal_brief()
        pillars = _stub_messaging_pillars(brief)

        assert isinstance(pillars, list)
        assert len(pillars) > 0
        assert all(isinstance(p, StrategyPillar) for p in pillars)

    def test_stub_mode_honest_language(self):
        """Stub mode should use honest, modest language."""
        brief = _create_minimal_brief()

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            pillars = generate_messaging_pillars(brief)

        full_text = " ".join(
            [
                pillar.name + " " + (pillar.description or "") + " " + (pillar.kpi_impact or "")
                for pillar in pillars
            ]
        ).lower()

        # Should NOT make presumptive claims
        assert "stronger than" not in full_text
        assert "dominates" not in full_text
        assert "#1 in" not in full_text


class TestMessagingPillarsSanitization:
    """Tests for pillar sanitization and enforcement."""

    def test_sanitize_enforces_max_pillars(self):
        """Sanitization should limit to max_pillars."""
        pillars = [
            StrategyPillar(
                name=f"Pillar {i}", description=f"Description {i}", kpi_impact=f"KPI {i}"
            )
            for i in range(5)
        ]

        sanitized = _sanitize_messaging_pillars(pillars, max_pillars=2)

        assert len(sanitized) <= 2

    def test_sanitize_removes_pillars_without_names(self):
        """Sanitization should remove pillars with empty names."""
        pillars = [
            StrategyPillar(name="Good Pillar", description="Valid", kpi_impact="KPI"),
            StrategyPillar(name="", description="Empty name", kpi_impact="KPI"),
            StrategyPillar(name="Another Good", description="Valid", kpi_impact="KPI"),
        ]

        sanitized = _sanitize_messaging_pillars(pillars)

        # Should only have 2 (removed the one with empty name)
        assert len(sanitized) == 2
        assert all(p.name for p in sanitized)

    def test_sanitize_empty_input(self):
        """Sanitization should handle empty input gracefully."""
        result = _sanitize_messaging_pillars([])
        assert result == []


class TestMessagingPillarsLLMIntegration:
    """Tests for LLM integration with mocking."""

    def test_llm_mode_generates_pillars_or_falls_back(self):
        """LLM mode should generate pillars or gracefully fall back to stub."""
        brief = _create_minimal_brief()

        with patch.dict(os.environ, {"AICMO_USE_LLM": "1"}):
            # Without actual LLM credentials, this should fall back to stub
            pillars = generate_messaging_pillars(brief)

            # Should return valid pillars regardless of LLM availability
            assert isinstance(pillars, list)
            assert len(pillars) > 0
            assert all(isinstance(p, StrategyPillar) for p in pillars)
            assert all(p.name for p in pillars)


class TestMessagingPillarsIntegrationInReport:
    """Integration tests: Messaging Pillars in generated reports."""

    def test_aicmo_generate_includes_messaging_pillars_stub_mode(self):
        """Generated report should include Messaging Pillars even in stub mode."""
        brief = _create_minimal_brief()

        payload = {
            "brief": brief.model_dump(),
            "industry_key": None,
            "include_agency_grade": False,
        }

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            resp = client.post("/aicmo/generate", json=payload)

        assert resp.status_code == 200
        data = resp.json()

        # Check Messaging Pillars are present
        assert "marketing_plan" in data
        assert "pillars" in data["marketing_plan"]
        pillars = data["marketing_plan"]["pillars"]

        # Verify it's a non-empty list
        assert isinstance(pillars, list)
        assert len(pillars) > 0

    def test_aicmo_generate_pillars_no_placeholder_phrases(self):
        """Messaging Pillars in generated report should NOT contain placeholders."""
        brief = _create_minimal_brief()

        payload = {
            "brief": brief.model_dump(),
            "industry_key": None,
            "include_agency_grade": False,
        }

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
            resp = client.post("/aicmo/generate", json=payload)

        assert resp.status_code == 200
        data = resp.json()
        pillars = data["marketing_plan"]["pillars"]

        # Combine all pillar text
        full_text = " ".join(
            [
                f"{p.get('name', '')} {p.get('description', '')} {p.get('kpi_impact', '')}"
                for p in pillars
            ]
        ).lower()

        for phrase in placeholder_phrases:
            assert phrase.lower() not in full_text, f"Found placeholder phrase in report: {phrase}"


class TestMessagingPillarsStructure:
    """Tests for output structure and limits."""

    def test_max_pillars_default(self):
        """Default max_pillars should be 3."""
        brief = _create_minimal_brief()

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            pillars = generate_messaging_pillars(brief)

        assert len(pillars) <= 3

    def test_max_pillars_custom(self):
        """Should respect custom max_pillars parameter."""
        brief = _create_minimal_brief()

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            pillars = generate_messaging_pillars(brief, max_pillars=1)

        assert len(pillars) <= 1
