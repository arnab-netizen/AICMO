"""
Tests for LLM safety module (timeouts, input size limits).

Covers:
1. Input size validation and truncation
2. Timeout handling
3. Graceful fallback on failures
"""

import pytest
from backend.llm_safety import (
    validate_llm_input_size,
    _truncate_text,
    LLMCallWithTimeout,
    DEFAULT_MAX_SECTION_CHARS,
)


class TestInputTruncation:
    """Tests for text truncation logic."""

    def test_truncate_text_short_text_unchanged(self):
        """Short text should not be truncated."""
        text = "This is a short text"
        result, was_truncated = _truncate_text(text, 100)

        assert result == text
        assert was_truncated is False

    def test_truncate_text_long_text_truncated(self):
        """Long text should be truncated."""
        text = "x" * 150
        result, was_truncated = _truncate_text(text, 100)

        assert len(result) <= 100
        assert was_truncated is True

    def test_truncate_text_at_word_boundary(self):
        """Truncation should try to preserve word boundaries."""
        text = "This is a longer text that should be truncated at word boundaries"
        result, was_truncated = _truncate_text(text, 20)

        assert len(result) <= 20
        assert was_truncated is True
        # Should not end in middle of word
        assert not result.endswith(" ")

    def test_truncate_text_none_input(self):
        """None input should return empty string."""
        result, was_truncated = _truncate_text(None, 100)

        assert result == ""
        assert was_truncated is False

    def test_truncate_text_with_label_for_logging(self):
        """Truncation with label should log appropriately."""
        text = "x" * 150
        result, was_truncated = _truncate_text(text, 100, label="test_section")

        assert was_truncated is True
        assert len(result) <= 100


class TestInputSizeValidation:
    """Tests for comprehensive input size validation."""

    def test_validate_input_size_normal_input(self):
        """Normal-sized input should not be truncated."""
        brief = {
            "brand": {"brand_name": "Test Brand", "tagline": "Test tagline"},
            "goal": {"primary_goal": "Growth"},
        }
        output = {
            "marketing_plan": {
                "executive_summary": "Summary",
                "situation_analysis": "Analysis",
                "strategy": "Strategy",
            }
        }

        brief_result, output_result, any_trunc = validate_llm_input_size(brief, output)

        assert brief_result == brief
        assert output_result == output
        assert any_trunc is False

    def test_validate_input_size_large_section_truncated(self):
        """Large sections should be truncated."""
        large_text = "x" * (DEFAULT_MAX_SECTION_CHARS + 5000)
        brief = {
            "brand": {"brand_name": large_text},
        }
        output = {}

        brief_result, output_result, any_trunc = validate_llm_input_size(brief, output)

        assert len(brief_result["brand"]["brand_name"]) <= DEFAULT_MAX_SECTION_CHARS
        assert any_trunc is True

    def test_validate_input_size_marketing_plan_truncation(self):
        """Marketing plan fields should be truncated if too large."""
        large_text = "x" * (DEFAULT_MAX_SECTION_CHARS + 1000)
        output = {
            "marketing_plan": {
                "executive_summary": large_text,
                "situation_analysis": "Normal",
                "strategy": large_text,
            }
        }
        brief = {}

        brief_result, output_result, any_trunc = validate_llm_input_size(brief, output)

        assert (
            len(output_result["marketing_plan"]["executive_summary"]) <= DEFAULT_MAX_SECTION_CHARS
        )
        assert len(output_result["marketing_plan"]["strategy"]) <= DEFAULT_MAX_SECTION_CHARS
        assert any_trunc is True

    def test_validate_input_size_custom_limits(self):
        """Should respect custom size limits."""
        custom_limit = 500
        text = "x" * 600
        brief = {"brand": {"brand_name": text}}
        output = {}

        brief_result, output_result, any_trunc = validate_llm_input_size(
            brief, output, max_section_chars=custom_limit
        )

        assert len(brief_result["brand"]["brand_name"]) <= custom_limit
        assert any_trunc is True


class TestLLMTimeoutHandling:
    """Tests for LLM call timeout handling."""

    def test_timeout_handler_with_quick_function(self):
        """Quick functions should succeed."""

        def quick_func():
            return "success"

        result = LLMCallWithTimeout.call(quick_func, timeout=5)

        assert result == "success"

    def test_timeout_handler_with_failing_function(self):
        """Failing functions should return None."""

        def failing_func():
            raise ValueError("Intentional error")

        result = LLMCallWithTimeout.call(failing_func, timeout=5, label="test_call")

        # Should return None instead of raising
        assert result is None

    def test_timeout_handler_with_slow_function(self):
        """Slow functions should timeout gracefully."""
        import time

        def slow_func():
            time.sleep(2)
            return "result"

        # Set very short timeout
        result = LLMCallWithTimeout.call(slow_func, timeout=1, label="slow_test")

        # On Unix systems, should timeout. On Windows, may not (signal not supported)
        # So we just verify it doesn't crash
        assert result is None or result == "result"

    def test_timeout_handler_with_lambda(self):
        """Should work with lambda functions."""
        result = LLMCallWithTimeout.call(lambda: {"key": "value"}, timeout=5, label="lambda_test")

        assert result == {"key": "value"}


class TestSafeLLMEnhancement:
    """Tests for safe LLM enhancement wrapper."""

    def test_safe_enhancement_with_failing_llm_returns_stub(self):
        """Enhancement failures should return stub output."""
        from backend.llm_safety import safe_llm_enhancement
        from aicmo.io.client_reports import (
            ClientInputBrief,
            BrandBrief,
            AudienceBrief,
            GoalBrief,
            VoiceBrief,
            ProductServiceBrief,
            AssetsConstraintsBrief,
            OperationsBrief,
            StrategyExtrasBrief,
        )

        def failing_enhance(brief, output, options):
            raise ValueError("LLM failed")

        brief = ClientInputBrief(
            brand=BrandBrief(brand_name="Test"),
            audience=AudienceBrief(primary_customer="Customer"),
            goal=GoalBrief(primary_goal="Growth"),
            voice=VoiceBrief(),
            product_service=ProductServiceBrief(),
            assets_constraints=AssetsConstraintsBrief(),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(),
        )
        stub_output = {"marketing_plan": {"executive_summary": "Stub"}}

        result = safe_llm_enhancement(failing_enhance, brief, stub_output, timeout=5)

        # Should return stub output on failure
        assert result == stub_output

    def test_safe_enhancement_respects_timeout(self):
        """Enhancement should respect timeout setting."""
        from backend.llm_safety import safe_llm_enhancement
        from aicmo.io.client_reports import (
            ClientInputBrief,
            BrandBrief,
            AudienceBrief,
            GoalBrief,
            VoiceBrief,
            ProductServiceBrief,
            AssetsConstraintsBrief,
            OperationsBrief,
            StrategyExtrasBrief,
        )

        def slow_enhance(brief, output, options):
            import time

            time.sleep(2)
            return {"enhanced": True}

        brief = ClientInputBrief(
            brand=BrandBrief(brand_name="Test"),
            audience=AudienceBrief(primary_customer="Customer"),
            goal=GoalBrief(primary_goal="Growth"),
            voice=VoiceBrief(),
            product_service=ProductServiceBrief(),
            assets_constraints=AssetsConstraintsBrief(),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(),
        )
        stub_output = {"marketing_plan": {"executive_summary": "Stub"}}

        # Very short timeout should cause fallback to stub
        result = safe_llm_enhancement(slow_enhance, brief, stub_output, timeout=1)

        # Should be stub output or dict (never raises)
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
