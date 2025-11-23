"""
AICMO Agency-Grade Processor

Orchestrates framework injection, language filtering, and reasoning trace
for agency-grade report generation.

This module sits between raw generation and final output, applying
strategic frameworks and language polishing when agency_grade=True.
"""

import logging
from typing import Dict, Optional

from aicmo.io.client_reports import AICMOOutputReport
from aicmo.presets.framework_fusion import inject_frameworks
from aicmo.generators.language_filters import apply_all_filters
from aicmo.generators.reasoning_trace import attach_reasoning_trace, strip_reasoning_trace

logger = logging.getLogger("aicmo.agency_grade")


def process_report_for_agency_grade(
    report: AICMOOutputReport,
    brief_text: str,
    learning_context_raw: str = "",
    learning_context_struct: Optional[Dict[str, str]] = None,
    include_reasoning_trace: bool = False,
) -> AICMOOutputReport:
    """
    Apply agency-grade transformations to a report.

    Sequence:
    1. If learning_context_struct available: inject frameworks into text sections
    2. Apply language filters (blacklist removal, premium language, copywriting patterns)
    3. Optionally attach reasoning trace for internal review
    4. Return enhanced report

    Args:
        report: Base AICMO output report to enhance
        brief_text: Original client brief text (for framework context)
        learning_context_raw: Raw learned context from memory (optional)
        learning_context_struct: Structured learning context dict (optional)
        include_reasoning_trace: Whether to attach reasoning trace (internal use only)

    Returns:
        Enhanced AICMOOutputReport with agency-grade transformations applied

    Design:
        - Non-breaking: if learning context missing, skips framework injection
        - Non-blocking: if language filters fail, continues with basic enhancement
        - Graceful degradation: each step is independent and can fail safely
    """

    if not report:
        logger.warning("process_report_for_agency_grade called with None report")
        return report

    try:
        # Step 1: Inject frameworks if learning context available
        if learning_context_struct:
            _inject_frameworks_into_report(report, brief_text, learning_context_struct)

        # Step 2: Apply language filters to text sections
        _apply_language_filters_to_report(report)

        # Step 3: Optionally attach reasoning trace
        if include_reasoning_trace and learning_context_raw:
            _attach_reasoning_trace_to_report(report, brief_text, learning_context_raw)

        logger.info("✅ Agency-grade processing complete")

    except Exception as e:
        logger.debug(f"Agency-grade processing failed (non-critical): {e}", exc_info=False)

    return report


def _inject_frameworks_into_report(
    report: AICMOOutputReport,
    brief_text: str,
    learning_context_struct: Dict[str, str],
) -> None:
    """
    Inject strategic frameworks into key report sections.

    Applies to: marketing_plan, campaign_blueprint, strategy narrative
    """
    try:
        frameworks_str = learning_context_struct.get("core_frameworks", "")
        if not frameworks_str:
            logger.debug("No core_frameworks in learning context, skipping framework injection")
            return

        # Inject into marketing plan if it exists
        if hasattr(report, "marketing_plan") and report.marketing_plan:
            if hasattr(report.marketing_plan, "strategy"):
                original_strategy = report.marketing_plan.strategy or ""
                report.marketing_plan.strategy = inject_frameworks(
                    brief=brief_text,
                    base_draft=original_strategy,
                    learning_context=frameworks_str,
                )
                logger.info("Injected frameworks into marketing_plan.strategy")

        # Inject into campaign blueprint if it exists and is a dict
        if hasattr(report, "campaign_blueprint") and isinstance(report.campaign_blueprint, dict):
            if "briefing" in report.campaign_blueprint:
                original_briefing = report.campaign_blueprint["briefing"] or ""
                report.campaign_blueprint["briefing"] = inject_frameworks(
                    brief=brief_text,
                    base_draft=original_briefing,
                    learning_context=frameworks_str,
                )
                logger.info("Injected frameworks into campaign_blueprint.briefing")

        # Inject into creative direction if available
        if hasattr(report, "extra_sections") and isinstance(report.extra_sections, dict):
            if "Creative Direction" in report.extra_sections:
                original_creative = report.extra_sections["Creative Direction"] or ""
                report.extra_sections["Creative Direction"] = inject_frameworks(
                    brief=brief_text,
                    base_draft=original_creative,
                    learning_context=frameworks_str,
                )
                logger.info("Injected frameworks into Creative Direction section")

        logger.info("Framework injection complete")

    except Exception as e:
        logger.debug(f"Framework injection failed (non-critical): {e}", exc_info=False)


