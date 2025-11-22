"""
Report validation for agency-grade standards.

Validates AICMOOutputReport against REPORT_SPEC_AGENCY_GRADE.md requirements.
"""

import logging
import re
from dataclasses import dataclass
from typing import Iterator, List, Optional

from aicmo.io.client_reports import AICMOOutputReport

logger = logging.getLogger(__name__)

# Strictly prohibited phrases that indicate incomplete/placeholder content
PROHIBITED_PHRASES = {
    "hook idea for day",
    "will be populated once data is available",
    "tbd",
    "to be determined",
    "lorem ipsum",
    "placeholder",
    "todo",
    "fixme",
    "tk",  # journalist shorthand for "to come"
    "generic persona",
    "example objective",
}

# Patterns for bracketed placeholders [INSERT], [TBD], etc.
BRACKET_PATTERN = re.compile(r"\[(?:INSERT|TBD|TBA|FILL|TO.*?COME|DELETE|EDIT)\]", re.IGNORECASE)


@dataclass
class ReportIssue:
    """Represents a validation issue found in a report."""

    section: str
    """Section name where issue was found (e.g., 'marketing_plan.pillars')"""

    message: str
    """Human-readable issue description"""

    severity: str
    """'error' (blocks export) or 'warning' (allows export but alerts operator)"""

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.section}: {self.message}"


class ReportValidationError(Exception):
    """Raised when a report fails validation with error-level issues."""

    def __init__(self, issues: List[ReportIssue]):
        self.issues = issues
        error_issues = [i for i in issues if i.severity == "error"]
        message = f"Report validation failed with {len(error_issues)} error(s)"
        super().__init__(message)


def iter_report_text_fields(report: AICMOOutputReport) -> Iterator[tuple[str, str]]:
    """
    Iterate over all text fields in a report.

    Yields tuples of (field_path, text_content) for validation scanning.
    Skips empty/None values and non-text fields.

    Args:
        report: AICMOOutputReport instance to scan

    Yields:
        (field_path, text) tuples, e.g., ('marketing_plan.executive_summary', 'text...')
    """
    mp = report.marketing_plan
    cb = report.campaign_blueprint
    cal = report.social_calendar
    pr = report.performance_review
    cr = report.creatives
    ap = report.action_plan

    # Handle None fields gracefully
    if not mp or not cb or not cal:
        return

    # Marketing Plan
    if mp.executive_summary:
        yield ("marketing_plan.executive_summary", mp.executive_summary)
    if mp.situation_analysis:
        yield ("marketing_plan.situation_analysis", mp.situation_analysis)
    if mp.strategy:
        yield ("marketing_plan.strategy", mp.strategy)

    for i, pillar in enumerate(mp.pillars):
        if pillar.name:
            yield (f"marketing_plan.pillars[{i}].name", pillar.name)
        if pillar.description:
            yield (f"marketing_plan.pillars[{i}].description", pillar.description)

    if mp.messaging_pyramid:
        mp_m = mp.messaging_pyramid
        if mp_m.promise:
            yield ("marketing_plan.messaging_pyramid.promise", mp_m.promise)
        for i, msg in enumerate(mp_m.key_messages):
            if msg:
                yield (f"marketing_plan.messaging_pyramid.key_messages[{i}]", msg)
        for i, pp in enumerate(mp_m.proof_points):
            if pp:
                yield (f"marketing_plan.messaging_pyramid.proof_points[{i}]", pp)

    if mp.swot:
        swot = mp.swot
        for i, s in enumerate(swot.strengths):
            if s:
                yield (f"marketing_plan.swot.strengths[{i}]", s)
        for i, w in enumerate(swot.weaknesses):
            if w:
                yield (f"marketing_plan.swot.weaknesses[{i}]", w)
        for i, o in enumerate(swot.opportunities):
            if o:
                yield (f"marketing_plan.swot.opportunities[{i}]", o)
        for i, t in enumerate(swot.threats):
            if t:
                yield (f"marketing_plan.swot.threats[{i}]", t)

    if mp.competitor_snapshot:
        cs = mp.competitor_snapshot
        if cs.narrative:
            yield ("marketing_plan.competitor_snapshot.narrative", cs.narrative)
        for i, cp in enumerate(cs.common_patterns):
            if cp:
                yield (f"marketing_plan.competitor_snapshot.common_patterns[{i}]", cp)

    # Campaign Blueprint
    if cb.big_idea:
        yield ("campaign_blueprint.big_idea", cb.big_idea)
    if cb.objective.primary:
        yield ("campaign_blueprint.objective.primary", cb.objective.primary)
    if cb.objective.secondary:
        yield ("campaign_blueprint.objective.secondary", cb.objective.secondary)
    if cb.audience_persona and cb.audience_persona.name:
        yield ("campaign_blueprint.audience_persona.name", cb.audience_persona.name)
    if cb.audience_persona and cb.audience_persona.description:
        yield (
            "campaign_blueprint.audience_persona.description",
            cb.audience_persona.description,
        )

    # Social Calendar
    for i, post in enumerate(cal.posts):
        if post.theme:
            yield (f"social_calendar.posts[{i}].theme", post.theme)
        if post.hook:
            yield (f"social_calendar.posts[{i}].hook", post.hook)
        if post.cta:
            yield (f"social_calendar.posts[{i}].cta", post.cta)

    # Performance Review
    if pr:
        perf = pr.summary
        if perf.growth_summary:
            yield ("performance_review.summary.growth_summary", perf.growth_summary)
        if perf.wins:
            yield ("performance_review.summary.wins", perf.wins)
        if perf.failures:
            yield ("performance_review.summary.failures", perf.failures)
        if perf.opportunities:
            yield ("performance_review.summary.opportunities", perf.opportunities)

    # Persona Cards
    for i, card in enumerate(report.persona_cards):
        if card.name:
            yield (f"persona_cards[{i}].name", card.name)
        if card.demographics:
            yield (f"persona_cards[{i}].demographics", card.demographics)
        for j, pp in enumerate(card.pain_points):
            if pp:
                yield (f"persona_cards[{i}].pain_points[{j}]", pp)

    # Action Plan
    if ap:
        for i, action in enumerate(ap.quick_wins):
            if action:
                yield (f"action_plan.quick_wins[{i}]", action)
        for i, action in enumerate(ap.next_10_days):
            if action:
                yield (f"action_plan.next_10_days[{i}]", action)
        for i, action in enumerate(ap.next_30_days):
            if action:
                yield (f"action_plan.next_30_days[{i}]", action)
        for i, risk in enumerate(ap.risks):
            if risk:
                yield (f"action_plan.risks[{i}]", risk)

    # Creatives
    if cr:
        if cr.notes:
            yield ("creatives.notes", cr.notes)
        for i, hook in enumerate(cr.hooks):
            if hook:
                yield (f"creatives.hooks[{i}]", hook)
        for i, caption in enumerate(cr.captions):
            if caption:
                yield (f"creatives.captions[{i}]", caption)
        for i, script in enumerate(cr.scripts):
            if script:
                yield (f"creatives.scripts[{i}]", script)

    # Extra sections (TURBO enhancements)
    for section_name, content in report.extra_sections.items():
        if content:
            yield (f"extra_sections.{section_name}", content)


