"""
Test suite for industry-specific configuration (FIX #4).

Tests that industry configurations provide:
- Correct primary/secondary channels per industry
- Default personas appropriate for each industry
- Messaging tone tailored to industry
- Content format recommendations

Run: pytest tests/test_industry_alignment.py -v
"""

import pytest
from backend.industry_config import (
    get_industry_config,
    get_primary_channel_for_industry,
    get_default_personas_for_industry,
    INDUSTRY_CONFIGS,
)


class TestIndustryConfigLoading:
    """Tests for loading industry configurations."""

    def test_all_industries_defined(self):
        """Test that all expected industries are defined."""
        expected_industries = [
            "food_beverage",
            "boutique_retail",
            "saas",
            "fitness",
            "ecommerce",
        ]

        for industry in expected_industries:
            assert industry in INDUSTRY_CONFIGS
            config = INDUSTRY_CONFIGS[industry]
            assert "industry_key" in config
            assert "display_name" in config
            assert "channels" in config
            assert "default_personas" in config

    def test_industry_config_structure(self):
        """Test that each industry config has required fields."""
        required_fields = [
            "industry_key",
            "display_name",
            "channels",
            "default_personas",
            "messaging_tone",
            "content_formats",
        ]

        for industry_key, config in INDUSTRY_CONFIGS.items():
            for field in required_fields:
                assert field in config, f"{industry_key} missing {field}"

    def test_channel_config_structure(self):
        """Test that each industry's channel config is complete."""
        required_channel_fields = ["primary", "secondary", "tertiary", "avoid", "reasoning"]

        for industry_key, config in INDUSTRY_CONFIGS.items():
            channels = config["channels"]
            for field in required_channel_fields:
                assert field in channels, f"{industry_key} channels missing {field}"
                if field != "reasoning":
                    # primary should be string, secondary/tertiary/avoid should be lists
                    if field == "primary":
                        assert isinstance(channels[field], str)
                    else:
                        assert isinstance(channels[field], list)


class TestGetIndustryConfig:
    """Tests for get_industry_config function."""

    def test_exact_key_match(self):
        """Test exact industry key match."""
        config = get_industry_config("saas")
        assert config is not None
        assert config["industry_key"] == "saas"

    def test_display_name_match(self):
        """Test matching by display name."""
        config = get_industry_config("SaaS & B2B Software")
        assert config is not None
        assert config["industry_key"] == "saas"

    def test_partial_keyword_match(self):
        """Test partial keyword matching."""
        config = get_industry_config("food")
        assert config is not None
        assert config["industry_key"] == "food_beverage"

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        config1 = get_industry_config("SAAS")
        config2 = get_industry_config("SaaS")
        config3 = get_industry_config("saas")

        assert config1 == config2 == config3

    def test_unknown_industry_returns_none(self):
        """Test that unknown industry returns None."""
        config = get_industry_config("unknown_industry_xyz")
        assert config is None

    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        config = get_industry_config(None)
        assert config is None


class TestPrimaryChannelSelection:
    """Tests for primary channel selection per industry."""

    def test_food_beverage_primary_channel(self):
        """Test that F&B primary is Instagram."""
        channel = get_primary_channel_for_industry("food_beverage")
        assert channel == "Instagram"

    def test_saas_primary_channel(self):
        """Test that SaaS primary is LinkedIn."""
        channel = get_primary_channel_for_industry("saas")
        assert channel == "LinkedIn"

    def test_boutique_retail_primary_channel(self):
        """Test that retail primary is Instagram."""
        channel = get_primary_channel_for_industry("boutique_retail")
        assert channel == "Instagram"

    def test_fitness_primary_channel(self):
        """Test that fitness primary is Instagram."""
        channel = get_primary_channel_for_industry("fitness")
        assert channel == "Instagram"

    def test_ecommerce_primary_channel(self):
        """Test that ecommerce primary is Instagram."""
        channel = get_primary_channel_for_industry("ecommerce")
        assert channel == "Instagram"

    def test_unknown_industry_returns_none(self):
        """Test that unknown industry returns None."""
        channel = get_primary_channel_for_industry("unknown")
        assert channel is None


class TestDefaultPersonas:
    """Tests for default persona selection per industry."""

    def test_each_industry_has_personas(self):
        """Test that each industry has default personas."""
        for industry_key in INDUSTRY_CONFIGS.keys():
            personas = get_default_personas_for_industry(industry_key)
            assert isinstance(personas, list)
            assert len(personas) > 0

    def test_persona_structure(self):
        """Test that each persona has required fields."""
        required_persona_fields = [
            "name",
            "role",
            "age_range",
            "primary_pain_points",
            "primary_goals",
            "decision_factors",
            "channel_preference",
        ]

        for industry_key in INDUSTRY_CONFIGS.keys():
            personas = INDUSTRY_CONFIGS[industry_key]["default_personas"]
            for persona in personas:
                for field in required_persona_fields:
                    assert field in persona, f"Persona missing {field} in {industry_key}"

    def test_food_beverage_personas(self):
        """Test F&B industry has appropriate personas."""
        personas = get_default_personas_for_industry("food_beverage")

        # Should have at least 2 personas (foodie + local)
        assert len(personas) >= 2

        # Check persona preferences are Instagram/TikTok focused
        channel_prefs = [p.get("channel_preference", "").lower() for p in personas]
        assert any("instagram" in pref or "tiktok" in pref for pref in channel_prefs)

    def test_saas_personas(self):
        """Test SaaS industry has appropriate personas."""
        personas = get_default_personas_for_industry("saas")

        # Should have at least 2 personas (VP + Developer)
        assert len(personas) >= 2

        # Check that personas mention ROI/technical concerns
        all_text = str(personas).lower()
        assert "roi" in all_text or "technical" in all_text or "integration" in all_text


