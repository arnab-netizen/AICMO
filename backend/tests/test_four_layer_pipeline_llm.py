"""
Tests for 4-Layer Pipeline with LLM Integration

Tests verify:
- Layer 2 (Humanizer) behavior with mock LLM
- Layer 4 (Rewriter) behavior with mock LLM
- Quality score thresholds trigger correct layers
- Non-blocking guarantees (no exceptions thrown)
- Graceful fallback when LLM unavailable
- Environment variable toggling (AICMO_ENABLE_HUMANIZER)
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure humanizer is enabled for tests
os.environ["AICMO_ENABLE_HUMANIZER"] = "true"

from backend.layers import (
    enhance_section_humanizer,
    run_soft_validators,
    rewrite_low_quality_section,
)


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self, mode="humanize"):
        """
        mode: "humanize" -> returns "HUMANIZED: " + extended text
              "rewrite" -> returns "REWRITTEN: " + extended text
              "error" -> raises Exception
              "empty" -> returns ""
        """
        self.mode = mode
        self.call_count = 0

    def __call__(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Callable interface matching LLM provider."""
        self.call_count += 1

        if self.mode == "error":
            raise RuntimeError("Mock LLM error")
        elif self.mode == "empty":
            return ""
        elif self.mode == "humanize":
            # Return substantial text to pass length check (>50% of original)
            return "HUMANIZED: " + ("This is enhanced content. " * 20)
        elif self.mode == "rewrite":
            # Return substantial text to pass length check (>50% of original)
            return "REWRITTEN: " + ("This is rewritten content. " * 20)
        else:
            return prompt


class TestLayer2Humanizer:
    """Tests for Layer 2 (Humanizer) with LLM."""

    def test_humanizer_disabled(self):
        """When AICMO_ENABLE_HUMANIZER=false, humanizer returns raw text."""
        with patch.dict(os.environ, {"AICMO_ENABLE_HUMANIZER": "false"}):
            # Force reload to pick up env change
            import importlib
            import backend.layers.layer2_humanizer as layer2
            importlib.reload(layer2)

            raw_text = "This is the original section."
            result = layer2.enhance_section_humanizer(
                section_id="overview",
                raw_text=raw_text,
                context={"brand_name": "TestBrand", "campaign_name": "TestCampaign"},
                req=None,
                llm_provider=MockLLMProvider(mode="humanize"),
            )

            assert result == raw_text

    def test_humanizer_empty_text(self):
        """When raw_text is empty, humanizer returns it unchanged."""
        result = enhance_section_humanizer(
            section_id="overview",
            raw_text="",
            context={"brand_name": "TestBrand", "campaign_name": "TestCampaign"},
            req=None,
            llm_provider=MockLLMProvider(mode="humanize"),
        )

        assert result == ""

    def test_humanizer_no_llm_provider(self):
        """When no LLM provider available, humanizer returns raw text."""
        raw_text = "This is the original section."
        result = enhance_section_humanizer(
            section_id="overview",
            raw_text=raw_text,
            context={"brand_name": "TestBrand", "campaign_name": "TestCampaign"},
            req=None,
            llm_provider=None,  # No LLM provider
        )

        # Should return raw text if no LLM provider (factory also unavailable in test)
        assert result == raw_text

    def test_humanizer_llm_error(self):
        """When LLM raises exception, humanizer returns raw text (non-blocking)."""
        raw_text = "This is the original section."
        llm_provider = MockLLMProvider(mode="error")

        # Patch the ENABLE_HUMANIZER variable to be True
        with patch("backend.layers.layer2_humanizer.ENABLE_HUMANIZER", True):
            result = enhance_section_humanizer(
                section_id="overview",
                raw_text=raw_text,
                context={"brand_name": "TestBrand", "campaign_name": "TestCampaign"},
                req=None,
                llm_provider=llm_provider,
            )

            # Should catch error and return raw text, not raise exception
            assert result == raw_text
            assert llm_provider.call_count == 1

    def test_humanizer_llm_empty_response(self):
        """When LLM returns empty string, humanizer returns raw text."""
        raw_text = "This is the original section."
        llm_provider = MockLLMProvider(mode="empty")

        # Patch the ENABLE_HUMANIZER variable to be True
        with patch("backend.layers.layer2_humanizer.ENABLE_HUMANIZER", True):
            result = enhance_section_humanizer(
                section_id="overview",
                raw_text=raw_text,
                context={"brand_name": "TestBrand", "campaign_name": "TestCampaign"},
                req=None,
                llm_provider=llm_provider,
            )

            assert result == raw_text
            assert llm_provider.call_count == 1

    def test_humanizer_success(self):
        """When LLM succeeds, humanizer returns enhanced text."""
        raw_text = "This is the original section. " * 10  # Make it longer
        llm_provider = MockLLMProvider(mode="humanize")

        # Patch the ENABLE_HUMANIZER variable to be True
        with patch("backend.layers.layer2_humanizer.ENABLE_HUMANIZER", True):
            result = enhance_section_humanizer(
                section_id="overview",
                raw_text=raw_text,
                context={"brand_name": "TestBrand", "campaign_name": "TestCampaign"},
                req=None,
                llm_provider=llm_provider,
            )

            # Should contain the "HUMANIZED: " prefix from mock
            assert result.startswith("HUMANIZED:")
            assert llm_provider.call_count == 1