def _apply_language_filters_to_report(report: AICMOOutputReport) -> None:
    """
    Apply language filters to all text sections in the report.

    Removes blacklisted phrases, injects premium language, and corrects structure.
    """
    try:
        # Apply to marketing plan
        if hasattr(report, "marketing_plan") and report.marketing_plan:
            if hasattr(report.marketing_plan, "executive_summary"):
                if report.marketing_plan.executive_summary:
                    report.marketing_plan.executive_summary = apply_all_filters(
                        report.marketing_plan.executive_summary
                    )
                    logger.debug("Applied filters to marketing_plan.executive_summary")

            if hasattr(report.marketing_plan, "strategy"):
                if report.marketing_plan.strategy:
                    report.marketing_plan.strategy = apply_all_filters(
                        report.marketing_plan.strategy
                    )
                    logger.debug("Applied filters to marketing_plan.strategy")

        # Apply to campaign blueprint
        if hasattr(report, "campaign_blueprint") and isinstance(report.campaign_blueprint, dict):
            for key, value in report.campaign_blueprint.items():
                if isinstance(value, str):
                    report.campaign_blueprint[key] = apply_all_filters(value)
            logger.debug("Applied filters to campaign_blueprint sections")

        # Apply to extra sections
        if hasattr(report, "extra_sections") and isinstance(report.extra_sections, dict):
            for key, value in report.extra_sections.items():
                if isinstance(value, str):
                    report.extra_sections[key] = apply_all_filters(value)
            logger.info(f"Applied filters to {len(report.extra_sections)} extra sections")

        logger.info("Language filtering complete")

    except Exception as e:
        logger.debug(f"Language filtering failed (non-critical): {e}", exc_info=False)


def _attach_reasoning_trace_to_report(
    report: AICMOOutputReport,
    brief_text: str,
    learning_context_raw: str,
) -> None:
    """
    Optionally attach reasoning trace for internal operator review.

    This is marked as internal-only and can be stripped from client exports.
    """
    try:
        if not hasattr(report, "extra_sections"):
            report.extra_sections = {}

        # Format learning context as frameworks string
        frameworks_str = learning_context_raw[:500] if learning_context_raw else ""

        # Attach reasoning trace if strategy narrative exists
        if hasattr(report, "marketing_plan") and report.marketing_plan:
            if hasattr(report.marketing_plan, "strategy"):
                original_strategy = report.marketing_plan.strategy or ""
                trace = attach_reasoning_trace(
                    draft=original_strategy,
                    brief=brief_text,
                    frameworks_str=frameworks_str,
                    internal_only=True,
                )
                if trace != original_strategy:
                    report.marketing_plan.strategy = trace
                    logger.info("Attached reasoning trace (internal only)")

    except Exception as e:
        logger.debug(f"Reasoning trace attachment failed (non-critical): {e}", exc_info=False)


def should_strip_reasoning_trace_from_export(export_format: str) -> bool:
    """
    Determine if reasoning trace should be stripped for this export format.

    Reasoning trace is for internal operator review only.
    It should be removed from PDF, PPTX, and any client-facing exports.
    """
    return (
        strip_reasoning_trace.__wrapped__(export_format)
        if hasattr(strip_reasoning_trace, "__wrapped__")
        else export_format.lower() in ["pdf", "pptx", "powerpoint", "presentation"]
    )
