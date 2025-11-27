"""
Test suite for PDF template resolution and parity (FIX #3).

Tests that:
- Each WOW package maps to correct PDF template
- PDF templates exist for all packages
- PDF export uses correct template based on package key
- Content parity between preview and PDF

Run: pytest tests/test_pdf_templates.py -v
"""

import pytest
from pathlib import Path
from backend.pdf_renderer import resolve_pdf_template_for_pack, TEMPLATE_BY_WOW_PACKAGE


class TestTemplateResolution:
    """Tests for PDF template resolution function."""

    def test_quick_social_basic_template(self):
        """Test that quick_social_basic resolves to correct template."""
        template = resolve_pdf_template_for_pack("quick_social_basic")
        assert template == "quick_social_basic.html"

    def test_strategy_campaign_standard_template(self):
        """Test that standard pack uses campaign_strategy.html."""
        template = resolve_pdf_template_for_pack("strategy_campaign_standard")
        assert template == "campaign_strategy.html"

    def test_full_funnel_growth_template(self):
        """Test that premium pack maps to full_funnel_growth.html."""
        template = resolve_pdf_template_for_pack("full_funnel_growth_suite")
        assert template == "full_funnel_growth.html"

    def test_launch_gtm_template(self):
        """Test launch GTM pack template."""
        template = resolve_pdf_template_for_pack("launch_gtm_pack")
        assert template == "launch_gtm.html"

    def test_brand_turnaround_template(self):
        """Test brand turnaround pack template."""
        template = resolve_pdf_template_for_pack("brand_turnaround_lab")
        assert template == "brand_turnaround.html"

    def test_retention_crm_template(self):
        """Test retention & CRM pack template."""
        template = resolve_pdf_template_for_pack("retention_crm_booster")
        assert template == "retention_crm.html"

    def test_performance_audit_template(self):
        """Test performance audit pack template."""
        template = resolve_pdf_template_for_pack("performance_audit_revamp")
        assert template == "performance_audit.html"

    def test_unknown_package_returns_default(self):
        """Test that unknown package returns default template."""
        template = resolve_pdf_template_for_pack("unknown_package")
        assert template == "campaign_strategy.html"

    def test_none_package_returns_default(self):
        """Test that None package returns default template."""
        template = resolve_pdf_template_for_pack(None)
        assert template == "campaign_strategy.html"

    def test_empty_string_returns_default(self):
        """Test that empty string returns default template."""
        template = resolve_pdf_template_for_pack("")
        assert template == "campaign_strategy.html"


class TestTemplateMapping:
    """Tests for TEMPLATE_BY_WOW_PACKAGE mapping."""

    def test_mapping_is_complete(self):
        """Test that all expected packages are in mapping."""
        expected_packages = [
            "quick_social_basic",
            "strategy_campaign_standard",
            "full_funnel_growth_suite",
            "launch_gtm_pack",
            "brand_turnaround_lab",
            "retention_crm_booster",
            "performance_audit_revamp",
        ]

        for package in expected_packages:
            assert package in TEMPLATE_BY_WOW_PACKAGE

    def test_all_mappings_are_html_files(self):
        """Test that all mapped templates are .html files."""
        for package, template in TEMPLATE_BY_WOW_PACKAGE.items():
            assert template.endswith(".html"), f"{package} maps to {template} (should be .html)"

    def test_no_duplicate_templates_for_different_packages(self):
        """Test that different packages use different templates (mostly)."""
        templates = list(TEMPLATE_BY_WOW_PACKAGE.values())

        # Only campaign_strategy.html should be used for multiple (as fallback)
        # Most packages should have unique templates
        from collections import Counter

        template_counts = Counter(templates)

        # More than half should be unique
        unique_count = sum(1 for count in template_counts.values() if count == 1)
        total_count = len(template_counts)
        assert unique_count > (total_count / 2)


class TestTemplateFilesExist:
    """Tests that all required template files exist."""

    def get_templates_dir(self):
        """Get path to templates directory."""
        from backend import pdf_renderer

        base_path = Path(pdf_renderer.__file__).parent
        templates_path = base_path.parent / "templates" / "pdf"
        return templates_path

    def test_quick_social_template_file_exists(self):
        """Test that quick_social_basic.html exists."""
        templates_dir = self.get_templates_dir()
        template_file = templates_dir / "quick_social_basic.html"
        assert template_file.exists(), f"Template not found: {template_file}"

    def test_full_funnel_template_file_exists(self):
        """Test that full_funnel_growth.html exists."""
        templates_dir = self.get_templates_dir()
        template_file = templates_dir / "full_funnel_growth.html"
        assert template_file.exists(), f"Template not found: {template_file}"

    def test_launch_gtm_template_file_exists(self):
        """Test that launch_gtm.html exists."""
        templates_dir = self.get_templates_dir()
        template_file = templates_dir / "launch_gtm.html"
        assert template_file.exists(), f"Template not found: {template_file}"

    def test_brand_turnaround_template_file_exists(self):
        """Test that brand_turnaround.html exists."""
        templates_dir = self.get_templates_dir()
        template_file = templates_dir / "brand_turnaround.html"
        assert template_file.exists(), f"Template not found: {template_file}"

    def test_retention_crm_template_file_exists(self):
        """Test that retention_crm.html exists."""
        templates_dir = self.get_templates_dir()
        template_file = templates_dir / "retention_crm.html"
        assert template_file.exists(), f"Template not found: {template_file}"

    def test_performance_audit_template_file_exists(self):
        """Test that performance_audit.html exists."""
        templates_dir = self.get_templates_dir()
        template_file = templates_dir / "performance_audit.html"
        assert template_file.exists(), f"Template not found: {template_file}"


