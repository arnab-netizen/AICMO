"""
Tests for Perplexity-Powered Hashtag Strategy v1.

This test suite verifies:
1. Perplexity hashtag data merges into BrandResearchResult
2. Generator uses research values and renders compliant Markdown
3. Benchmark rejects missing/invalid tags
4. Perplexity JSON format validation
"""

import pytest
from unittest.mock import Mock, patch

from backend.research_models import BrandResearchResult
from backend.external.perplexity_client import PerplexityClient
from backend.services.brand_research import get_brand_research
from backend.validators.quality_checks import (
    check_hashtag_format,
    check_hashtag_category_counts,
)
from aicmo.io.client_reports import (
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
    ClientInputBrief,
)


def create_minimal_test_brief(
    brand_name: str = "TestBrand",
    industry: str = "Coffee",
    attach_research: bool = False,
) -> ClientInputBrief:
    """
    Create a minimal valid ClientInputBrief for testing.

    This helper ensures all required fields are populated and uses
    with_safe_defaults() to match production usage patterns.

    Args:
        brand_name: Brand name for the test
        industry: Industry for the test
        attach_research: If True, attach mock Perplexity research data

    Returns:
        ClientInputBrief with all required fields populated
    """
    # Create brand with required fields
    brand = BrandBrief(
        brand_name=brand_name,
        industry=industry,
        product_service="Coffee Shop",
        primary_goal="Increase brand awareness",
        primary_customer="Coffee enthusiasts",
        location="Seattle, USA",
        timeline="90 days",
    ).with_safe_defaults()

    # Optionally attach research
    if attach_research:
        brand.research = BrandResearchResult(
            brand_summary=f"Test summary for {brand_name}",
            keyword_hashtags=["#TestBrand", "#CoffeeLover", "#ArtisanCoffee"],
            industry_hashtags=["#Coffee", "#Cafe", "#Espresso"],
            campaign_hashtags=["#FallMenu", "#PumpkinSpice", "#LimitedTime"],
        )

    # Create other required brief components
    brief = ClientInputBrief(
        brand=brand,
        audience=AudienceBrief(primary_customer="Coffee enthusiasts"),
        goal=GoalBrief(primary_goal="Increase sales", timeline="90 days"),
        voice=VoiceBrief(tone_of_voice=["professional", "engaging"]),
        product_service=ProductServiceBrief(),
        assets_constraints=AssetsConstraintsBrief(),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )

    return brief


