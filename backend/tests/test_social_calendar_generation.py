"""Tests for social_calendar_generator: verify hooks, CTAs, and brief context usage."""

import pytest
from datetime import date, timedelta
from aicmo.io.client_reports import (
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    ProductServiceItem,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
)
from aicmo.generators.social_calendar_generator import (
    generate_social_calendar,
    _stub_social_calendar,
    _get_themes,
    _get_platforms,
)


@pytest.fixture
def sample_brief():
    """Create a sample brief for testing."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="TechFlow",
            industry="Software",
            business_type="B2B SaaS",
            description="Workflow automation for teams",
        ),
        audience=AudienceBrief(
            primary_customer="Software teams",
            pain_points=["Time management", "Collaboration overhead"],
        ),
        goal=GoalBrief(
            primary_goal="Increase platform adoption",
            timeline="6 months",
            kpis=["Sign-ups", "Engagement"],
        ),
        voice=VoiceBrief(tone_of_voice=["Professional", "Friendly"]),
        product_service=ProductServiceBrief(
            items=[
                ProductServiceItem(
                    name="Core Platform",
                    usp="AI-powered workflow optimization",
                )
            ]
        ),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["LinkedIn", "Twitter"],
        ),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )


class TestStubSocialCalendar:
    """Test stub mode (offline fallback)."""

    def test_stub_generates_correct_number_of_posts(self, sample_brief):
        """Verify stub generates requested number of days."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        assert len(posts) == 7

    def test_stub_post_structure(self, sample_brief):
        """Verify all posts have required fields."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        for post in posts:
            assert post.date is not None
            assert post.platform
            assert post.theme
            assert post.hook
            assert post.cta
            assert post.asset_type
            assert post.status == "planned"

    def test_stub_no_hardcoded_placeholders(self, sample_brief):
        """Verify no hardcoded 'Hook idea for day' phrases."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        for i, post in enumerate(posts):
            assert "Hook idea for day" not in post.hook
            assert "hook idea for day" not in post.hook.lower()
            assert not post.hook.startswith(f"Hook idea for day {i+1}")

    def test_stub_cta_variation(self, sample_brief):
        """Verify CTAs are not all the same."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        ctas = [post.cta for post in posts]
        # With 7 days and CTA rotation options, should have variation
        unique_ctas = set(ctas)
        assert len(unique_ctas) > 1, f"Expected varied CTAs but got: {ctas}"

    def test_stub_uses_brief_context(self, sample_brief):
        """Verify hooks use brand and audience from brief."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        all_hooks = " ".join([post.hook for post in posts])
        # Should reference brand name at some point
        assert "TechFlow" in all_hooks or "Software teams" in all_hooks

    def test_stub_respects_start_date(self, sample_brief):
        """Verify posts have correct dates starting from start_date."""
        start = date(2025, 2, 15)
        posts = _stub_social_calendar(
            sample_brief,
            start_date=start,
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        for i, post in enumerate(posts):
            expected_date = start + timedelta(days=i)
            assert post.date == expected_date

    def test_stub_uses_brief_platforms(self, sample_brief):
        """Verify posts use platforms from brief when available."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        platforms_used = set([post.platform for post in posts])
        # Should use at least some of the provided platforms
        brief_platforms = set(sample_brief.assets_constraints.focus_platforms)
        assert len(platforms_used & brief_platforms) > 0

    def test_stub_asset_type_alternation(self, sample_brief):
        """Verify asset types alternate between reel and static_post."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        for i, post in enumerate(posts):
            expected = "reel" if (i + 1) % 2 == 1 else "static_post"
            assert post.asset_type == expected

    def test_stub_pain_points_in_hooks(self, sample_brief):
        """Verify pain points appear in stub hooks."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        all_hooks = " ".join([post.hook for post in posts])
        # At least one pain point should appear
        pain_points = sample_brief.audience.pain_points
        assert any(pp.lower() in all_hooks.lower() for pp in pain_points)

    def test_stub_no_placeholder_phrases(self, sample_brief):
        """Verify no placeholder phrases like 'TBD', 'placeholder', etc."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        forbidden_phrases = ["TBD", "placeholder", "lorem ipsum", "TODO", "will be customized"]
        for post in posts:
            full_text = f"{post.hook} {post.cta}"
            for phrase in forbidden_phrases:
                assert phrase.lower() not in full_text.lower()

    def test_stub_hooks_are_descriptive(self, sample_brief):
        """Verify hooks are actual content, not generic templates."""
        posts = _stub_social_calendar(
            sample_brief,
            start_date=date(2025, 1, 1),
            days=7,
            themes=_get_themes(7),
            platforms=_get_platforms(sample_brief),
        )
        for post in posts:
            # Each hook should be meaningful length and specific
            assert len(post.hook) > 20, f"Hook too short: {post.hook}"
            assert len(post.cta) > 2, f"CTA too short: {post.cta}"


class TestMainGenerateFunction:
    """Test main generate_social_calendar function."""

    def test_generate_returns_list(self, sample_brief):
        """Verify main function returns a list."""
        result = generate_social_calendar(sample_brief, days=7)
        assert isinstance(result, list)
        assert len(result) == 7

    def test_generate_respects_days_parameter(self, sample_brief):
        """Verify days parameter is respected."""
        for num_days in [1, 3, 7, 14]:
            result = generate_social_calendar(sample_brief, days=num_days)
            assert len(result) == num_days

    def test_generate_default_start_date(self, sample_brief):
        """Verify default start_date is today."""
        from datetime import datetime

        result = generate_social_calendar(sample_brief, days=3)
        today = datetime.now().date()
        assert result[0].date == today
        assert result[1].date == today + timedelta(days=1)
        assert result[2].date == today + timedelta(days=2)

    def test_generate_custom_start_date(self, sample_brief):
        """Verify custom start_date is used."""
        custom_date = date(2025, 3, 1)
        result = generate_social_calendar(sample_brief, start_date=custom_date, days=3)
        assert result[0].date == custom_date
        assert result[1].date == custom_date + timedelta(days=1)
        assert result[2].date == custom_date + timedelta(days=2)

    def test_generate_graceful_degradation(self, sample_brief):
        """Verify function never throws, always returns valid posts."""
        # Even with env var set to LLM, should gracefully fall back
        result = generate_social_calendar(sample_brief, days=5)
        assert len(result) == 5
        for post in result:
            assert post.date
            assert post.hook
            assert post.cta
            assert post.platform
            assert post.theme


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_themes_returns_correct_count(self):
        """Verify _get_themes returns requested number."""
        themes = _get_themes(7)
        assert len(themes) == 7
        assert themes[0] == "Brand Story"

    def test_get_themes_includes_variety(self):
        """Verify themes have variety."""
        themes = _get_themes(7)
        unique = set(themes)
        assert len(unique) > 1

    def test_get_platforms_from_brief(self, sample_brief):
        """Verify _get_platforms extracts from brief."""
        platforms = _get_platforms(sample_brief)
        assert "LinkedIn" in platforms
        assert "Twitter" in platforms

    def test_get_platforms_defaults(self):
        """Verify _get_platforms defaults when not in brief."""
        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="Test",
                industry="Tech",
                business_type="B2B",
                description="Test",
            ),
            audience=AudienceBrief(primary_customer="Teams"),
            goal=GoalBrief(primary_goal="Growth"),
            voice=VoiceBrief(tone_of_voice=["Professional"]),
            product_service=ProductServiceBrief(items=[]),
            assets_constraints=AssetsConstraintsBrief(),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(),
        )
        platforms = _get_platforms(brief)
        assert len(platforms) == 3
        assert "Instagram" in platforms


