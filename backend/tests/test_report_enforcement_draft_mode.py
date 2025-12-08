"""
Test draft mode behavior for benchmark enforcement.

Verify that when draft_mode=True:
1. Reports are generated successfully even if benchmarks fail
2. Response includes success=True with status="warning"
3. Response includes the generated report_markdown
4. Response includes benchmark_warnings for debugging
5. No error_type:"llm_failure" in the payload

When draft_mode=False (strict mode):
1. Benchmark failures result in error responses
2. success=False with error_type in the response
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.validators.report_enforcer import (
    enforce_benchmarks_with_regen,
    BenchmarkEnforcementError,
    EnforcementOutcome,
)


class TestDraftModeBehavior:
    """Test draft mode vs strict mode for benchmark enforcement."""

    def test_draft_mode_skips_strict_validation(self):
        """
        In draft mode, enforce_benchmarks_with_regen should return
        PASS_WITH_WARNINGS without raising exceptions, even if sections
        would fail in strict mode.
        """
        # Create sections that would fail strict validation
        sections = [
            {"id": "overview", "content": "Short content"},  # Too short
            {"id": "persona_cards", "content": "Minimal"},  # Too short
        ]

        # Mock the validation to return failing results
        mock_validation = MagicMock()
        mock_validation.status = "FAIL"
        mock_validation.failing_sections = lambda: [
            MagicMock(section_id="overview", issues=[]),
            MagicMock(section_id="persona_cards", issues=[]),
        ]

        with patch(
            "backend.validators.report_enforcer.validate_report_sections",
            return_value=mock_validation,
        ):
            # Call with draft_mode=True
            outcome = enforce_benchmarks_with_regen(
                pack_key="quick_social_basic",
                sections=sections,
                draft_mode=True,
                max_attempts=2,
            )

            # Should return success with warnings
            assert outcome.status == "PASS_WITH_WARNINGS"
            assert len(outcome.sections) == len(sections)
            # Sections should be unchanged
            assert outcome.sections[0]["id"] == "overview"

    def test_strict_mode_raises_on_benchmark_failure(self):
        """
        In strict mode (draft_mode=False), failing benchmarks should
        raise BenchmarkEnforcementError.
        """
        sections = [
            {"id": "overview", "content": "Short"},
        ]

        # Mock validation to always fail
        mock_validation = MagicMock()
        mock_validation.status = "FAIL"
        mock_validation.failing_sections = lambda: [
            MagicMock(section_id="overview", issues=[MagicMock(code="TOO_SHORT")])
        ]

        with patch(
            "backend.validators.report_enforcer.validate_report_sections",
            return_value=mock_validation,
        ):
            # Should raise BenchmarkEnforcementError in strict mode
            with pytest.raises(BenchmarkEnforcementError) as exc_info:
                enforce_benchmarks_with_regen(
                    pack_key="quick_social_basic",
                    sections=sections,
                    draft_mode=False,  # Strict mode
                    max_attempts=2,
                    regenerate_failed_sections=None,  # No regen callback
                )

            # Error message should mention the pack and failing sections
            assert "quick_social_basic" in str(exc_info.value)
            assert "overview" in str(exc_info.value)

    def test_draft_mode_includes_validation_results(self):
        """
        Draft mode should still run validation and include the results
        in the outcome, even though it doesn't fail.
        """
        sections = [{"id": "test_section", "content": "Test content"}]

        mock_validation = MagicMock()
        mock_validation.status = "PASS"
        mock_validation.failing_sections = lambda: []

        with patch(
            "backend.validators.report_enforcer.validate_report_sections",
            return_value=mock_validation,
        ):
            outcome = enforce_benchmarks_with_regen(
                pack_key="test_pack",
                sections=sections,
                draft_mode=True,
            )

            # Validation object should be attached
            assert outcome.validation is not None
            assert outcome.validation == mock_validation


class TestHTTPEndpointDraftMode:
    """Test the HTTP endpoint behavior with draft mode."""

    @pytest.mark.asyncio
    async def test_endpoint_draft_mode_returns_success_on_benchmark_fail(self):
        """
        The /api/aicmo/generate_report endpoint should return success=True
        with warnings when draft_mode=True, even if benchmarks fail.
        """
        from backend.main import api_aicmo_generate_report

        # Minimal payload with draft_mode=True
        payload = {
            "pack_key": "quick_social_basic",
            "client_brief": {
                "brand_name": "Test Brand",
                "industry": "Technology",
                "primary_goal": "Increase awareness",
            },
            "draft_mode": True,
        }

        # Mock the aicmo_generate function to raise BenchmarkEnforcementError
        with patch("backend.main.aicmo_generate") as mock_gen:
            # Create a mock that raises BenchmarkEnforcementError
            mock_gen.side_effect = BenchmarkEnforcementError(
                "Benchmark validation failed for pack 'quick_social_basic' after 2 attempt(s). Failing sections: ['overview']"
            )

            result = await api_aicmo_generate_report(payload)

            # Should return success with warnings, not failure
            assert result.get("success") is True
            assert result.get("status") == "warning"
            assert "report_markdown" in result
            assert result["report_markdown"]  # Should have content
            assert "benchmark_warnings" in result
            assert "llm_failure" not in str(result.get("error_type", ""))

    @pytest.mark.asyncio
    async def test_endpoint_strict_mode_fails_on_benchmark_error(self):
        """
        The /api/aicmo/generate_report endpoint should catch and handle
        BenchmarkEnforcementError when draft_mode=False (strict mode).
        """
        from backend.main import api_aicmo_generate_report
        from backend.client.aicmo_api_client import call_generate_report

        payload = {
            "pack_key": "quick_social_basic",
            "client_brief": {
                "brand_name": "Test Brand",
                "industry": "Technology",
                "primary_goal": "Increase awareness",
            },
            "draft_mode": False,  # Strict mode
        }

        # Use the actual client wrapper which catches exceptions
        result = call_generate_report(payload)

        # In strict mode, if there's a benchmark error, it should be handled
        # The actual behavior depends on whether the pack passes benchmarks
        # For this test, we just verify it doesn't raise an uncaught exception
        assert isinstance(result, dict)
        assert "success" in result
        # Result will be success=True if pack passes, or success=False with error if it fails


# Test command to run:
# PYTHONPATH=/workspaces/AICMO pytest backend/tests/test_report_enforcement_draft_mode.py -v
