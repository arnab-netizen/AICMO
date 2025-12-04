"""
Tests for ResearchService - Perplexity research orchestration layer.

These tests validate:
1. Comprehensive research data fetching with all sources
2. Graceful fallback when Perplexity is unavailable
3. Configuration flag handling (AICMO_PERPLEXITY_ENABLED)
4. Data structure integrity (ComprehensiveResearchData)
5. Individual research method behaviors
"""

import pytest
from unittest.mock import Mock, patch
from backend.services.research_service import (
    ResearchService,
    ComprehensiveResearchData,
    CompetitorResearchResult,
    AudienceInsightsResult,
    MarketTrendsResult,
)
from backend.research_models import BrandResearchResult


class TestResearchServiceInitialization:
    """Test ResearchService initialization and configuration."""

    def test_init_creates_client(self):
        """ResearchService should initialize PerplexityClient."""
        service = ResearchService()
        assert service.client is not None

    def test_init_respects_config(self):
        """ResearchService should respect configuration flags."""
        with patch("backend.services.research_service.os.getenv") as mock_env:
            mock_env.return_value = "false"
            service = ResearchService()
            # Service should still initialize but may skip calls
            assert service is not None


class TestComprehensiveResearchData:
    """Test ComprehensiveResearchData dataclass and helper methods."""

    def test_empty_research_is_detected(self):
        """Empty research data should be correctly identified."""
        empty = ComprehensiveResearchData()
        assert empty.is_empty() is True
        assert empty.has_brand_data() is False
        assert empty.has_competitor_data() is False

    def test_brand_data_detection(self):
        """Brand research data should be correctly detected."""
        brand_result = BrandResearchResult(
            brand_name="TestBrand",
            industry="Tech",
            description="Test description",
            recent_content_themes=["AI", "Innovation"],
            hashtag_brand=["#testbrand"],
            hashtag_industry=["#tech"],
            hashtag_campaign=["#launch"],
        )
        research = ComprehensiveResearchData(brand=brand_result)
        assert research.has_brand_data() is True
        assert research.is_empty() is False

    def test_competitor_data_detection(self):
        """Competitor data should be correctly detected."""
        competitor = CompetitorResearchResult(
            competitors=["Competitor A", "Competitor B"],
            summaries={"Competitor A": "Leading player"},
        )
        research = ComprehensiveResearchData(local_competitors=competitor)
        assert research.has_competitor_data() is True
        assert research.is_empty() is False


class TestResearchServiceFetchComprehensive:
    """Test main fetch_comprehensive_research() method."""

    @patch("backend.services.research_service.PerplexityClient")
    @patch("backend.services.research_service.is_stub_mode")
    def test_fetch_comprehensive_success(self, mock_stub, mock_client_class):
        """Should fetch all research data successfully when enabled."""
        mock_stub.return_value = False

        # Mock PerplexityClient instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock brand research response
        mock_brand_result = BrandResearchResult(
            brand_name="TestBrand",
            industry="Tech",
            description="Test description",
            recent_content_themes=["AI"],
            hashtag_brand=["#test"],
            hashtag_industry=["#tech"],
            hashtag_campaign=["#launch"],
        )
        mock_client.research_brand.return_value = mock_brand_result

        # Create mock brief
        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"
        mock_brief.brand.description = "A test brand"

        service = ResearchService()
        service.client = mock_client  # Inject mock

        result = service.fetch_comprehensive_research(mock_brief)

        assert result is not None
        assert isinstance(result, ComprehensiveResearchData)
        assert result.brand == mock_brand_result

    @patch("backend.services.research_service.is_stub_mode")
    def test_fetch_comprehensive_stub_mode(self, mock_stub):
        """Should return empty data in stub mode."""
        mock_stub.return_value = True

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"

        service = ResearchService()
        result = service.fetch_comprehensive_research(mock_brief)

        assert result is not None
        assert isinstance(result, ComprehensiveResearchData)
        assert result.is_empty() is True

    @patch("backend.services.research_service.PerplexityClient")
    @patch("backend.services.research_service.is_stub_mode")
    def test_fetch_comprehensive_handles_client_failure(self, mock_stub, mock_client_class):
        """Should gracefully handle Perplexity client failures."""
        mock_stub.return_value = False

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.research_brand.side_effect = Exception("API Error")

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"
        mock_brief.brand.description = "Test"

        service = ResearchService()
        service.client = mock_client

        # Should not raise, should return empty or partial data
        result = service.fetch_comprehensive_research(mock_brief)
        assert result is not None
        assert isinstance(result, ComprehensiveResearchData)