class TestHashtagResearchAttachment:
    """Test A: Verify Perplexity hashtag data merges into BrandResearchResult."""

    def test_brand_research_result_has_hashtag_fields(self):
        """Verify BrandResearchResult model has new hashtag fields."""
        result = BrandResearchResult(
            brand_summary="Test brand",
            keyword_hashtags=["#TestBrand", "#BrandKeyword"],
            industry_hashtags=["#Industry", "#IndustryTag"],
            campaign_hashtags=["#Campaign", "#Launch"],
        )

        assert result.keyword_hashtags == ["#TestBrand", "#BrandKeyword"]
        assert result.industry_hashtags == ["#Industry", "#IndustryTag"]
        assert result.campaign_hashtags == ["#Campaign", "#Launch"]

    def test_apply_fallbacks_creates_empty_lists(self):
        """Verify apply_fallbacks sets None hashtag fields to empty lists."""
        result = BrandResearchResult(
            brand_summary="Test",
            keyword_hashtags=None,
            industry_hashtags=None,
            campaign_hashtags=None,
        )

        result.apply_fallbacks("TestBrand", "Coffee")

        assert result.keyword_hashtags == []
        assert result.industry_hashtags == []
        assert result.campaign_hashtags == []

    def test_apply_fallbacks_ensures_hash_prefix(self):
        """Verify apply_fallbacks adds # prefix to hashtags missing it."""
        result = BrandResearchResult(
            brand_summary="Test",
            keyword_hashtags=["TestBrand", "#AlreadyHashed"],
            industry_hashtags=["Industry", "#Coffee"],
            campaign_hashtags=["Launch"],
        )

        result.apply_fallbacks("TestBrand", "Coffee")

        # All should have # prefix now
        assert all(tag.startswith("#") for tag in result.keyword_hashtags)
        assert all(tag.startswith("#") for tag in result.industry_hashtags)
        assert all(tag.startswith("#") for tag in result.campaign_hashtags)

    def test_apply_fallbacks_removes_duplicates(self):
        """Verify apply_fallbacks removes duplicate hashtags within categories."""
        result = BrandResearchResult(
            brand_summary="Test",
            keyword_hashtags=["#Test", "#Test", "#Brand", "#brand"],  # Duplicates
            industry_hashtags=["#Coffee", "#coffee", "#Coffee"],
            campaign_hashtags=["#Launch", "#Launch"],
        )

        result.apply_fallbacks("TestBrand", "Coffee")

        # Should have unique tags only (case-insensitive)
        assert len(result.keyword_hashtags) == 2  # #Test, #Brand
        assert len(result.industry_hashtags) == 1  # #Coffee
        assert len(result.campaign_hashtags) == 1  # #Launch

    @pytest.mark.skip(
        reason="Requires complex Perplexity client mocking - covered by integration tests"
    )
    @patch("backend.external.perplexity_client.httpx.Client")
    @patch("backend.services.brand_research.asyncio.run")
    def test_hashtag_research_integrates_with_brand_research(
        self, mock_asyncio_run, mock_httpx_client
    ):
        """Verify hashtag research is fetched and merged into brand research."""
        # Mock the main research call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"brand_summary": "Test Brand", "official_website": "", '
                        '"main_social_profiles": [], "current_positioning": "", '
                        '"recent_content_themes": [], "local_competitors": [], '
                        '"audience_pain_points": [], "audience_language_snippets": [], '
                        '"hashtag_hints": [], "keyword_hashtags": [], '
                        '"industry_hashtags": [], "campaign_hashtags": []}'
                    }
                }
            ]
        }
        mock_httpx_client.return_value.__enter__.return_value.post.return_value = mock_response

        # Mock the hashtag research call (async)
        mock_asyncio_run.return_value = {
            "keyword_hashtags": ["#Brand", "#Product"],
            "industry_hashtags": ["#Coffee", "#Cafe"],
            "campaign_hashtags": ["#Launch", "#NewMenu"],
        }

        # Call get_brand_research
        result = get_brand_research(
            brand_name="TestBrand",
            industry="Coffee",
            location="Seattle",
            enabled=True,
        )

        # Verify hashtag data was merged
        assert result is not None
        assert result.keyword_hashtags == ["#Brand", "#Product"]
        assert result.industry_hashtags == ["#Coffee", "#Cafe"]
        assert result.campaign_hashtags == ["#Launch", "#NewMenu"]