class TestIntegrationWithBrief:
    """Test integration with various brief configurations."""

    def test_brief_with_no_pain_points(self):
        """Verify stub mode works without pain points."""
        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="Simple Co",
                industry="Retail",
                business_type="B2C",
                description="A simple company",
            ),
            audience=AudienceBrief(primary_customer="Everyone"),
            goal=GoalBrief(primary_goal="Be great"),
            voice=VoiceBrief(tone_of_voice=["Friendly"]),
            product_service=ProductServiceBrief(items=[]),
            assets_constraints=AssetsConstraintsBrief(),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(),
        )
        posts = generate_social_calendar(brief, days=3)
        assert len(posts) == 3
        assert all(p.hook for p in posts)

    def test_brief_with_multiple_products(self):
        """Verify stub mode works with multiple products."""
        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="Multi Corp",
                industry="Tech",
                business_type="B2B",
                description="Multiple products",
            ),
            audience=AudienceBrief(primary_customer="Enterprise"),
            goal=GoalBrief(primary_goal="Market leadership"),
            voice=VoiceBrief(tone_of_voice=["Professional"]),
            product_service=ProductServiceBrief(
                items=[
                    ProductServiceItem(name="Product A", usp="Fast"),
                    ProductServiceItem(name="Product B", usp="Scalable"),
                ]
            ),
            assets_constraints=AssetsConstraintsBrief(
                focus_platforms=["LinkedIn", "Twitter", "Instagram"]
            ),
            operations=OperationsBrief(),
            strategy_extras=StrategyExtrasBrief(),
        )
        posts = generate_social_calendar(brief, days=5)
        assert len(posts) == 5
        assert all(p.hook for p in posts)
        assert all("Hook idea for day" not in p.hook for p in posts)
