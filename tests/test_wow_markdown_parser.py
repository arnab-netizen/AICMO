"""
Tests for WOW markdown parsing and section extraction.

These tests verify that Fix #1 (parsing wow_markdown into sections) works correctly.
"""

from backend.utils.wow_markdown_parser import (
    parse_wow_markdown_to_sections,
    validate_section_completeness,
    _title_to_section_id,
)


def test_parse_simple_markdown():
    """Test parsing markdown with two sections."""
    markdown = """## Overview

Brand: ACME Corp
Industry: Technology

## Messaging Framework

Key message: Innovation drives us
"""
    sections = parse_wow_markdown_to_sections(markdown)

    assert len(sections) == 2
    assert sections[0]["id"] == "overview"
    assert "Brand: ACME Corp" in sections[0]["content"]
    assert sections[1]["id"] == "messaging_framework"
    assert "Key message" in sections[1]["content"]


def test_parse_empty_markdown():
    """Test parsing empty markdown returns empty list."""
    assert parse_wow_markdown_to_sections("") == []
    assert parse_wow_markdown_to_sections("   ") == []
    assert parse_wow_markdown_to_sections(None) == []


def test_parse_markdown_with_preamble():
    """Test that content before first header is skipped."""
    markdown = """This is preamble text before any headers.
It should be ignored.

## Overview

This is the actual content.
"""
    sections = parse_wow_markdown_to_sections(markdown)

    assert len(sections) == 1
    assert sections[0]["id"] == "overview"
    assert "preamble" not in sections[0]["content"].lower()


def test_parse_calendar_section():
    """Test parsing a 30-day calendar table."""
    markdown = """## 30-Day Social Calendar

| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Share success story |
| Day 2 | Facebook | Post product demo |
"""
    sections = parse_wow_markdown_to_sections(markdown)

    assert len(sections) == 1
    assert sections[0]["id"] == "detailed_30_day_calendar"
    assert "| Day | Platform | Hook |" in sections[0]["content"]


def test_parse_multiple_sections_preserves_order():
    """Test that sections maintain their order."""
    markdown = """## Overview
First section

## Messaging Framework
Second section

## KPI Plan
Third section

## Final Summary
Fourth section
"""
    sections = parse_wow_markdown_to_sections(markdown)

    assert len(sections) == 4
    assert sections[0]["id"] == "overview"
    assert sections[1]["id"] == "messaging_framework"
    assert sections[2]["id"] == "kpi_plan_light"
    assert sections[3]["id"] == "final_summary"


def test_title_to_section_id_normalization():
    """Test section title normalization."""
    assert _title_to_section_id("Client Overview") == "overview"
    assert _title_to_section_id("30-Day Social Calendar") == "detailed_30_day_calendar"
    assert _title_to_section_id("Messaging Framework") == "messaging_framework"
    assert _title_to_section_id("KPI Plan") == "kpi_plan_light"
    assert _title_to_section_id("Final Summary") == "final_summary"


def test_title_to_section_id_handles_special_chars():
    """Test that special characters are removed from section IDs."""
    assert _title_to_section_id("Section (with) special! chars@") == "section_with_special_chars"


def test_validate_section_completeness_all_present():
    """Test completeness validation when all sections present."""
    sections = [
        {"id": "overview", "content": "..."},
        {"id": "messaging_framework", "content": "..."},
    ]
    expected = ["overview", "messaging_framework"]

    result = validate_section_completeness(sections, expected)

    assert result == {"overview": True, "messaging_framework": True}


def test_validate_section_completeness_missing_sections():
    """Test completeness validation when sections are missing."""
    sections = [
        {"id": "overview", "content": "..."},
    ]
    expected = ["overview", "messaging_framework", "kpi_plan_light"]

    result = validate_section_completeness(sections, expected)

    assert result == {
        "overview": True,
        "messaging_framework": False,
        "kpi_plan_light": False,
    }


def test_parse_real_wow_output_structure():
    """Test parsing a realistic WOW report structure."""
    markdown = """## Client Overview

**Brand**: Starbucks
**Industry**: Food & Beverage
**Primary Goal**: Drive digital engagement

## Messaging Framework

**Core Message**: Premium coffee experience
**Supporting Points**:
- Quality beans
- Expert roasting
- Community focus

## 30-Day Social Calendar

| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Share origin story |
| Day 2 | Facebook | Customer testimonial |
| Day 3 | Twitter | Coffee tip of the day |

## Final Summary

This strategy will drive engagement through authentic storytelling and community building.
"""
    sections = parse_wow_markdown_to_sections(markdown)

    assert len(sections) == 4

    # Verify each section has correct ID and content
    overview = next(s for s in sections if s["id"] == "overview")
    assert "Starbucks" in overview["content"]

    messaging = next(s for s in sections if s["id"] == "messaging_framework")
    assert "Premium coffee" in messaging["content"]

    calendar = next(s for s in sections if s["id"] == "detailed_30_day_calendar")
    assert "| Day |" in calendar["content"]

    summary = next(s for s in sections if s["id"] == "final_summary")
    assert "drive engagement" in summary["content"]


def test_parse_preserves_markdown_formatting():
    """Test that parsing preserves markdown formatting (bold, bullets, etc.)."""
    markdown = """## Overview

**Bold text** and *italic text*

- Bullet point 1
- Bullet point 2

1. Numbered item
2. Another item
"""
    sections = parse_wow_markdown_to_sections(markdown)

    content = sections[0]["content"]
    assert "**Bold text**" in content
    assert "*italic text*" in content
    assert "- Bullet point" in content
    assert "1. Numbered" in content


def test_parse_handles_headers_in_content():
    """Test that level-3 headers within sections don't split sections."""
    markdown = """## Overview

This is the overview.

### Subsection

This is still part of the overview.

## Messaging Framework

This is a different section.
"""
    sections = parse_wow_markdown_to_sections(markdown)

    assert len(sections) == 2
    assert "### Subsection" in sections[0]["content"]
    assert "This is still part of" in sections[0]["content"]
