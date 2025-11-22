"""
Tests for SWOT generation.

Verify:
- Stub mode produces valid, non-placeholder SWOT
- LLM mode integration works with proper fallback
- SWOT is always present and valid in generated reports
- No "will be refined", "placeholder", "TBD" in SWOT content
"""

import json
import os
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from aicmo.generators.swot_generator import generate_swot, _stub_swot, _sanitize_swot
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


class TestSWOTGeneratorStubMode:
    """Tests for stub mode (no LLM)."""

    def test_swot_stub_mode_returns_valid_structure(self):
        """SWOT in stub mode should have all 4 keys."""
        brief = _create_minimal_brief()

        # Force stub mode
        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            swot = generate_swot(brief)

        assert isinstance(swot, dict)
        assert set(swot.keys()) == {"strengths", "weaknesses", "opportunities", "threats"}

    def test_swot_stub_mode_all_lists(self):
        """All SWOT values should be lists of strings."""
        brief = _create_minimal_brief()

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            swot = generate_swot(brief)

        for key, items in swot.items():
            assert isinstance(items, list), f"{key} is not a list"
            for item in items:
                assert isinstance(item, str), f"{key} contains non-string: {item}"
                assert len(item) > 0, f"{key} contains empty string"

    def test_swot_stub_mode_no_placeholder_phrases(self):
        """Stub SWOT should never contain obvious placeholder language."""
        brief = _create_minimal_brief()

        placeholder_phrases = [
            "will be refined",
            "placeholder",
            "[PLACEHOLDER]",
            "TBD",
            "Hook idea for",
            "Performance review will be populated",
        ]

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            swot = generate_swot(brief)

        full_text = " ".join([item for items in swot.values() for item in items]).lower()

        for phrase in placeholder_phrases:
            assert phrase.lower() not in full_text, f"Found placeholder phrase: {phrase}"

    def test_swot_stub_mode_contains_brand_name(self):
        """Stub SWOT should ideally reference the brand name."""
        brief = _create_minimal_brief()
        brand_name = brief.brand.brand_name

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            swot = generate_swot(brief)

        full_text = " ".join([item for items in swot.values() for item in items])

        # At least mention the brand (or "Your Brand" fallback)
        assert brand_name.lower() in full_text.lower() or "your brand" in full_text.lower()

    def test_swot_stub_function_directly(self):
        """Direct test of _stub_swot function."""
        brief = _create_minimal_brief()
        swot = _stub_swot(brief)

        assert len(swot["strengths"]) >= 2
        assert len(swot["weaknesses"]) >= 2
        assert len(swot["opportunities"]) >= 2
        assert len(swot["threats"]) >= 2


class TestSWOTGeneratorSanitization:
    """Tests for SWOT sanitization."""

    def test_sanitize_swot_enforces_max_items(self):
        """Sanitization should truncate lists to max_items."""
        swot_raw = {
            "strengths": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6"],
            "weaknesses": ["W1"],
            "opportunities": [],
            "threats": ["T1", "T2"],
        }

        sanitized = _sanitize_swot(swot_raw, max_items=3)

        assert len(sanitized["strengths"]) == 3
        assert len(sanitized["weaknesses"]) == 1
        assert len(sanitized["opportunities"]) == 0
        assert len(sanitized["threats"]) == 2

    def test_sanitize_swot_strips_whitespace(self):
        """Sanitization should strip leading/trailing whitespace."""
        swot_raw = {
            "strengths": ["  Item with spaces  ", "\t\tTabbed\t\t"],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        }

        sanitized = _sanitize_swot(swot_raw)

        assert sanitized["strengths"][0] == "Item with spaces"
        assert sanitized["strengths"][1] == "Tabbed"

    def test_sanitize_swot_removes_empties(self):
        """Sanitization should skip empty or whitespace-only items."""
        swot_raw = {
            "strengths": ["Valid Item", "   ", "", None, "Another Valid"],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        }

        sanitized = _sanitize_swot(swot_raw)

        assert len(sanitized["strengths"]) == 2
        assert sanitized["strengths"][0] == "Valid Item"
        assert sanitized["strengths"][1] == "Another Valid"

    def test_sanitize_swot_handles_non_list_values(self):
        """Sanitization should gracefully handle non-list values."""
        swot_raw = {
            "strengths": "Not a list",
            "weaknesses": None,
            "opportunities": 123,
            "threats": ["Valid Item"],
        }

        sanitized = _sanitize_swot(swot_raw)

        assert sanitized["strengths"] == []
        assert sanitized["weaknesses"] == []
        assert sanitized["opportunities"] == []
        assert sanitized["threats"] == ["Valid Item"]