def _contains_prohibited_phrase(text: str) -> Optional[str]:
    """
    Check if text contains prohibited placeholder phrases.

    Returns the offending phrase if found, None otherwise.
    """
    text_lower = text.lower()
    for phrase in PROHIBITED_PHRASES:
        if phrase in text_lower:
            return phrase
    return None


def _contains_bracket_placeholder(text: str) -> Optional[str]:
    """Check if text contains [BRACKETED] placeholders."""
    match = BRACKET_PATTERN.search(text)
    return match.group(0) if match else None


def validate_report(report: AICMOOutputReport) -> List[ReportIssue]:
    """
    Validate a report against agency-grade standards.

    Scans all text fields for prohibited content, checks required fields
    for presence and depth, validates structure.

    Args:
        report: AICMOOutputReport to validate

    Returns:
        List of ReportIssue instances (empty if report is valid)

    Raises:
        Nothing - check returned list for error-level issues
    """
    issues: List[ReportIssue] = []

    # 1. Check required fields are present
    if not report.marketing_plan:
        issues.append(
            ReportIssue(
                "marketing_plan",
                "Marketing plan is required",
                "error",
            )
        )
        return issues  # Can't validate further without plan

    if not report.campaign_blueprint:
        issues.append(
            ReportIssue(
                "campaign_blueprint",
                "Campaign blueprint is required",
                "error",
            )
        )

    if not report.social_calendar:
        issues.append(
            ReportIssue(
                "social_calendar",
                "Social calendar is required",
                "error",
            )
        )

    if not report.action_plan:
        issues.append(
            ReportIssue(
                "action_plan",
                "Action plan is required",
                "error",
            )
        )

    # 2. Scan all text for prohibited phrases and placeholders
    for field_path, text in iter_report_text_fields(report):
        if not text or not isinstance(text, str):
            continue

        # Check for prohibited phrases
        prohibited = _contains_prohibited_phrase(text)
        if prohibited:
            issues.append(
                ReportIssue(
                    field_path,
                    f'Contains prohibited phrase "{prohibited}"',
                    "error",
                )
            )

        # Check for bracketed placeholders
        bracket_placeholder = _contains_bracket_placeholder(text)
        if bracket_placeholder:
            issues.append(
                ReportIssue(
                    field_path,
                    f'Contains placeholder "{bracket_placeholder}"',
                    "error",
                )
            )

    # 3. Validate marketing plan structure
    mp = report.marketing_plan

    # Executive summary depth
    if mp.executive_summary and len(mp.executive_summary.strip()) < 50:
        issues.append(
            ReportIssue(
                "marketing_plan.executive_summary",
                "Executive summary is too brief (minimum 50 characters)",
                "warning",
            )
        )

    # Situation analysis depth
    if mp.situation_analysis and len(mp.situation_analysis.strip()) < 100:
        issues.append(
            ReportIssue(
                "marketing_plan.situation_analysis",
                "Situation analysis is too brief (minimum 100 characters)",
                "warning",
            )
        )

    # Strategy depth
    if mp.strategy and len(mp.strategy.strip()) < 100:
        issues.append(
            ReportIssue(
                "marketing_plan.strategy",
                "Strategy is too brief (minimum 100 characters)",
                "warning",
            )
        )

    # At least 3 pillars
    if len(mp.pillars) < 3:
        issues.append(
            ReportIssue(
                "marketing_plan.pillars",
                f"At least 3 strategic pillars required (found {len(mp.pillars)})",
                "error",
            )
        )

    # Pillars have meaningful names (not "Pillar 1", etc.)
    for i, pillar in enumerate(mp.pillars):
        if not pillar.name or pillar.name.lower() in (
            "pillar 1",
            "pillar 2",
            "pillar 3",
            "pillar 4",
            "pillar 5",
        ):
            issues.append(
                ReportIssue(
                    f"marketing_plan.pillars[{i}]",
                    "Pillar names must be customized (not generic like 'Pillar 1')",
                    "error",
                )
            )

        # Each pillar has description
        if not pillar.description or len(pillar.description.strip()) < 20:
            issues.append(
                ReportIssue(
                    f"marketing_plan.pillars[{i}]",
                    "Each pillar must have a description (minimum 20 characters)",
                    "warning",
                )
            )

    # 4. Validate campaign blueprint
    cb = report.campaign_blueprint

    # Big idea is present and named (not empty or generic)
    if not cb.big_idea or len(cb.big_idea.strip()) < 10:
        issues.append(
            ReportIssue(
                "campaign_blueprint.big_idea",
                "Campaign big idea must be present and meaningful (minimum 10 characters)",
                "error",
            )
        )

    # Big idea is named (not generic)
    if cb.big_idea and cb.big_idea.lower() in ("campaign 1", "new campaign", "campaign"):
        issues.append(
            ReportIssue(
                "campaign_blueprint.big_idea",
                "Campaign big idea must be named (not generic like 'Campaign 1')",
                "error",
            )
        )

    # Objective is present
    if not cb.objective or not cb.objective.primary:
        issues.append(
            ReportIssue(
                "campaign_blueprint.objective",
                "Campaign objective is required",
                "error",
            )
        )

    # 5. Validate social calendar
    cal = report.social_calendar

    # At least 7 posts
    if len(cal.posts) < 7:
        issues.append(
            ReportIssue(
                "social_calendar.posts",
                f"At least 7 calendar posts required (found {len(cal.posts)})",
                "error",
            )
        )

    # Posts have hooks and CTAs (not placeholder)
    for i, post in enumerate(cal.posts):
        if not post.hook or post.hook.lower() == "hook idea for day":
            issues.append(
                ReportIssue(
                    f"social_calendar.posts[{i}]",
                    "Post hook must be specific (not 'Hook idea for day')",
                    "error",
                )
            )

        if not post.cta or post.cta.lower() in ("cta", "call to action", "to be determined"):
            issues.append(
                ReportIssue(
                    f"social_calendar.posts[{i}]",
                    "Post CTA must be specific",
                    "error",
                )
            )

    # 6. Validate action plan
    if report.action_plan:
        ap = report.action_plan

        # At least 5 total actions
        total_actions = len(ap.quick_wins) + len(ap.next_10_days) + len(ap.next_30_days)
        if total_actions < 5:
            issues.append(
                ReportIssue(
                    "action_plan",
                    f"At least 5 total actions required across all timeframes (found {total_actions})",
                    "error",
                )
            )

        # Actions are not generic
        for i, action in enumerate(ap.quick_wins):
            if action.lower() in ("improve social media", "increase engagement", "tbd"):
                issues.append(
                    ReportIssue(
                        f"action_plan.quick_wins[{i}]",
                        "Actions must be specific (not generic like 'improve social media')",
                        "error",
                    )
                )

        for i, action in enumerate(ap.next_10_days):
            if action.lower() in ("improve social media", "increase engagement", "tbd"):
                issues.append(
                    ReportIssue(
                        f"action_plan.next_10_days[{i}]",
                        "Actions must be specific (not generic like 'improve social media')",
                        "error",
                    )
                )

        for i, action in enumerate(ap.next_30_days):
            if action.lower() in ("improve social media", "increase engagement", "tbd"):
                issues.append(
                    ReportIssue(
                        f"action_plan.next_30_days[{i}]",
                        "Actions must be specific (not generic like 'improve social media')",
                        "error",
                    )
                )

    logger.info(
        f"Report validation complete: {len(issues)} issue(s) found "
        f"({sum(1 for i in issues if i.severity == 'error')} error, "
        f"{sum(1 for i in issues if i.severity == 'warning')} warning)"
    )

    return issues


def has_blocking_issues(issues: List[ReportIssue]) -> bool:
    """Check if any error-level issues present (would block export)."""
    return any(issue.severity == "error" for issue in issues)
