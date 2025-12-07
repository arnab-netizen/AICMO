"""
Tests for PDF HTML structure to prevent layout regressions.

These tests check the generated HTML BEFORE it's converted to PDF,
ensuring that CSS classes and structural elements are present.
"""

import copy
import pytest
from backend.pdf_renderer import _render_pdf_html


@pytest.fixture
def quick_social_context():
    """Minimal context for quick_social_basic template."""
    return {
        "title": "Quick Social Test",
        "brand_name": "Test Brand",
        "campaign_title": "Test Campaign",
        "primary_channel": "Instagram",
        "overview_html": "<p>Test overview</p>",
        "audience_segments_html": "<p>Test audience</p>",
        "messaging_framework_html": "<p>Test message</p>",
        "content_buckets_html": "<ul><li>Test bucket</li></ul>",
        "calendar_html": "<table><tr><th>Day</th></tr></table>",
        "creative_direction_html": "<p>Test creative</p>",
        "hashtags_html": "<p>#test</p>",
        "platform_guidelines_html": "<p>Test guidelines</p>",
        "kpi_plan_html": "<p>Test KPIs</p>",
        "final_summary_html": "<p>Test summary</p>",
        "report": {
            "title": "Quick Social Playbook",
            "brand_name": "Test Brand",
            "audience_segments_html": "<p>Test audience</p>",
            "messaging_framework_html": "<p>Test message</p>",
            "content_buckets_html": "<ul><li>Test bucket</li></ul>",
            "calendar_html": "<table><tr><th>Day</th></tr></table>",
            "creative_direction_html": "<p>Test creative</p>",
            "hashtags_html": "<p>#test</p>",
            "platform_guidelines_html": "<p>Test guidelines</p>",
            "kpi_plan_html": "<p>Test KPIs</p>",
            "final_summary_html": "<p>Test summary</p>",
        },
    }


@pytest.fixture
def campaign_strategy_context():
    """Minimal context for campaign_strategy template."""
    return {
        "title": "Campaign Strategy Test",
        "brand_name": "Test Brand",
        "campaign_title": "Test Campaign",
        "industry": "Wellness",
        "primary_goal": "Increase brand awareness",
        "target_audience": "Growth seekers",
        "positioning_summary": "Positioning summary placeholder",
        "executive_summary": "Executive summary copy",
        "situation_analysis": "Situation description",
        "strategy": "Strategy narrative",
        "strategic_pillars": ["Pillar one", "Pillar two", "Pillar three"],
        "campaign_big_idea": "Big idea statement",
        "campaign_concepts": ["Concept A", "Concept B"],
        "content_calendar_summary": "Content calendar overview",
        "content_calendar_table_markdown": "<table><tr><td>Week</td></tr></table>",
        "kpi_framework": "KPI breakdown",
        "measurement_plan": "Measurement details",
        "next_30_days_action_plan": "Next 30 days plan",
        "core_campaign_idea_html": "<p>Legacy idea</p>",
        "audience_segments_html": "<p>Legacy audiences</p>",
        "brand_strategy_html": "<p>Brand strategy copy</p>",
        "report": {
            "campaign_title": "Test Campaign",
            "campaign_duration": "90 days",
            "objectives_html": "<p>Test objectives</p>",
            "core_campaign_idea_html": "<p>Test idea</p>",
            "competitor_snapshot": [
                {
                    "name": "Competitor A",
                    "position": "Leader",
                    "key_message": "Message A",
                    "channels": "All",
                }
            ],
            "channel_plan_html": "<ul><li>Test channel</li></ul>",
            "audience_segments_html": "<p>Test audience</p>",
            "personas": [
                {
                    "name": "Test Persona",
                    "role": "Test Role",
                    "goals": "Test Goals",
                    "challenges": "Test Challenges",
                }
            ],
            "roi_model": {
                "reach": {"q1": "10K", "q2": "25K"},
                "engagement": {"q1": "2%", "q2": "3%"},
            },
            "creative_direction_html": "<p>Test creative</p>",
            "brand_identity": {
                "primary_color": "#FF0000",
                "secondary_color": "#00FF00",
                "typography": "Test Font",
                "tone_voice": "Test Tone",
            },
            "calendar_html": "<table><tr><th>Week</th></tr></table>",
            "kpi_budget_html": "<p>Test KPIs</p>",
            "execution_html": "<p>Test execution</p>",
            "final_summary_html": "<p>Test summary</p>",
        },
    }


@pytest.fixture
def full_funnel_context():
    """Minimal context for full_funnel_growth template, including brand strategy."""
    return {
        "title": "Full Funnel Test",
        "brand_name": "Test Brand",
        "campaign_title": "Full Funnel Campaign",
        "report": {
            "title": "Full Funnel Growth Suite",
            "brand_name": "Test Brand",
        },
        "brand_strategy_html": "<p>Positioning snapshot for Test Brand</p>",
    }