class TestSWOTLLMIntegration:
    """Tests for LLM integration with mocking."""

    def test_swot_llm_mode_with_valid_response(self):
        """LLM mode should parse valid JSON response."""
        brief = _create_minimal_brief()
        mock_response = {
            "strengths": ["LLM Generated Strength 1", "LLM Generated Strength 2"],
            "weaknesses": ["LLM Generated Weakness"],
            "opportunities": ["LLM Generated Opportunity"],
            "threats": ["LLM Generated Threat"],
        }

        # Mock the LLM client at the point where it's used in the generator
        with patch("aicmo.llm.client._get_llm_provider") as mock_provider:
            mock_provider.return_value = "claude"

            with patch("aicmo.llm.client._get_claude_client") as mock_client:
                mock_response_obj = MagicMock()
                mock_response_obj.content = [MagicMock(text=json.dumps(mock_response))]
                mock_client.return_value.messages.create.return_value = mock_response_obj

                with patch.dict(os.environ, {"AICMO_USE_LLM": "1"}):
                    swot = generate_swot(brief)

                assert swot["strengths"] == ["LLM Generated Strength 1", "LLM Generated Strength 2"]
                assert swot["weaknesses"] == ["LLM Generated Weakness"]

    def test_swot_llm_mode_falls_back_on_invalid_json(self):
        """LLM mode should fall back to stub if JSON parsing fails."""
        brief = _create_minimal_brief()

        with patch("aicmo.llm.client._get_llm_provider") as mock_provider:
            mock_provider.return_value = "claude"

            with patch("aicmo.llm.client._get_claude_client") as mock_client:
                # Return invalid JSON
                mock_response_obj = MagicMock()
                mock_response_obj.content = [MagicMock(text="This is not valid JSON {")]
                mock_client.return_value.messages.create.return_value = mock_response_obj

                with patch.dict(os.environ, {"AICMO_USE_LLM": "1"}):
                    swot = generate_swot(brief)

                # Should fall back to stub
                assert set(swot.keys()) == {"strengths", "weaknesses", "opportunities", "threats"}
                assert all(isinstance(v, list) for v in swot.values())

    def test_swot_llm_mode_falls_back_on_exception(self):
        """LLM mode should fall back to stub if LLM call throws."""
        brief = _create_minimal_brief()

        with patch("aicmo.llm.client._get_llm_provider") as mock_provider:
            mock_provider.return_value = "claude"

            with patch("aicmo.llm.client._get_claude_client") as mock_client:
                mock_client.side_effect = RuntimeError("LLM is down")

                with patch.dict(os.environ, {"AICMO_USE_LLM": "1"}):
                    swot = generate_swot(brief)

                # Should gracefully fall back to stub
                assert set(swot.keys()) == {"strengths", "weaknesses", "opportunities", "threats"}
                assert all(isinstance(v, list) for v in swot.values())


class TestSWOTIntegrationInReport:
    """Integration tests: SWOT in generated reports."""

    def test_aicmo_generate_includes_swot_stub_mode(self):
        """Generated report should include SWOT even in stub mode."""
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

        # Check SWOT is present
        assert "marketing_plan" in data
        assert "swot" in data["marketing_plan"]
        swot = data["marketing_plan"]["swot"]

        # Verify structure
        assert set(swot.keys()) == {"strengths", "weaknesses", "opportunities", "threats"}
        for key, items in swot.items():
            assert isinstance(items, list)
            for item in items:
                assert isinstance(item, str)
                assert len(item) > 0

    def test_aicmo_generate_swot_no_placeholder_phrases(self):
        """SWOT in generated report should not contain placeholder phrases."""
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
            "Hook idea for",
            "Performance review will be populated",
        ]

        with patch.dict(os.environ, {"AICMO_USE_LLM": "0"}):
            resp = client.post("/aicmo/generate", json=payload)

        assert resp.status_code == 200
        data = resp.json()
        swot = data["marketing_plan"]["swot"]

        # Concatenate all SWOT text
        full_text = " ".join([item for items in swot.values() for item in items]).lower()

        for phrase in placeholder_phrases:
            assert phrase.lower() not in full_text, f"Found placeholder in SWOT: {phrase}"


class TestSWOTMaxItems:
    """Tests for max_items enforcement."""

    def test_swot_max_items_default(self):
        """Default max_items should be 5."""
        brief = _create_minimal_brief()
        mock_response = {
            "strengths": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
            "weaknesses": ["W1"],
            "opportunities": ["O1"],
            "threats": ["T1"],
        }

        with patch("aicmo.llm.client._get_llm_provider") as mock_provider:
            mock_provider.return_value = "claude"

            with patch("aicmo.llm.client._get_claude_client") as mock_client:
                mock_response_obj = MagicMock()
                mock_response_obj.content = [MagicMock(text=json.dumps(mock_response))]
                mock_client.return_value.messages.create.return_value = mock_response_obj

                with patch.dict(os.environ, {"AICMO_USE_LLM": "1"}):
                    swot = generate_swot(brief)

                assert len(swot["strengths"]) == 5, "Should limit to max 5 items"

    def test_swot_max_items_custom(self):
        """Should respect custom max_items parameter."""
        brief = _create_minimal_brief()
        mock_response = {
            "strengths": ["S1", "S2", "S3", "S4", "S5", "S6"],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        }

        with patch("aicmo.llm.client._get_llm_provider") as mock_provider:
            mock_provider.return_value = "claude"

            with patch("aicmo.llm.client._get_claude_client") as mock_client:
                mock_response_obj = MagicMock()
                mock_response_obj.content = [MagicMock(text=json.dumps(mock_response))]
                mock_client.return_value.messages.create.return_value = mock_response_obj

                with patch.dict(os.environ, {"AICMO_USE_LLM": "1"}):
                    swot = generate_swot(brief, max_items=3)

                assert len(swot["strengths"]) == 3, "Should limit to custom max 3 items"