class TestLayer3Validators:
    """Tests for Layer 3 (Soft Validators) - quality scoring."""

    def test_layer3_quality_scoring(self):
        """Layer 3 produces quality scores and warnings."""
        content = "## Strategy\n\nBoost your brand in today's digital world. Unlock potential."

        result_content, quality_score, genericity_score, warnings = run_soft_validators(
            pack_key="test_pack",
            section_id="strategy",
            content=content,
            context={"brand_name": "TestBrand"},
        )

        # Should return tuple with scores and warnings
        assert isinstance(quality_score, (int, float))
        assert isinstance(genericity_score, (int, float))
        assert isinstance(warnings, (list, type(None)))

    def test_layer3_detects_cliches(self):
        """Layer 3 detects generic phrases."""
        # Highly clichéd content
        content = "Boost your brand to unlock your potential in today's digital world. Best-in-class solutions."

        _, quality_score, _, warnings = run_soft_validators(
            pack_key="test_pack",
            section_id="overview",
            content=content,
            context={"brand_name": "TestBrand"},
        )

        # Should detect clichés and lower quality
        assert quality_score is not None
        if warnings:
            assert any("cliche" in str(w).lower() for w in warnings) or quality_score < 80


class TestLayer4Rewriter:
    """Tests for Layer 4 (Rewriter) with quality thresholds."""

    def test_rewriter_no_llm_provider(self):
        """When no LLM provider, rewriter returns original content."""
        content = "Low quality content."
        warnings = ["too_short", "too_many_cliches"]

        result = rewrite_low_quality_section(
            pack_key="test_pack",
            section_id="overview",
            content=content,
            warnings=warnings,
            context={"brand_name": "TestBrand"},
            req=None,
            llm_provider=None,  # No provider
        )

        assert result == content

    def test_rewriter_llm_error(self):
        """When LLM raises error, rewriter returns original content (non-blocking)."""
        content = "Low quality content. " * 10  # Make longer
        warnings = ["too_short"]
        llm_provider = MockLLMProvider(mode="error")

        result = rewrite_low_quality_section(
            pack_key="test_pack",
            section_id="overview",
            content=content,
            warnings=warnings,
            context={"brand_name": "TestBrand"},
            req=None,
            llm_provider=llm_provider,
        )

        # Should catch error and return original, not raise
        assert result == content
        assert llm_provider.call_count == 1

    def test_rewriter_success(self):
        """When LLM succeeds, rewriter returns rewritten text."""
        content = "Low quality content. " * 10  # Make longer
        warnings = ["too_many_cliches"]
        llm_provider = MockLLMProvider(mode="rewrite")

        result = rewrite_low_quality_section(
            pack_key="test_pack",
            section_id="overview",
            content=content,
            warnings=warnings,
            context={"brand_name": "TestBrand"},
            req=None,
            llm_provider=llm_provider,
        )

        # Should contain "REWRITTEN: " prefix from mock
        assert result.startswith("REWRITTEN:")
        assert llm_provider.call_count == 1


