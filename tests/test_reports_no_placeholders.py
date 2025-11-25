"""
Cross-Pack Placeholder & Quality Tests

Ensures that ALL package outputs are free of:
- Generic tokens ("your audience", "your industry", etc.)
- Placeholder brackets ("[Brand Name]", "[insert ...]", etc.)
- Error messages or internal error text
- Incomplete sections

Run this test to validate that generator + aggregator patches
prevent any placeholder leaks to the client-facing report.

Usage:
    pytest tests/test_reports_no_placeholders.py -v
    
    Or run as smoke test with real LLM:
    OPENAI_API_KEY=sk-... pytest tests/test_reports_no_placeholders.py::test_all_packages_no_placeholders -v -s
"""

import pytest
from backend.generators.common_helpers import (
    BrandBrief,
    is_empty_or_noise,
    has_generic_tokens,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def complete_brief() -> BrandBrief:
    """A fully populated brief for testing."""
    return BrandBrief(
        brand_name="ClarityMark",
        industry="B2B SaaS marketing automation",
        primary_goal="Increase qualified demo bookings by 40%",
        timeline="Next 90 days",
        primary_customer="Marketing decision-makers at mid-market SaaS companies",
        secondary_customer="Founders at early-stage SaaS startups",
        brand_tone="professional, clear, growth-focused",
        product_service="Marketing compounding system with AI-driven optimization",
        location="Kolkata, India",
        competitors=["HubSpot", "Marketo", "ActiveCampaign"],
    )


@pytest.fixture
def bad_snippets() -> list:
    """Snippets that should NOT appear in clean output."""
    return [
        "your audience",
        "your industry",
        "your category",
        "your market",
        "your customers",
        "your solution",
        "[Brand Name]",
        "[Founder Name]",
        "[insert ",
        "not yet implemented",
        "Error generating",
        "error generating",
        "object has no attribute",
        "attribute error",
        "unexpected error",
        "traceback",
    ]


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def assert_no_generic_tokens(text: str, bad_snippets: list) -> None:
    """
    Assert that text does NOT contain any of the bad snippets.

    Raises AssertionError with the found snippet for easy debugging.
    """
    if not text:
        return

    lowered = text.lower()
    for bad in bad_snippets:
        bad_lower = bad.lower()
        if bad_lower in lowered:
            # Find the context around the bad snippet
            idx = lowered.find(bad_lower)
            context_start = max(0, idx - 50)
            context_end = min(len(text), idx + len(bad) + 50)
            context = text[context_start:context_end]

            pytest.fail(
                f"Found bad snippet: '{bad}'\n"
                f"Context: ...{context}...\n"
                f"Full text length: {len(text)} chars"
            )


def assert_report_not_empty(text: str, package_key: str) -> None:
    """Assert that the report has meaningful content."""
    assert text.strip(), f"Report for package '{package_key}' is empty"
    assert len(text.strip()) > 500, (
        f"Report for package '{package_key}' is too short ({len(text)} chars). "
        f"May indicate generation failure."
    )


def assert_no_error_messages(text: str, package_key: str) -> None:
    """Assert that the report does not contain error messages."""
    error_indicators = [
        "Error generating",
        "error generating",
        "Traceback",
        "object has no attribute",
        "attribute error",
    ]

    lowered = text.lower()
    for indicator in error_indicators:
        assert (
            indicator.lower() not in lowered
        ), f"Report for package '{package_key}' contains error message: {indicator}"


# ============================================================================
# UNIT TESTS
# ============================================================================


class TestCommonHelpersBasics:
    """Test the common_helpers functions in isolation."""

    def test_is_empty_or_noise_rejects_empty(self):
        """Empty text should be detected as noise."""
        assert is_empty_or_noise("") is True
        assert is_empty_or_noise(None) is True
        assert is_empty_or_noise("   ") is True

    def test_is_empty_or_noise_rejects_short_text(self):
        """Text < 150 chars should be noise."""
        assert is_empty_or_noise("Short section") is True
        assert (
            is_empty_or_noise(
                "This is 100 chars of text that is still too short for a real section"
            )
            is True
        )

    def test_is_empty_or_noise_rejects_error_text(self):
        """Text with error indicators should be noise."""
        assert is_empty_or_noise("Not yet implemented. " * 50) is True
        assert is_empty_or_noise("Error generating: " + "x" * 200) is True
        assert is_empty_or_noise("object has no attribute " + "x" * 200) is True

    def test_is_empty_or_noise_accepts_clean_long_text(self):
        """Clean, long text should NOT be noise."""
        clean_text = "This is a clean, substantive section about marketing strategy. " * 10
        assert is_empty_or_noise(clean_text) is False

    def test_has_generic_tokens_detects_tokens(self):
        """Should detect generic tokens."""
        assert has_generic_tokens("Your audience loves our product") is True
        assert has_generic_tokens("In your industry, this matters") is True
        assert has_generic_tokens("Your market is growing") is True

    def test_has_generic_tokens_ignores_clean_text(self):
        """Should ignore text without generic tokens."""
        clean = "ClarityMark helps SaaS teams grow faster than ever before."
        assert has_generic_tokens(clean) is False


class TestBrandBriefModel:
    """Test BrandBrief validation and structure."""

    def test_brand_brief_requires_core_fields(self, complete_brief):
        """Core fields should be required and present."""
        assert complete_brief.brand_name
        assert complete_brief.industry
        assert complete_brief.primary_customer
        assert complete_brief.product_service

    def test_brand_brief_product_service_no_attribute_error(self, complete_brief):
        """product_service should be accessible without AttributeError."""
        # This was the original issue: 'BrandBrief' object has no attribute 'product_service'
        try:
            ps = complete_brief.product_service
            assert ps  # Should have a value
        except AttributeError as e:
            pytest.fail(f"product_service attribute missing: {e}")

    def test_brand_brief_allows_none_optional_fields(self):
        """Optional fields can be None."""
        brief = BrandBrief(
            brand_name="TestBrand",
            industry="Tech",
            primary_goal="Grow",
            timeline="90 days",
            primary_customer="CTOs",
        )
        assert brief.product_service is None
        assert brief.secondary_customer is None
        assert brief.location is None


# ============================================================================
# INTEGRATION TESTS (STUB FOR REAL GENERATOR CALLS)
# ============================================================================


class TestReportSanitization:
    """Test that reports are clean before being returned to users."""

    def test_complete_brief_has_no_missing_fields(self, complete_brief):
        """Sanity check: our test brief should be complete."""
        assert complete_brief.brand_name == "ClarityMark"
        assert complete_brief.industry == "B2B SaaS marketing automation"
        assert (
            complete_brief.primary_customer
            == "Marketing decision-makers at mid-market SaaS companies"
        )
        assert (
            complete_brief.product_service
            == "Marketing compounding system with AI-driven optimization"
        )

    def test_report_with_generic_tokens_fails_validation(self, bad_snippets):
        """A report containing generic tokens should fail."""
        dirty_report = (
            "In your industry, you need a solution for your audience. "
            "Your customers want your category of product. "
            "This is repeated 50 times to make it long enough to pass length checks. " * 20
        )

        with pytest.raises(AssertionError, match="Found bad snippet"):
            assert_no_generic_tokens(dirty_report, bad_snippets)

    def test_report_without_generic_tokens_passes_validation(self, bad_snippets):
        """A clean report should pass."""
        clean_report = (
            "ClarityMark helps marketing decision-makers at mid-market SaaS companies "
            "increase qualified demo bookings by 40%. "
            "Our B2B SaaS marketing automation platform leverages AI-driven optimization "
            "to compound marketing results. "
            "This is a long, clean report with no placeholders or generic tokens. " * 10
        )

        # Should not raise
        assert_no_generic_tokens(clean_report, bad_snippets)


# ============================================================================
# SMOKE TESTS (FOR USE WITH REAL LLM)
# ============================================================================


@pytest.mark.skip(reason="Requires real LLM and OPENAI_API_KEY. Run manually with: pytest -v -s")
def test_strategic_plan_generator_no_placeholders(complete_brief):
    """
    SMOKE TEST: Generate a strategic plan and verify no placeholders.

    Requires OPENAI_API_KEY to be set.

    Usage:
        OPENAI_API_KEY=sk-... pytest tests/test_reports_no_placeholders.py::test_strategic_plan_generator_no_placeholders -v -s
    """
    try:
        from backend.generators.strategic_plan import generate_strategic_marketing_plan
        from openai import OpenAI
    except ImportError:
        pytest.skip("Generators or OpenAI not available")

    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    llm_client = OpenAI(api_key=api_key)

    report = generate_strategic_marketing_plan(
        complete_brief,
        llm_client,
        model_name="gpt-4.1-mini",
    )

    bad_snippets = [
        "your industry",
        "your audience",
        "your category",
        "[Brand Name]",
        "not yet implemented",
        "Error generating",
    ]

    assert_report_not_empty(report, "strategic_plan")
    assert_no_error_messages(report, "strategic_plan")
    assert_no_generic_tokens(report, bad_snippets)


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    # Allow running as: python -m pytest tests/test_reports_no_placeholders.py -v
    pytest.main([__file__, "-v"])
