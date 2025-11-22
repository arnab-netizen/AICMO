"""
Placeholder detection utilities.

Provides:
- Detection of known placeholder patterns in reports
- Integration point for export pipeline to block/warn on placeholders
- Configurable placeholder list for future extensibility
"""

import logging
from typing import List
from aicmo.io.client_reports import AICMOOutputReport

logger = logging.getLogger("aicmo.placeholders")

# Known placeholder patterns that indicate incomplete/stub content
PLACEHOLDER_PATTERNS = {
    # Social calendar hooks
    "Hook idea for day": "Social Calendar",
    "hook idea for day": "Social Calendar",
    # Performance review stubs
    "Performance review will be populated": "Performance Review",
    "performance review will be populated": "Performance Review",
    "will be populated once data is available": "Performance Review",
    # General stubs
    "TBD": "Unspecified Section",
    "TO BE DETERMINED": "Unspecified Section",
    "[PLACEHOLDER]": "Unspecified Section",
    "[placeholder]": "Unspecified Section",
}


def report_has_placeholders(report: AICMOOutputReport) -> List[str]:
    """
    Scan report for known placeholder patterns.

    Args:
        report: AICMOOutputReport to scan.

    Returns:
        List of section names where placeholders were found.
        Empty list if report is clean.

    Design:
        - Scans all text-bearing fields in the report
        - Returns section names (not line numbers) for operator-friendly messages
        - Non-blocking: doesn't crash on missing fields
    """
    found_sections = set()

    if not report:
        return []

    # Scan marketing plan
    try:
        mp = report.marketing_plan
        if mp:
            fields_to_check = [
                mp.executive_summary,
                mp.situation_analysis,
                mp.strategy,
            ]
            for field in fields_to_check:
                if field:
                    for pattern, section in PLACEHOLDER_PATTERNS.items():
                        if pattern in field:
                            found_sections.add(section)
                            logger.warning(
                                f"Placeholder found in marketing plan: {pattern} ({section})"
                            )
    except Exception as e:
        logger.warning(f"Error scanning marketing plan for placeholders: {e}")

    # Scan campaign blueprint
    try:
        cb = report.campaign_blueprint
        if cb and cb.big_idea:
            for pattern, section in PLACEHOLDER_PATTERNS.items():
                if pattern in cb.big_idea:
                    found_sections.add(section)
                    logger.warning(
                        f"Placeholder found in campaign blueprint: {pattern} ({section})"
                    )
    except Exception as e:
        logger.warning(f"Error scanning campaign blueprint for placeholders: {e}")

    # Scan social calendar
    try:
        cal = report.social_calendar
        if cal and cal.posts:
            for post in cal.posts:
                fields = [post.hook, post.theme, post.cta]
                for field in fields:
                    if field:
                        for pattern, section in PLACEHOLDER_PATTERNS.items():
                            if pattern in field:
                                found_sections.add("Social Calendar")
                                logger.warning(f"Placeholder found in social calendar: {pattern}")
    except Exception as e:
        logger.warning(f"Error scanning social calendar for placeholders: {e}")

    # Scan performance review
    try:
        pr = report.performance_review
        if pr and pr.summary:
            fields = [
                pr.summary.growth_summary,
                pr.summary.wins,
                pr.summary.failures,
                pr.summary.opportunities,
            ]
            for field in fields:
                if field:
                    for pattern, section in PLACEHOLDER_PATTERNS.items():
                        if pattern in field:
                            found_sections.add("Performance Review")
                            logger.warning(f"Placeholder found in performance review: {pattern}")
    except Exception as e:
        logger.warning(f"Error scanning performance review for placeholders: {e}")

    # Scan creatives
    try:
        cr = report.creatives
        if cr:
            all_text = []
            if cr.hooks:
                all_text.extend(cr.hooks)
            if cr.captions:
                all_text.extend(cr.captions)
            if cr.scripts:
                all_text.extend(cr.scripts)
            if cr.email_subject_lines:
                all_text.extend(cr.email_subject_lines)

            for text in all_text:
                if text:
                    for pattern, section in PLACEHOLDER_PATTERNS.items():
                        if pattern in text:
                            found_sections.add("Creatives")
                            logger.warning(f"Placeholder found in creatives: {pattern}")
    except Exception as e:
        logger.warning(f"Error scanning creatives for placeholders: {e}")

    return sorted(list(found_sections))


def format_placeholder_warning(sections: List[str]) -> str:
    """
    Format placeholder section list into a human-readable message.

    Args:
        sections: List of section names with placeholders.

    Returns:
        Formatted warning message for operator display.
    """
    if not sections:
        return ""

    sections_str = ", ".join(sections)
    return (
        f"Report contains placeholders in: {sections_str}. "
        f"Please update or remove these sections before exporting."
    )