class TestTemplateContent:
    """Tests that templates have expected content."""

    def get_template_content(self, template_name):
        """Load template content."""
        from backend import pdf_renderer

        base_path = Path(pdf_renderer.__file__).parent
        template_file = base_path.parent / "templates" / "pdf" / template_name

        if template_file.exists():
            return template_file.read_text()
        return ""

    def test_templates_extend_base(self):
        """Test that all templates extend base.html."""
        template_names = [
            "quick_social_basic.html",
            "full_funnel_growth.html",
            "launch_gtm.html",
            "brand_turnaround.html",
            "retention_crm.html",
            "performance_audit.html",
        ]

        for template_name in template_names:
            content = self.get_template_content(template_name)
            if content:  # Skip if file doesn't exist (will be caught by other tests)
                assert '{% extends "base.html" %}' in content or 'extends "base.html"' in content

    def test_quick_social_template_has_sections(self):
        """Test that quick_social template has expected sections."""
        content = self.get_template_content("quick_social_basic.html")

        # Should have section content markers
        expected_sections = [
            "Overview",
            "Audience",
            "Messaging",
            "Calendar",
            "Creative",
            "Hashtag",
        ]

        for section in expected_sections:
            assert section.lower() in content.lower()

    def test_full_funnel_template_has_21_sections(self):
        """Test that premium template has ~21 sections."""
        content = self.get_template_content("full_funnel_growth.html")

        # Count h2 headers (each section should have one)
        section_count = content.count("<h2>")

        # Should be close to 21 sections
        assert section_count >= 18, f"Expected ~21 sections, found {section_count}"

    def test_templates_use_report_object(self):
        """Test that templates reference report object."""
        template_names = [
            "quick_social_basic.html",
            "full_funnel_growth.html",
        ]

        for template_name in template_names:
            content = self.get_template_content(template_name)
            if content:
                assert "report.get(" in content or "{{ report" in content


class TestPackSectionAlignment:
    """Tests that templates match pack section counts."""

    def get_template_section_count(self, template_name):
        """Count sections (h2 headers) in template."""
        from backend import pdf_renderer

        base_path = Path(pdf_renderer.__file__).parent
        template_file = base_path.parent / "templates" / "pdf" / template_name

        if template_file.exists():
            content = template_file.read_text()
            return content.count("<h2>")
        return 0

    def test_basic_template_has_10_sections(self):
        """Test that Basic pack template has ~10 sections."""
        count = self.get_template_section_count("quick_social_basic.html")
        # Allow ±2 sections
        assert 8 <= count <= 12, f"Expected ~10 sections, found {count}"

    def test_standard_template_has_17_sections(self):
        """Test that Standard pack template has ~17 sections."""
        count = self.get_template_section_count("campaign_strategy.html")
        # Allow ±2 sections
        assert 15 <= count <= 19, f"Expected ~17 sections, found {count}"

    def test_premium_template_has_21_sections(self):
        """Test that Premium pack template has ~21 sections."""
        count = self.get_template_section_count("full_funnel_growth.html")
        # Allow ±2 sections
        assert 19 <= count <= 23, f"Expected ~21 sections, found {count}"

    def test_launch_gtm_has_14_sections(self):
        """Test that Launch GTM template has ~14 sections."""
        count = self.get_template_section_count("launch_gtm.html")
        # Allow ±2 sections
        assert 12 <= count <= 16, f"Expected ~14 sections, found {count}"


class TestTemplateInheritance:
    """Tests that templates properly inherit from base."""

    def test_base_template_exists(self):
        """Test that base.html exists."""
        from backend import pdf_renderer

        base_path = Path(pdf_renderer.__file__).parent
        base_file = base_path.parent / "templates" / "pdf" / "base.html"
        assert base_file.exists()

    def test_base_template_has_content_block(self):
        """Test that base template defines content block."""
        from backend import pdf_renderer

        base_path = Path(pdf_renderer.__file__).parent
        base_file = base_path.parent / "templates" / "pdf" / "base.html"

        if base_file.exists():
            content = base_file.read_text()
            assert "{% block content %}" in content or "block content" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