class TestMessagingTone:
    """Tests for messaging tone recommendations."""

    def test_each_industry_has_tone(self):
        """Test that each industry has messaging tone defined."""
        for industry_key in INDUSTRY_CONFIGS.keys():
            config = INDUSTRY_CONFIGS[industry_key]
            assert "messaging_tone" in config
            assert isinstance(config["messaging_tone"], str)
            assert len(config["messaging_tone"]) > 0

    def test_tone_is_descriptive(self):
        """Test that tones are descriptive (multiple words)."""
        for industry_key in INDUSTRY_CONFIGS.keys():
            tone = INDUSTRY_CONFIGS[industry_key]["messaging_tone"]
            # Should be multiple tone descriptors
            assert len(tone.split(",")) >= 2


class TestContentFormats:
    """Tests for recommended content formats per industry."""

    def test_each_industry_has_formats(self):
        """Test that each industry has content format recommendations."""
        for industry_key in INDUSTRY_CONFIGS.keys():
            config = INDUSTRY_CONFIGS[industry_key]
            assert "content_formats" in config
            assert isinstance(config["content_formats"], list)
            assert len(config["content_formats"]) > 0

    def test_format_recommendations_vary(self):
        """Test that format recommendations vary by industry."""
        # Get all format recommendations
        all_formats = []
        for industry_key in INDUSTRY_CONFIGS.keys():
            formats = INDUSTRY_CONFIGS[industry_key]["content_formats"]
            all_formats.extend(formats)

        # Should have variety (not all the same)
        unique_formats = set(all_formats)
        assert len(unique_formats) > 3  # At least 3 different format types across industries

    def test_social_industries_different_formats(self):
        """Test that visual industries have different formats than B2B."""
        food_bev_config = get_industry_config("food_beverage")
        saas_config = get_industry_config("saas")

        food_formats = set(food_bev_config["content_formats"])
        saas_formats = set(saas_config["content_formats"])

        # Should have significant differences
        # F&B likely has more visual/trending content
        # SaaS likely has more thought leadership content
        diff = food_formats.symmetric_difference(saas_formats)
        assert len(diff) > 0


class TestChannelSecondaryOptions:
    """Tests for secondary and tertiary channel recommendations."""

    def test_channels_are_distinct(self):
        """Test that primary, secondary, tertiary are different."""
        for industry_key in INDUSTRY_CONFIGS.keys():
            config = INDUSTRY_CONFIGS[industry_key]
            primary = config["channels"]["primary"]
            secondary = set(config["channels"]["secondary"])
            tertiary = set(config["channels"]["tertiary"])

            # Primary should not be in secondary or tertiary
            assert primary not in secondary
            assert primary not in tertiary

    def test_secondary_channels_for_fb(self):
        """Test secondary channels for F&B are social platforms."""
        config = get_industry_config("food_beverage")
        secondary = config["channels"]["secondary"]

        # Should include TikTok, Facebook
        secondary_lower = [ch.lower() for ch in secondary]
        assert any("tiktok" in ch for ch in secondary_lower)
        assert any("facebook" in ch for ch in secondary_lower)

    def test_avoid_channels_for_saas(self):
        """Test that SaaS avoids TikTok."""
        config = get_industry_config("saas")
        avoid = [ch.lower() for ch in config["channels"]["avoid"]]

        assert any("tiktok" in ch for ch in avoid)


class TestIndustryAlignment:
    """Integration tests for full industry alignment."""

    def test_fb_industry_alignment(self):
        """Test complete F&B industry alignment."""
        config = get_industry_config("food_beverage")

        # Primary channel should be Instagram
        assert config["channels"]["primary"] == "Instagram"

        # Should have foodie/experience personas
        personas = config["default_personas"]
        persona_names = [p["name"] for p in personas]
        assert any("foodie" in n.lower() or "food" in n.lower() for n in persona_names)

        # Tone should be visual/trendy
        assert (
            "visual" in config["messaging_tone"].lower()
            or "trend" in config["messaging_tone"].lower()
        )

    def test_saas_industry_alignment(self):
        """Test complete SaaS industry alignment."""
        config = get_industry_config("saas")

        # Primary channel should be LinkedIn
        assert config["channels"]["primary"] == "LinkedIn"

        # Should avoid consumer platforms
        avoid_lower = [ch.lower() for ch in config["channels"]["avoid"]]
        assert any("tiktok" in ch for ch in avoid_lower)

        # Tone should mention ROI/thought leadership
        tone_lower = config["messaging_tone"].lower()
        assert "roi" in tone_lower or "professional" in tone_lower or "thought" in tone_lower

    def test_fitness_industry_alignment(self):
        """Test complete fitness industry alignment."""
        config = get_industry_config("fitness")

        # Primary channel should be Instagram
        assert config["channels"]["primary"] == "Instagram"

        # Should have transformation/motivation focus
        tone_lower = config["messaging_tone"].lower()
        assert "motiv" in tone_lower or "transform" in tone_lower or "community" in tone_lower


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