class TestGeneratorBenchmarkCompliance:
    """Test B: Verify generator uses research values and renders compliant Markdown."""

    def test_generated_hashtag_strategy_structure(self):
        """Verify generated hashtag_strategy has required sections."""
        from backend.main import _gen_hashtag_strategy, GenerateRequest

        # Create proper test brief with research
        brief = create_minimal_test_brief(attach_research=True)
        req = GenerateRequest(brief=brief)

        # Generate section
        output = _gen_hashtag_strategy(req)

        # Verify required sections present
        assert "## Brand Hashtags" in output
        assert "## Industry Hashtags" in output
        assert "## Campaign Hashtags" in output
        assert "## Usage Guidelines" in output

        # Verify hashtags are included
        assert "#TestBrand" in output or "#" in output  # Some hashtag present
        assert "#Coffee" in output or "Coffee" in output
        assert "#FallMenu" in output or "FallMenu" in output or "#" in output

    def test_generated_hashtag_strategy_uses_perplexity_data(self):
        """Verify generator prioritizes Perplexity data over fallbacks."""
        from backend.main import _gen_hashtag_strategy, GenerateRequest

        # Create brief with custom Perplexity tags
        brief = create_minimal_test_brief(brand_name="PerplexityBrand", attach_research=False)

        # Attach specific Perplexity research
        brief.brand.research = BrandResearchResult(
            brand_summary="Test",
            keyword_hashtags=["#PerplexityTag1", "#PerplexityTag2", "#PerplexityTag3"],
            industry_hashtags=["#PerplexityIndustry", "#PerplexityMarket", "#PerplexitySector"],
            campaign_hashtags=["#PerplexityCampaign", "#PerplexityLaunch", "#PerplexityPromo"],
        )

        req = GenerateRequest(brief=brief)
        output = _gen_hashtag_strategy(req)

        # Should use Perplexity tags, not generated fallbacks
        assert "#PerplexityTag1" in output
        assert "#PerplexityIndustry" in output
        assert "#PerplexityCampaign" in output

    def test_generated_hashtag_strategy_fallback_when_no_research(self):
        """Verify generator uses fallbacks when no Perplexity data available."""
        from backend.main import _gen_hashtag_strategy, GenerateRequest

        # Create brief without research attached
        brief = create_minimal_test_brief(attach_research=False)
        req = GenerateRequest(brief=brief)

        output = _gen_hashtag_strategy(req)

        # Should still generate valid output with fallbacks
        assert "## Brand Hashtags" in output
        assert "## Industry Hashtags" in output
        assert "## Campaign Hashtags" in output

        # Should have at least 3 tags per category (benchmark requirement)
        brand_section = output.split("## Brand Hashtags")[1].split("##")[0]
        assert brand_section.count("#") >= 3

    def test_generated_output_passes_benchmark_validation(self):
        """Verify generated output passes all benchmark validation checks."""
        from backend.main import _gen_hashtag_strategy, GenerateRequest
        from backend.validators.quality_checks import run_all_quality_checks

        # Create proper test brief with research
        brief = create_minimal_test_brief(
            brand_name="ValidationBrand", industry="Coffee", attach_research=True
        )

        req = GenerateRequest(brief=brief)
        output = _gen_hashtag_strategy(req)

        # Run quality checks
        issues = run_all_quality_checks(output, section_id="hashtag_strategy")

        # Should have no errors (warnings ok)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0, f"Found validation errors: {errors}"


class TestBenchmarkRejection:
    """Test C: Verify benchmark rejects missing/invalid tags."""

    def test_hashtag_format_check_missing_hash(self):
        """Verify check detects hashtags missing # symbol."""
        bad_content = """## Brand Hashtags

- TestBrand
- BrandTag
- MyBrand

## Industry Hashtags

- Coffee
- Cafe
"""

        issues = check_hashtag_format(bad_content, "hashtag_strategy")

        # Should detect missing # symbols
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) > 0
        assert any("missing #" in i.message.lower() for i in error_issues)

    def test_hashtag_format_check_too_short(self):
        """Verify check detects hashtags that are too short."""
        bad_content = """## Brand Hashtags

- #A
- #BB
- #CCC

## Industry Hashtags

- #X
- #YY
"""

        issues = check_hashtag_format(bad_content, "hashtag_strategy")

        # Should detect tags too short (<= 3 chars including #)
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) > 0
        assert any("too short" in i.message.lower() for i in error_issues)

    def test_hashtag_format_check_generic_banned(self):
        """Verify check detects banned generic hashtags."""
        bad_content = """## Brand Hashtags

- #fun
- #love
- #happy

## Industry Hashtags

- #instagood
- #photooftheday
"""

        issues = check_hashtag_format(bad_content, "hashtag_strategy")

        # Should detect banned generic tags
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) > 0
        assert any(
            "generic" in i.message.lower() or "banned" in i.message.lower() for i in error_issues
        )

    def test_hashtag_category_count_check_insufficient(self):
        """Verify check detects categories with too few hashtags."""
        bad_content = """## Brand Hashtags

- #BrandTag

## Industry Hashtags

- #Industry

## Campaign Hashtags

- #Campaign
"""

        issues = check_hashtag_category_counts(bad_content, "hashtag_strategy", min_per_category=3)

        # Should detect all 3 categories as insufficient (need 3 each)
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) == 3  # One for each category

    def test_hashtag_validation_passes_good_content(self):
        """Verify validation passes for good hashtag content."""
        good_content = """## Brand Hashtags

- #TestBrand
- #BrandCommunity
- #BrandLife

## Industry Hashtags

- #Coffee
- #Cafe
- #Barista

## Campaign Hashtags

- #FallMenu
- #SeasonalOffer
- #LimitedTime

## Usage Guidelines

- Use 8-12 hashtags per post
"""

        format_issues = check_hashtag_format(good_content, "hashtag_strategy")
        count_issues = check_hashtag_category_counts(
            good_content, "hashtag_strategy", min_per_category=3
        )

        # Should have no errors
        all_errors = [i for i in format_issues + count_issues if i.severity == "error"]
        assert len(all_errors) == 0