class TestResearchServiceBrandResearch:
    """Test _fetch_brand_research() method."""

    @patch("backend.services.research_service.PerplexityClient")
    def test_fetch_brand_research_success(self, mock_client_class):
        """Should fetch brand research successfully."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_result = BrandResearchResult(
            brand_name="TestBrand",
            industry="Tech",
            description="Test",
            recent_content_themes=["AI"],
            hashtag_brand=["#test"],
            hashtag_industry=["#tech"],
            hashtag_campaign=["#launch"],
        )
        mock_client.research_brand.return_value = mock_result

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"
        mock_brief.brand.description = "Test description"

        service = ResearchService()
        service.client = mock_client

        result = service._fetch_brand_research(mock_brief)

        assert result == mock_result
        mock_client.research_brand.assert_called_once()

    @patch("backend.services.research_service.PerplexityClient")
    def test_fetch_brand_research_handles_error(self, mock_client_class):
        """Should return None on error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.research_brand.side_effect = Exception("API Error")

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"

        service = ResearchService()
        service.client = mock_client

        result = service._fetch_brand_research(mock_brief)
        assert result is None


class TestResearchServiceCompetitorResearch:
    """Test _fetch_competitor_research() method."""

    @patch("backend.services.research_service.PerplexityClient")
    def test_fetch_competitor_research_returns_structure(self, mock_client_class):
        """Should return CompetitorResearchResult structure."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock API response with competitor data
        mock_client.chat.return_value = "Competitor A: Leading player\nCompetitor B: Challenger"

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"

        service = ResearchService()
        service.client = mock_client

        result = service._fetch_competitor_research(mock_brief)

        # Should return a result (may be empty if parsing fails, but should not crash)
        assert result is not None
        assert isinstance(result, CompetitorResearchResult)


class TestResearchServiceAudienceInsights:
    """Test _fetch_audience_insights() method."""

    def test_fetch_audience_insights_returns_structure(self):
        """Should return AudienceInsightsResult structure."""
        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.audience.primary_customer = "Tech professionals"

        service = ResearchService()
        result = service._fetch_audience_insights(mock_brief)

        assert result is not None
        assert isinstance(result, AudienceInsightsResult)


class TestResearchServiceMarketTrends:
    """Test _fetch_market_trends() method."""

    def test_fetch_market_trends_returns_structure(self):
        """Should return MarketTrendsResult structure."""
        mock_brief = Mock()
        mock_brief.brand.industry = "Tech"

        service = ResearchService()
        result = service._fetch_market_trends(mock_brief)

        assert result is not None
        assert isinstance(result, MarketTrendsResult)


class TestResearchServiceIntegration:
    """Integration tests for full research pipeline."""

    @patch("backend.services.research_service.PerplexityClient")
    @patch("backend.services.research_service.is_stub_mode")
    def test_full_pipeline_with_all_data(self, mock_stub, mock_client_class):
        """Should orchestrate all research sources successfully."""
        mock_stub.return_value = False

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock successful responses
        mock_brand = BrandResearchResult(
            brand_name="TestBrand",
            industry="Tech",
            description="Test",
            recent_content_themes=["AI", "Innovation"],
            hashtag_brand=["#testbrand"],
            hashtag_industry=["#tech"],
            hashtag_campaign=["#launch"],
        )
        mock_client.research_brand.return_value = mock_brand

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"
        mock_brief.brand.description = "Test brand"
        mock_brief.audience.primary_customer = "Tech users"

        service = ResearchService()
        service.client = mock_client

        result = service.fetch_comprehensive_research(mock_brief)

        # Should have populated data
        assert result is not None
        assert result.has_brand_data() is True
        assert result.brand.brand_name == "TestBrand"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
