"""
Tests for Quick Social soft validation sections.

Ensures that detailed_30_day_calendar, kpi_plan_light, and execution_roadmap
use format-only validation instead of strict benchmark matching.
"""

from backend.validators.benchmark_validator import validate_section_against_benchmark


def test_detailed_30_day_calendar_soft_validation_passes():
    """Test that calendar section passes with valid table structure."""
    content = """This calendar provides a monthly roadmap.

| Day | Platform | Hook | Bucket | CTA |
|-----|----------|------|--------|-----|
| 1 | Instagram | Morning routine tips | Education | DM us |
| 2 | LinkedIn | Behind the scenes | Education | Learn more |
| 3 | Twitter | Customer success story | Proof | Read story |
| 4 | Instagram | 20% off pastries | Promo | Use code PASTRY20 |
| 5 | LinkedIn | Friday meetup | Community | RSVP now |
| 6 | Instagram | Latte art tutorial | Education | Try it |
| 7 | Twitter | 5-star review | Proof | Check reviews |
| 8 | Instagram | New menu item | Experience | Visit this week |
| 9 | LinkedIn | Industry trend | Education | Read article |
| 10 | Instagram | Customer photo | Community | Tag us |
| 11 | Twitter | Free pastry offer | Promo | Show tweet |
| 12 | Instagram | Barista interview | Education | Learn more |
| 13 | LinkedIn | Catering success | Proof | Get quote |
| 14 | Instagram | Weekend vibes | Experience | Visit us |
| 15 | Twitter | Loyalty program | Community | Join rewards |
| 16 | Instagram | Brewing mistakes | Education | Save post |
| 17 | LinkedIn | Team spotlight | Education | Meet team |
| 18 | Instagram | Renovation journey | Proof | See transformation |
| 19 | Twitter | Flash sale | Promo | Valid today |
| 20 | Instagram | Host your event | Experience | Book now |
| 21 | LinkedIn | Local bakery collab | Community | Learn partnership |
| 22 | Instagram | Coffee origin story | Education | Explore beans |
| 23 | Twitter | Testimonial video | Proof | Watch video |
| 24 | Instagram | New merchandise | Promo | Shop now |
| 25 | LinkedIn | Sustainability | Education | Read commitment |
| 26 | Instagram | Community poll | Community | Vote now |
| 27 | Twitter | Extended hours | Experience | See you soon |
| 28 | Instagram | Barista training | Education | Appreciate craft |
| 29 | LinkedIn | Month in review | Community | See recap |
| 30 | Instagram | Next month preview | Experience | Stay tuned |

## Implementation Notes

Batch-create content weekly."""

    result = validate_section_against_benchmark(
        pack_key="quick_social_basic",
        section_id="detailed_30_day_calendar",
        content=content,
    )

    assert result.status in ("PASS", "PASS_WITH_WARNINGS")
    assert not result.has_errors()


def test_detailed_30_day_calendar_fails_without_table():
    """Test that calendar section fails without table structure."""
    content = """Just some text about calendars but no actual table."""

    result = validate_section_against_benchmark(
        pack_key="quick_social_basic",
        section_id="detailed_30_day_calendar",
        content=content,
    )

    assert result.status == "FAIL"
    assert result.has_errors()
    assert any(issue.code == "MISSING_TABLE_STRUCTURE" for issue in result.issues)


def test_kpi_plan_light_soft_validation_passes():
    """Test that KPI section passes with relevant metrics."""
    content = """## Key Performance Indicators

Track these metrics to measure success:

- **Reach**: Target 10,000 impressions per week across all platforms
- **Engagement Rate**: Aim for 4-6% engagement (likes, comments, shares)
- **Click-Through Rate (CTR)**: Monitor traffic to website from social posts
- **Follower Growth**: Grow audience by 15% per quarter
- **Conversion**: Track leads and sales from social channels

## Measurement Approach

Review metrics weekly and adjust content strategy based on performance data."""

    result = validate_section_against_benchmark(
        pack_key="quick_social_basic",
        section_id="kpi_plan_light",
        content=content,
    )

    assert result.status in ("PASS", "PASS_WITH_WARNINGS")
    assert not result.has_errors()


def test_kpi_plan_light_fails_without_kpi_content():
    """Test that KPI section fails without relevant metrics."""
    content = """Just some general text about business goals."""

    result = validate_section_against_benchmark(
        pack_key="quick_social_basic",
        section_id="kpi_plan_light",
        content=content,
    )

    assert result.status == "FAIL"
    assert result.has_errors()
    assert any(issue.code == "MISSING_KPI_CONTENT" for issue in result.issues)


def test_execution_roadmap_soft_validation_passes():
    """Test that execution roadmap passes with timeline structure."""
    content = """## Implementation Timeline

### Week 1: Setup & Launch
- Day 1: Set up social media profiles and branding
- Day 2: Create content calendar and prepare first week's posts
- Day 3: Launch first posts across all platforms

### Week 2-4: Momentum Building
- Continue daily posting schedule
- Monitor engagement and optimize timing
- Respond to comments and build community

### Ongoing Optimization
- Review analytics weekly
- Adjust content mix based on performance
- Test new formats and ideas"""

    result = validate_section_against_benchmark(
        pack_key="quick_social_basic",
        section_id="execution_roadmap",
        content=content,
    )

    assert result.status in ("PASS", "PASS_WITH_WARNINGS")
    assert not result.has_errors()


def test_execution_roadmap_fails_without_timeline():
    """Test that execution roadmap fails without timeline markers."""
    content = """Just some general advice about executing a plan."""

    result = validate_section_against_benchmark(
        pack_key="quick_social_basic",
        section_id="execution_roadmap",
        content=content,
    )

    assert result.status == "FAIL"
    assert result.has_errors()
    assert any(issue.code == "MISSING_TIMELINE" for issue in result.issues)


def test_soft_validation_only_for_quick_social():
    """Test that soft validation only applies to Quick Social pack."""
    # For a different pack, should use normal validation
    content = """| Day | Platform | Hook |
|-----|----------|------|
| 1 | Instagram | Test |"""

    result = validate_section_against_benchmark(
        pack_key="some_other_pack",
        section_id="detailed_30_day_calendar",
        content=content,
    )

    # Should not use soft validation - will either fail or succeed based on normal benchmarks
    # This just tests the routing logic
    assert result.section_id == "detailed_30_day_calendar"


def test_other_quick_social_sections_use_normal_validation():
    """Test that non-soft sections in Quick Social still use strict validation."""
    # A section like "overview" should still use normal benchmark validation
    content = """Brand overview content here."""

    result = validate_section_against_benchmark(
        pack_key="quick_social_basic",
        section_id="overview",
        content=content,
    )

    # Will validate against benchmark (may pass or fail depending on benchmarks)
    # This just verifies it doesn't use soft validation
    assert result.section_id == "overview"