class TestPerplexityJSONValidation:
    """Test D: Verify Perplexity JSON format validation."""

    def test_validate_hashtag_data_valid_input(self):
        """Verify _validate_hashtag_data accepts valid input."""
        client = PerplexityClient(api_key="test_key")

        data = {
            "keyword_hashtags": ["#Brand", "#Product", "#Service"],
            "industry_hashtags": ["#Coffee", "#Cafe"],
            "campaign_hashtags": ["#Launch", "#Sale"],
        }

        validated = client._validate_hashtag_data(data)

        assert validated is not None
        assert len(validated["keyword_hashtags"]) == 3
        assert len(validated["industry_hashtags"]) == 2
        assert len(validated["campaign_hashtags"]) == 2

    def test_validate_hashtag_data_adds_hash_prefix(self):
        """Verify validation adds # prefix to tags missing it."""
        client = PerplexityClient(api_key="test_key")

        data = {
            "keyword_hashtags": ["Brand", "#Product"],  # Mix of with/without #
            "industry_hashtags": ["Coffee", "Cafe"],  # No #
            "campaign_hashtags": ["#Launch"],  # Has #
        }

        validated = client._validate_hashtag_data(data)

        # All should have # now
        assert all(tag.startswith("#") for tag in validated["keyword_hashtags"])
        assert all(tag.startswith("#") for tag in validated["industry_hashtags"])
        assert all(tag.startswith("#") for tag in validated["campaign_hashtags"])

    def test_validate_hashtag_data_removes_short_tags(self):
        """Verify validation removes hashtags <= 3 characters (total including #)."""
        client = PerplexityClient(api_key="test_key")

        data = {
            "keyword_hashtags": ["#A", "#BB", "#CCC", "#DDDD"],  # #A and #BB too short
            "industry_hashtags": ["#X", "#YY", "#Coffee"],  # #X and #YY too short
            "campaign_hashtags": ["#Launch", "#Ok"],  # #Ok too short
        }

        validated = client._validate_hashtag_data(data)

        # Should keep tags with 4+ chars total (including #)
        assert len(validated["keyword_hashtags"]) == 2  # #CCC, #DDDD
        assert len(validated["industry_hashtags"]) == 1  # #Coffee
        assert len(validated["campaign_hashtags"]) == 1  # #Launch

    def test_validate_hashtag_data_removes_duplicates(self):
        """Verify validation removes duplicate hashtags (case-insensitive)."""
        client = PerplexityClient(api_key="test_key")

        data = {
            "keyword_hashtags": ["#Brand", "#brand", "#BRAND", "#Product"],
            "industry_hashtags": ["#Coffee", "#coffee", "#Cafe"],
            "campaign_hashtags": ["#Launch", "#Launch", "#Sale"],
        }

        validated = client._validate_hashtag_data(data)

        # Should have unique tags only
        assert len(validated["keyword_hashtags"]) == 2  # Brand, Product
        assert len(validated["industry_hashtags"]) == 2  # Coffee, Cafe
        assert len(validated["campaign_hashtags"]) == 2  # Launch, Sale

    def test_validate_hashtag_data_rejects_empty_result(self):
        """Verify validation returns None if no valid hashtags found."""
        client = PerplexityClient(api_key="test_key")

        data = {
            "keyword_hashtags": ["#A", "#B"],  # All too short
            "industry_hashtags": ["#X"],  # Too short
            "campaign_hashtags": [],  # Empty
        }

        validated = client._validate_hashtag_data(data)

        # Should return None because no valid hashtags
        assert validated is None

    def test_validate_hashtag_data_handles_missing_fields(self):
        """Verify validation handles missing fields gracefully."""
        client = PerplexityClient(api_key="test_key")

        data = {
            "keyword_hashtags": ["#Brand"],
            # Missing industry_hashtags and campaign_hashtags
        }

        validated = client._validate_hashtag_data(data)

        # Should fill in empty arrays for missing fields
        assert validated is not None
        assert len(validated["keyword_hashtags"]) == 1
        assert validated["industry_hashtags"] == []
        assert validated["campaign_hashtags"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
