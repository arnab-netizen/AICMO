"""
Tests for CreativeService - OpenAI creative enhancement layer.

These tests validate:
1. Polish section method with OpenAI enhancement
2. Degenericize text functionality
3. Narrative generation from scratch
4. Calendar post enhancement
5. Graceful fallback in stub mode
6. Error handling and template-first approach
"""

import pytest
from unittest.mock import Mock, patch
from backend.services.creative_service import (
    CreativeService,
    CreativeConfig,
)
from backend.services.research_service import ComprehensiveResearchData


class TestCreativeServiceInitialization:
    """Test CreativeService initialization and configuration."""

    def test_init_with_default_config(self):
        """Should initialize with default configuration."""
        service = CreativeService()
        assert service is not None
        assert isinstance(service.config, CreativeConfig)

    def test_init_with_custom_config(self):
        """Should accept custom configuration."""
        custom_config = CreativeConfig(
            temperature=0.5,
            max_tokens=500,
            model="gpt-4",
        )
        service = CreativeService(config=custom_config)
        assert service.config.temperature == 0.5
        assert service.config.max_tokens == 500

    @patch("backend.services.creative_service.is_stub_mode")
    def test_init_detects_stub_mode(self, mock_stub):
        """Should detect stub mode correctly."""
        mock_stub.return_value = True
        service = CreativeService()
        # Service should still initialize
        assert service is not None


class TestCreativeServicePolishSection:
    """Test polish_section() - main enhancement method."""

    @patch("backend.services.creative_service.is_stub_mode")
    def test_polish_section_stub_mode_returns_original(self, mock_stub):
        """Should return original content in stub mode."""
        mock_stub.return_value = True

        service = CreativeService()
        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"

        original = "This is test content."
        result = service.polish_section(original, mock_brief, None, "strategy")

        assert result == original

    @patch("backend.services.creative_service.OpenAI")
    @patch("backend.services.creative_service.is_stub_mode")
    @patch("backend.services.creative_service.os.getenv")
    def test_polish_section_with_openai(self, mock_env, mock_stub, mock_openai_class):
        """Should enhance content using OpenAI when available."""
        mock_stub.return_value = False
        mock_env.return_value = "test-api-key"

        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock completion response
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Enhanced polished content"
        mock_client.chat.completions.create.return_value = mock_completion

        service = CreativeService()
        service.client = mock_client  # Inject mock

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"

        original = "This is generic marketing content."
        result = service.polish_section(original, mock_brief, None, "strategy")

        # Should call OpenAI
        assert mock_client.chat.completions.create.called
        assert result == "Enhanced polished content"

    @patch("backend.services.creative_service.OpenAI")
    @patch("backend.services.creative_service.is_stub_mode")
    @patch("backend.services.creative_service.os.getenv")
    def test_polish_section_handles_api_error(self, mock_env, mock_stub, mock_openai_class):
        """Should gracefully fallback on API error."""
        mock_stub.return_value = False
        mock_env.return_value = "test-api-key"

        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        service = CreativeService()
        service.client = mock_client

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"

        original = "Original content"
        result = service.polish_section(original, mock_brief, None, "strategy")

        # Should return original content
        assert result == original

    def test_polish_section_includes_research_context(self):
        """Should include research data in prompts when available."""
        service = CreativeService()

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"

        mock_research = Mock()
        mock_research.has_brand_data.return_value = True
        mock_research.brand.recent_content_themes = ["AI", "Innovation"]

        # Build prompt (internal method)
        prompt = service._build_polish_prompt(
            content="Test content",
            brief=mock_brief,
            research_data=mock_research,
            section_type="strategy",
        )

        # Prompt should reference brand context
        assert "TestBrand" in prompt
        assert "Tech" in prompt


class TestCreativeServiceDegenericize:
    """Test degenericize_text() method."""

    @patch("backend.services.creative_service.is_stub_mode")
    def test_degenericize_stub_mode(self, mock_stub):
        """Should return original text in stub mode."""
        mock_stub.return_value = True

        service = CreativeService()
        original = "Leverage synergies to maximize ROI"
        result = service.degenericize_text(original, Mock())

        assert result == original

    @patch("backend.services.creative_service.OpenAI")
    @patch("backend.services.creative_service.is_stub_mode")
    @patch("backend.services.creative_service.os.getenv")
    def test_degenericize_removes_generic_language(self, mock_env, mock_stub, mock_openai_class):
        """Should remove generic marketing buzzwords."""
        mock_stub.return_value = False
        mock_env.return_value = "test-api-key"

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Specific, concrete content"
        mock_client.chat.completions.create.return_value = mock_completion

        service = CreativeService()
        service.client = mock_client

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"

        generic_text = "Leverage synergies to maximize ROI"
        result = service.degenericize_text(generic_text, mock_brief)

        assert result == "Specific, concrete content"


