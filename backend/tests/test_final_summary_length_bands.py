"""
Test that final_summary respects word count bands for different pack tiers.

This prevents regressions where one pack's length requirements break another pack.
"""

from __future__ import annotations

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
from backend.main import GenerateRequest, _gen_final_summary


def _basic_brief() -> ClientInputBrief:
    """Create a minimal test brief."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="Test Brand",
            industry="Technology",
            product_service="SaaS platform",
            primary_goal="Increase monthly active users by 40%",
            primary_customer="Remote team leads",
            secondary_customer="Project managers",
            brand_tone="innovative, reliable, user-friendly",
            location="San Francisco",
            timeline="3 months",
        ),
        audience=AudienceBrief(
            primary_customer="Remote team leads",
            secondary_customer="Project managers",
            pain_points=["Time constraints", "Tool overload"],
            online_hangouts=["LinkedIn", "X"],
        ),
        goal=GoalBrief(
            primary_goal="Increase monthly active users by 40%",
            timeline="3 months",
            kpis=["MAU", "Retention"],
        ),
        voice=VoiceBrief(
            tone_of_voice=["innovative", "reliable", "user-friendly"],
        ),
        product_service=ProductServiceBrief(
            current_offers="Team collaboration platform",
            testimonials_or_proof="4.5/5 stars from users",
        ),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["LinkedIn", "X"],
        ),
        operations=OperationsBrief(
            needs_calendar=True,
        ),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["innovative", "reliable", "user-friendly"],
            success_30_days="30% increase in signups",
            tagline="Work together, anywhere",
        ),
    )


def test_final_summary_respects_quick_social_word_band():
    """Quick Social final_summary should be 100-260 words (short, punchy)."""
    brief = _basic_brief()
    req = GenerateRequest(
        brief=brief,
        package_preset="quick_social_basic",
    )

    content = _gen_final_summary(req)
    words = content.split()
    word_count = len(words)

    # Quick Social benchmark: min_words=100, max_words=260
    assert 100 <= word_count <= 260, (
        f"Quick Social final_summary has {word_count} words, " f"expected 100-260 words"
    )

    # Should not contain forbidden phrases
    assert "post regularly" not in content.lower(), "Contains forbidden phrase 'post regularly'"
    assert (
        "do social media consistently" not in content.lower()
    ), "Contains forbidden phrase 'do social media consistently'"


def test_final_summary_respects_strategy_standard_word_band():
    """Strategy Standard final_summary should be 180-400 words (richer content)."""
    brief = _basic_brief()
    req = GenerateRequest(
        brief=brief,
        package_preset="strategy_campaign_standard",
    )

    content = _gen_final_summary(req)
    words = content.split()
    word_count = len(words)

    # Strategy Campaign benchmark: min_words=180, max_words=400
    assert 180 <= word_count <= 400, (
        f"Strategy final_summary has {word_count} words, " f"expected 180-400 words"
    )


def test_final_summary_respects_strategy_premium_word_band():
    """Strategy Premium final_summary should be 180-400 words (same as standard)."""
    brief = _basic_brief()
    req = GenerateRequest(
        brief=brief,
        package_preset="strategy_campaign_premium",
    )

    content = _gen_final_summary(req)
    words = content.split()
    word_count = len(words)

    # Strategy Campaign benchmark: min_words=180, max_words=400
    assert 180 <= word_count <= 400, (
        f"Strategy Premium final_summary has {word_count} words, " f"expected 180-400 words"
    )


def test_final_summary_respects_full_funnel_word_band():
    """Full Funnel final_summary should be 180-400 words (rich content)."""
    brief = _basic_brief()
    req = GenerateRequest(
        brief=brief,
        package_preset="full_funnel_growth_suite",
    )

    content = _gen_final_summary(req)
    words = content.split()
    word_count = len(words)

    # Full Funnel uses strategy campaign benchmarks: min_words=180, max_words=400
    assert 180 <= word_count <= 400, (
        f"Full Funnel final_summary has {word_count} words, " f"expected 180-400 words"
    )


def test_final_summary_has_key_takeaways_heading():
    """All final_summary sections should have the Key Takeaways heading."""
    brief = _basic_brief()

    for pack_key in [
        "quick_social_basic",
        "strategy_campaign_standard",
        "full_funnel_growth_suite",
    ]:
        req = GenerateRequest(
            brief=brief,
            package_preset=pack_key,
        )

        content = _gen_final_summary(req)
        assert (
            "## Key Takeaways" in content
        ), f"Pack {pack_key} final_summary missing '## Key Takeaways' heading"


def test_final_summary_short_style_uses_simple_bullets():
    """Short style (quick_social) should have 3-5 simple bullets."""
    brief = _basic_brief()
    req = GenerateRequest(
        brief=brief,
        package_preset="quick_social_basic",
    )

    content = _gen_final_summary(req)
    bullet_lines = [line for line in content.split("\n") if line.strip().startswith("- ")]
    bullet_count = len(bullet_lines)

    # Quick Social benchmark: max_bullets=8, but we target 3-5 for simplicity
    assert (
        3 <= bullet_count <= 8
    ), f"Quick Social final_summary has {bullet_count} bullets, expected 3-8"


def test_final_summary_rich_style_uses_detailed_bullets():
    """Rich style (strategy packs) should have 5+ detailed bullets."""
    brief = _basic_brief()
    req = GenerateRequest(
        brief=brief,
        package_preset="strategy_campaign_standard",
    )

    content = _gen_final_summary(req)
    bullet_lines = [line for line in content.split("\n") if line.strip().startswith("- ")]
    bullet_count = len(bullet_lines)

    # Strategy packs should have 5+ bullets for comprehensive takeaways
    assert bullet_count >= 5, f"Strategy final_summary has {bullet_count} bullets, expected 5+"