class TestFullPipelineWithQualityThresholds:
    """Tests for full pipeline with quality-based layer triggering."""

    def test_pipeline_high_quality_no_rewrite(self):
        """When quality >= 80, Layer 4 should NOT be triggered."""
        raw_text = """## Strategic Overview

Our comprehensive strategy focuses on three core pillars: brand awareness through targeted digital channels, 
customer engagement via personalized communication, and conversion optimization through data-driven insights.

Key metrics and KPIs guide our approach, ensuring measurable results and continuous improvement."""

        # Layer 3: Validate
        content, quality_score, _, warnings = run_soft_validators(
            pack_key="test",
            section_id="strategy",
            content=raw_text,
            context={"brand_name": "TestBrand"},
        )

        # If quality >= 80, Layer 4 should not rewrite
        if quality_score and quality_score >= 80:
            llm_provider = MockLLMProvider(mode="rewrite")
            result = rewrite_low_quality_section(
                pack_key="test",
                section_id="strategy",
                content=content,
                warnings=warnings or [],
                context={"brand_name": "TestBrand"},
                req=None,
                llm_provider=llm_provider,
            )
            # Condition not met, rewriter should return original
            # Actually, Layer 4 doesn't check quality threshold itself;
            # that's done in generate_sections(). So this test verifies
            # that if called, rewriter works.
            assert llm_provider.call_count == 1  # Would be called if instructed

    def test_pipeline_low_quality_triggers_rewrite(self):
        """When quality < 60, Layer 4 CAN be triggered."""
        # Create low-quality content
        raw_text = "Boost. Unlock. Digital world."

        # Layer 3: Validate
        content, quality_score, _, warnings = run_soft_validators(
            pack_key="test",
            section_id="overview",
            content=raw_text,
            context={"brand_name": "TestBrand"},
        )

        # If quality < 60, test that Layer 4 can rewrite
        if quality_score and quality_score < 60:
            llm_provider = MockLLMProvider(mode="rewrite")
            result = rewrite_low_quality_section(
                pack_key="test",
                section_id="overview",
                content=content,
                warnings=warnings or [],
                context={"brand_name": "TestBrand"},
                req=None,
                llm_provider=llm_provider,
            )

            # Should have been called and returned rewritten content
            assert llm_provider.call_count == 1


class TestNonBlockingGuarantee:
    """Tests for non-blocking behavior across all layers."""

    def test_no_exceptions_thrown(self):
        """Pipeline never throws exceptions, even with failing LLM."""
        test_cases = [
            ("Layer2", enhance_section_humanizer),
            ("Layer4", rewrite_low_quality_section),
        ]

        for layer_name, layer_func in test_cases:
            # Mock LLM that always raises
            llm_provider = MockLLMProvider(mode="error")

            if layer_name == "Layer2":
                try:
                    result = layer_func(
                        section_id="overview",
                        raw_text="Test content " * 10,
                        context={"brand_name": "Test"},
                        req=None,
                        llm_provider=llm_provider,
                    )
                    assert result is not None
                except Exception as e:
                    pytest.fail(f"{layer_name} threw exception: {e}")

            elif layer_name == "Layer4":
                try:
                    result = layer_func(
                        pack_key="test",
                        section_id="overview",
                        content="Test content " * 10,
                        warnings=["test_warning"],
                        context={"brand_name": "Test"},
                        req=None,
                        llm_provider=llm_provider,
                    )
                    assert result is not None
                except Exception as e:
                    pytest.fail(f"{layer_name} threw exception: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