class TestQuickSocialHTMLStructure:
    """Test HTML structure for quick_social_basic template."""

    def test_has_section_blocks(self, quick_social_context):
        """Verify template contains .section-block wrappers."""
        html = _render_pdf_html("quick_social_basic.html", quick_social_context)

        # Should have multiple section-block divs (at least 8 for Quick Social)
        assert (
            html.count('class="section-block"') >= 10
        ), "Template should have at least 10 section-block divs"

    def test_has_page_breaks(self, quick_social_context):
        """Verify template contains page-break markers."""
        html = _render_pdf_html("quick_social_basic.html", quick_social_context)

        # Should have at least 3 page breaks (after overview, content buckets, hashtags)
        assert (
            html.count('class="page-break"') >= 3
        ), "Template should have at least 3 page-break divs"

    def test_headings_inside_section_blocks(self, quick_social_context):
        """Verify h2 headings are inside section-block divs."""
        html = _render_pdf_html("quick_social_basic.html", quick_social_context)

        # Key section headings should exist
        assert "Who You're Reaching" in html
        assert "Your Core Message" in html
        assert "Content Themes" in html
        assert "Weekly Posting Schedule" in html

    def test_content_is_preserved(self, quick_social_context):
        """Verify template preserves actual report content."""
        html = _render_pdf_html("quick_social_basic.html", quick_social_context)

        # Content from context should appear in HTML
        assert "Test Brand" in html
        assert "Instagram" in html
        assert "Test audience" in html
        assert "#test" in html


class TestCampaignStrategyHTMLStructure:
    """Test HTML structure for campaign_strategy template."""

    def test_has_section_blocks(self, campaign_strategy_context):
        """Verify template contains .section-block wrappers."""
        html = _render_pdf_html("campaign_strategy.html", campaign_strategy_context)

        # Should have multiple section-block divs (at least 10 for Campaign Strategy)
        assert (
            html.count('class="section-block"') >= 8
        ), "Template should have at least 8 section-block divs"

    def test_has_table_wrappers(self, campaign_strategy_context):
        """Verify the content calendar table renders with Markdown data."""
        html = _render_pdf_html("campaign_strategy.html", campaign_strategy_context)

        # Verify that the content calendar table section renders
        assert "Content Calendar" in html
        assert "<table>" in html

    def test_has_page_breaks(self, campaign_strategy_context):
        """Verify template contains page-break markers."""
        html = _render_pdf_html("campaign_strategy.html", campaign_strategy_context)

        # Should have at least 5 page breaks between major sections
        assert (
            html.count('class="page-break"') >= 2
        ), "Template should have at least 2 page-break divs"

    def test_legacy_sections_render(self, campaign_strategy_context):
        """Verify legacy sections appear when the context provides HTML."""
        html = _render_pdf_html("campaign_strategy.html", campaign_strategy_context)

        assert "Legacy idea" in html
        assert "Legacy audiences" in html

    def test_headings_inside_section_blocks(self, campaign_strategy_context):
        """Verify h2 headings are inside section-block divs."""
        html = _render_pdf_html("campaign_strategy.html", campaign_strategy_context)

        # Key section headings should exist
        assert "Brand & Objectives" in html
        assert "Executive Summary" in html
        assert "Strategic Pillars" in html
        assert "Campaign Big Idea" in html

    def test_content_is_preserved(self, campaign_strategy_context):
        """Verify template preserves actual report content."""
        html = _render_pdf_html("campaign_strategy.html", campaign_strategy_context)

        # Content from context should appear in HTML
        assert "Test Brand" in html
        assert "Wellness" in html
        assert "Increase brand awareness" in html


class TestHTMLStructureIntegrity:
    """Cross-template HTML structure validation."""

    def test_base_template_extended(self, quick_social_context):
        """Verify templates properly extend base.html."""
        html = _render_pdf_html("quick_social_basic.html", quick_social_context)

        # Base template elements should be present
        assert "<!DOCTYPE html>" in html
        assert '<html lang="en">' in html
        assert 'class="doc-header"' in html
        assert 'class="doc-footer"' in html
        assert "AICMO" in html  # Agency name from base template

    def test_css_link_present(self, campaign_strategy_context):
        """Verify CSS stylesheet is linked."""
        html = _render_pdf_html("campaign_strategy.html", campaign_strategy_context)

        # CSS link should be present from base template
        assert 'link rel="stylesheet"' in html
        assert "styles.css" in html

    def test_no_jinja_artifacts(self, quick_social_context):
        """Verify no unrendered Jinja2 syntax in output."""
        html = _render_pdf_html("quick_social_basic.html", quick_social_context)

        # Should not contain Jinja2 syntax markers
        assert "{{" not in html, "Found unrendered Jinja2 variable syntax"
        assert "{%" not in html, "Found unrendered Jinja2 control syntax"
        assert "%}" not in html, "Found unrendered Jinja2 control syntax"

    def test_valid_html_structure(self, campaign_strategy_context):
        """Verify basic HTML structure is valid."""
        html = _render_pdf_html("campaign_strategy.html", campaign_strategy_context)

        # Basic HTML structure checks
        assert html.count("<html") == 1
        assert html.count("</html>") == 1
        assert html.count("<head>") == 1
        assert html.count("</head>") == 1
        assert html.count("<body>") == 1
        assert html.count("</body>") == 1


class TestFullFunnelHTMLStructure:
    """Ensure full_funnel_growth template handles brand strategy safely."""

    def test_brand_strategy_section_renders(self, full_funnel_context):
        html = _render_pdf_html("full_funnel_growth.html", full_funnel_context)

        assert "Brand Strategy" in html
        assert "Positioning snapshot for Test Brand" in html

    def test_brand_strategy_section_skips_when_missing(self, full_funnel_context):
        context = copy.deepcopy(full_funnel_context)
        context.pop("brand_strategy_html", None)
        html = _render_pdf_html("full_funnel_growth.html", context)

        assert "Brand Strategy" not in html