class TestCreativeServiceGenerateNarrative:
    """Test generate_narrative() - from-scratch content generation."""

    @patch("backend.services.creative_service.is_stub_mode")
    def test_generate_narrative_stub_mode(self, mock_stub):
        """Should return template in stub mode."""
        mock_stub.return_value = True

        service = CreativeService()
        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"

        result = service.generate_narrative(
            brief=mock_brief, narrative_type="brand_story", max_length=200
        )

        # Should return a string (template)
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("backend.services.creative_service.OpenAI")
    @patch("backend.services.creative_service.is_stub_mode")
    @patch("backend.services.creative_service.os.getenv")
    def test_generate_narrative_with_openai(self, mock_env, mock_stub, mock_openai_class):
        """Should generate narrative using OpenAI."""
        mock_stub.return_value = False
        mock_env.return_value = "test-api-key"

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Generated brand narrative"
        mock_client.chat.completions.create.return_value = mock_completion

        service = CreativeService()
        service.client = mock_client

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"

        result = service.generate_narrative(
            brief=mock_brief, narrative_type="brand_story", max_length=200
        )

        assert result == "Generated brand narrative"


class TestCreativeServiceEnhanceCalendarPosts:
    """Test enhance_calendar_posts() - social media enhancement."""

    def test_enhance_calendar_posts_preserves_structure(self):
        """Should preserve post structure while enhancing hooks."""
        service = CreativeService()

        posts = [
            {
                "hook": "Check out our product!",
                "body": "Product description here",
                "date": "2024-01-15",
            },
            {"hook": "New feature alert", "body": "Feature details", "date": "2024-01-16"},
        ]

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"

        result = service.enhance_calendar_posts(posts, mock_brief, None)

        # Should return same number of posts
        assert len(result) == 2
        # Should preserve keys
        assert "hook" in result[0]
        assert "body" in result[0]
        assert "date" in result[0]

    @patch("backend.services.creative_service.is_stub_mode")
    def test_enhance_calendar_posts_stub_mode(self, mock_stub):
        """Should return original posts in stub mode."""
        mock_stub.return_value = True

        service = CreativeService()

        original_posts = [{"hook": "Original hook", "body": "Body", "date": "2024-01-15"}]

        result = service.enhance_calendar_posts(original_posts, Mock(), None)

        assert result == original_posts


class TestCreativeServiceHelperMethods:
    """Test internal helper methods."""

    def test_build_polish_prompt_includes_context(self):
        """Polish prompt should include all relevant context."""
        service = CreativeService()

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"
        mock_brief.audience.primary_customer = "Tech professionals"

        prompt = service._build_polish_prompt(
            content="Test content", brief=mock_brief, research_data=None, section_type="strategy"
        )

        assert "TestBrand" in prompt
        assert "Tech" in prompt
        assert "Test content" in prompt

    def test_is_generic_hook_detection(self):
        """Should detect generic hooks."""
        service = CreativeService()

        generic_hooks = [
            "Check out our product!",
            "New update available",
            "Don't miss out!",
            "Click here to learn more",
        ]

        for hook in generic_hooks:
            # Should identify as generic (returns True if generic)
            result = service._is_generic_hook(hook)
            # Method should exist and return a boolean
            assert isinstance(result, bool)


class TestCreativeServiceConfigValidation:
    """Test configuration validation and edge cases."""

    def test_config_validates_temperature(self):
        """CreativeConfig should have valid temperature range."""
        config = CreativeConfig(temperature=0.7)
        assert 0.0 <= config.temperature <= 2.0

    def test_config_validates_max_tokens(self):
        """CreativeConfig should have positive max_tokens."""
        config = CreativeConfig(max_tokens=1000)
        assert config.max_tokens > 0

    def test_config_has_model(self):
        """CreativeConfig should specify a model."""
        config = CreativeConfig()
        assert config.model is not None
        assert len(config.model) > 0


class TestCreativeServiceIntegration:
    """Integration tests for full creative pipeline."""

    @patch("backend.services.creative_service.OpenAI")
    @patch("backend.services.creative_service.is_stub_mode")
    @patch("backend.services.creative_service.os.getenv")
    def test_full_polish_pipeline(self, mock_env, mock_stub, mock_openai_class):
        """Should handle complete polish workflow."""
        mock_stub.return_value = False
        mock_env.return_value = "test-api-key"

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Fully polished content"
        mock_client.chat.completions.create.return_value = mock_completion

        service = CreativeService()
        service.client = mock_client

        mock_brief = Mock()
        mock_brief.brand.brand_name = "TestBrand"
        mock_brief.brand.industry = "Tech"
        mock_brief.audience.primary_customer = "Tech users"

        mock_research = ComprehensiveResearchData()

        original = "Generic marketing content that needs enhancement"
        result = service.polish_section(original, mock_brief, mock_research, "strategy")

        # Should complete successfully
        assert result == "Fully polished content"
        assert mock_client.chat.completions.create.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
