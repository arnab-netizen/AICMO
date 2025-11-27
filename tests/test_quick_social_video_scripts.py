"""Tests for video script fields in Quick Social Pack."""

import pytest


def test_video_script_fields_schema():
    """Test that video script generator returns proper schema."""
    from backend.generators.social.video_script_generator import generate_video_script_for_day

    result = generate_video_script_for_day(
        brand="Test Brand", industry="Tech", audience="Entrepreneurs", text_topic="Product Launch"
    )

    assert isinstance(result, dict)
    assert "video_hook" in result
    assert "video_body" in result
    assert "video_audio_direction" in result
    assert "video_visual_reference" in result
    assert isinstance(result["video_body"], list)


def test_video_script_fields_optional_topic():
    """Test that video script works without text_topic."""
    from backend.generators.social.video_script_generator import generate_video_script_for_day

    result = generate_video_script_for_day(
        brand="Test Brand", industry="Retail", audience="Shoppers"
    )

    assert isinstance(result, dict)
    assert len(result) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
