"""
Agency-Grade PDF Renderer for AICMO Reports

Renders HTML templates with context data to PDF bytes using WeasyPrint.
Provides a clean abstraction for PDF generation with proper error handling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Guarded WeasyPrint import
try:
    from weasyprint import HTML, CSS

    WEASYPRINT_AVAILABLE = True
except Exception:
    HTML = None  # type: ignore
    CSS = None  # type: ignore
    WEASYPRINT_AVAILABLE = False

logger = logging.getLogger("aicmo.pdf_renderer")


def render_pdf_from_context(
    template_name: str,
    context: Dict[str, Any],
    base_url: Optional[str] = None,
) -> bytes:
    """
    Renders an agency-grade PDF from an HTML template + context.

    Args:
        template_name: Name of template file (e.g., 'strategy_campaign_standard.html')
        context: Dictionary of template variables
        base_url: Base URL for relative references in HTML/CSS

    Returns:
        PDF file as bytes (starts with b'%PDF')

    Raises:
        ImportError: If WeasyPrint is not installed
        FileNotFoundError: If template file doesn't exist
        RuntimeError: If PDF generation fails
    """
    try:
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML
    except ImportError as e:
        raise ImportError(
            "WeasyPrint and Jinja2 are required for PDF rendering. "
            "Install with: pip install weasyprint jinja2"
        ) from e

    # Set up Jinja2 environment
    templates_dir = Path(__file__).parent / "templates"

    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=True,
    )

    # Load and render template
    try:
        template = env.get_template(template_name)
        html_str = template.render(**context)
    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        raise

    # Generate PDF
    try:
        if base_url is None:
            base_url = str(templates_dir)

        pdf_bytes = HTML(string=html_str, base_url=base_url).write_pdf()

        if not pdf_bytes:
            raise RuntimeError("PDF generation returned empty bytes")

        # Validate PDF header
        if not pdf_bytes.startswith(b"%PDF"):
            raise RuntimeError(
                "Generated PDF bytes do not start with '%PDF' header. "
                "PDF generation may have failed."
            )

        logger.info(f"PDF rendered successfully: {template_name} ({len(pdf_bytes)} bytes)")
        return pdf_bytes

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise RuntimeError(f"PDF generation failed: {e}") from e


def sections_to_html_list(sections: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Convert markdown sections to HTML-ready sections for template injection.

    Args:
        sections: List of {'id', 'title', 'body'} dicts with markdown body

    Returns:
        List of {'id', 'title', 'body'} dicts with HTML body

    Note: This is a simple passthrough for now. In production, you'd use
    markdown2 or similar to convert markdown → HTML per section.
    """
    try:
        import markdown
    except ImportError:
        # Fallback: just escape HTML entities
        import html

        html_sections = []
        for section in sections:
            body = section.get("body", "")
            # Simple conversion: wrap in <p> tags
            body_html = "<p>" + html.escape(body) + "</p>"
            html_sections.append(
                {
                    "id": section.get("id"),
                    "title": section.get("title"),
                    "body": body_html,
                    "callouts": section.get("callouts"),
                }
            )
        return html_sections

    # With markdown available, do proper conversion
    html_sections = []
    for section in sections:
        body = section.get("body", "")
        body_html = markdown.markdown(body)
        html_sections.append(
            {
                "id": section.get("id"),
                "title": section.get("title"),
                "body": body_html,
                "callouts": section.get("callouts"),
            }
        )
    return html_sections


def _render_pdf_html(template_name: str, context: Dict[str, Any]) -> str:
    """
    INTERNAL: Render an HTML template with Jinja2 (without PDF generation).

    This helper is used internally for testing and by render_html_template_to_pdf.

    Args:
        template_name: Name of the Jinja2 template file
        context: Dictionary of template variables

    Returns:
        Rendered HTML string

    Raises:
        RuntimeError: If template rendering fails
    """
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError as e:
        raise RuntimeError("Jinja2 is not available") from e

    template_dir = Path(__file__).parent / "templates" / "pdf"

    if not template_dir.exists():
        raise RuntimeError(f"PDF template directory not found: {template_dir}")

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    try:
        template = env.get_template(template_name)
        html_str = template.render(**context)
        return html_str
    except Exception as e:
        logger.error(f"Template rendering failed for {template_name}: {e}")
        raise RuntimeError(f"Template rendering failed: {e}") from e


def render_html_template_to_pdf(template_name: str, context: Dict[str, Any]) -> bytes:
    """
    Render an HTML template with Jinja2 and convert it to PDF using WeasyPrint.

    This is an ADDITIVE function that does not change existing behavior.
    Raises RuntimeError if WeasyPrint is not available.

    Args:
        template_name: Name of the Jinja2 template file
        context: Dictionary of template variables

    Returns:
        PDF file as bytes

    Raises:
        RuntimeError: If WeasyPrint is not available or template not found
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint is not available; cannot render HTML to PDF. "
            "Install with: pip install weasyprint jinja2"
        )

    # Render HTML using internal helper
    html_str = _render_pdf_html(template_name, context)

    # Render HTML to PDF with optional CSS
    template_dir = Path(__file__).parent / "templates" / "pdf"

    try:
        css_path = template_dir / "styles.css"
        stylesheets = []

        if css_path.exists():
            stylesheets.append(CSS(filename=str(css_path)))

        pdf_bytes = HTML(string=html_str, base_url=str(template_dir)).write_pdf(
            stylesheets=stylesheets if stylesheets else None
        )

        if not pdf_bytes:
            raise RuntimeError("PDF generation returned empty bytes")

        if not pdf_bytes.startswith(b"%PDF"):
            raise RuntimeError("Generated PDF bytes do not start with '%PDF' header")

        logger.info(f"Agency PDF rendered: {template_name} ({len(pdf_bytes)} bytes)")
        return pdf_bytes

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise RuntimeError(f"PDF generation failed: {e}") from e


# ============================================================================
# PDF TEMPLATE MAP - One canonical template per WOW package
# ============================================================================

# Only include packs that actually have HTML templates in backend/templates/pdf
PDF_TEMPLATE_MAP = {
    "quick_social_basic": "quick_social_basic.html",
    "strategy_campaign_standard": "campaign_strategy.html",
    "strategy_campaign_basic": "campaign_strategy.html",  # Shares template
    "strategy_campaign_premium": "campaign_strategy.html",  # Shares template
    "strategy_campaign_enterprise": "campaign_strategy.html",  # Shares template
    "full_funnel_growth_suite": "full_funnel_growth.html",
    "launch_gtm_pack": "launch_gtm.html",
    "brand_turnaround_lab": "brand_turnaround.html",
    "retention_crm_booster": "retention_crm.html",
    "performance_audit_revamp": "performance_audit.html",
}


def convert_markdown_to_html(md_text: str) -> str:
    """Convert markdown text to HTML using markdown library."""
    if not md_text or not md_text.strip():
        return ""
    try:
        import markdown

        return markdown.markdown(md_text)
    except ImportError:
        import html

        return f"<p>{html.escape(md_text)}</p>"


def resolve_pdf_template_for_pack(wow_package_key: str) -> str:
    """
    Resolve which PDF template to use for a given WOW package.

    This is the ONLY source of truth for pack → template mapping.

    Args:
        wow_package_key: The WOW package key (e.g., "quick_social_basic")

    Returns:
        Template filename to use (defaults to "campaign_strategy.html" if unknown)
    """
    if not wow_package_key:
        template_name = "campaign_strategy.html"
    else:
        template_name = PDF_TEMPLATE_MAP.get(wow_package_key, "campaign_strategy.html")

    print(
        "📋 PDF TEMPLATE DEBUG:",
        "wow_package_key=",
        wow_package_key,
        "template=",
        template_name,
    )
    return template_name


# ============================================================================
# PDF CONTEXT BUILDER - Flatten report data into template-friendly context
# ============================================================================


# Section ID to template field mappings for each WOW package
QUICK_SOCIAL_SECTION_MAP = {
    "overview": "overview_html",
    "audience_segments": "audience_segments_html",
    "messaging_framework": "messaging_framework_html",
    "content_buckets": "content_buckets_html",
    "detailed_30day_calendar": "calendar_html",
    "detailed_30_day_calendar": "calendar_html",
    "creative_direction": "creative_direction_html",
    "hashtag_strategy": "hashtags_html",
    "platform_guidelines": "platform_guidelines_html",
    "kpi_plan_light": "kpi_plan_html",
    "execution_roadmap": "kpi_plan_html",  # Maps to same field as kpi (combined in PDF)
    "final_summary": "final_summary_html",
}

# WOW Template display headers to section ID mapping (for parsing WOW markdown)
# This maps the actual ## headers in WOW templates back to section IDs
QUICK_SOCIAL_HEADER_MAP = {
    "Brand & Context Snapshot": "overview",
    "Brand and Context Snapshot": "overview",  # Variant
    "Messaging Framework": "messaging_framework",
    "Your Core Message": "messaging_framework",  # PDF display name
    "30-Day Content Calendar": "detailed_30_day_calendar",
    "Weekly Posting Schedule": "detailed_30_day_calendar",  # PDF display name
    "Content Buckets & Themes": "content_buckets",
    "Content Buckets and Themes": "content_buckets",  # Variant
    "Content Themes": "content_buckets",  # PDF display name
    "Hashtag Strategy": "hashtag_strategy",
    "Hashtags to Use": "hashtag_strategy",  # PDF display name
    "Platform Guidelines": "platform_guidelines",
    "Platform-Specific Tips": "platform_guidelines",  # PDF display name
    "KPIs & Lightweight Measurement Plan": "kpi_plan_light",
    "KPIs and Lightweight Measurement Plan": "kpi_plan_light",  # Variant
    "Success Metrics": "kpi_plan_light",  # PDF display name
    "Execution Roadmap": "execution_roadmap",
    "Final Summary & Next Steps": "final_summary",
    "Final Summary and Next Steps": "final_summary",  # Variant
    "Next Steps": "final_summary",  # PDF display name
}

# Strategy + Campaign Standard/Premium/Enterprise share same template
# Template has fewer fields than sections, so some sections merge into same fields
STRATEGY_CAMPAIGN_SECTION_MAP = {
    "overview": "objectives_html",
    "campaign_objective": "objectives_html",
    "core_campaign_idea": "core_campaign_idea_html",
    "messaging_framework": "objectives_html",  # Merge with overview/objectives
    "channel_plan": "channel_plan_html",
    "audience_segments": "audience_segments_html",
    "persona_cards": "audience_segments_html",  # Merge with segments, or use structured personas
    "creative_direction": "creative_direction_html",
    "influencer_strategy": "channel_plan_html",  # Merge into channel strategy
    "promotions_and_offers": "core_campaign_idea_html",  # Merge into big idea
    "detailed_30_day_calendar": "calendar_html",
    "email_and_crm_flows": "channel_plan_html",  # Merge into channel
    "ad_concepts": "ad_concepts_html",
    "kpi_and_budget_plan": "kpi_budget_html",
    "execution_roadmap": "execution_html",
    "post_campaign_analysis": "post_campaign_html",
    "final_summary": "final_summary_html",
    # Premium tier additions
    "value_proposition_map": "core_campaign_idea_html",  # Merge with big idea
    "creative_territories": "creative_direction_html",
    "copy_variants": "ad_concepts_html",
    "ugc_and_community_plan": "channel_plan_html",
    "funnel_breakdown": "objectives_html",
    "awareness_strategy": "channel_plan_html",
    "consideration_strategy": "channel_plan_html",
    "conversion_strategy": "channel_plan_html",
    "retention_strategy": "channel_plan_html",
    "sms_and_whatsapp_strategy": "channel_plan_html",
    "remarketing_strategy": "channel_plan_html",
    "measurement_framework": "kpi_budget_html",
    "optimization_opportunities": "post_campaign_html",
    # Enterprise tier additions
    "industry_landscape": "objectives_html",
    "market_analysis": "objectives_html",
    "competitor_analysis": "objectives_html",
    "customer_insights": "audience_segments_html",
    "brand_positioning": "core_campaign_idea_html",
    "customer_journey_map": "audience_segments_html",
    "risk_assessment": "execution_html",
    "strategic_recommendations": "post_campaign_html",
    "cxo_summary": "final_summary_html",
}

# Full-Funnel Growth Suite - template has good 1:1 mapping with sections
FULL_FUNNEL_SECTION_MAP = {
    "overview": "overview_html",
    "market_landscape": "market_landscape_html",
    "competitor_analysis": "competitor_analysis_html",
    "funnel_breakdown": "funnel_breakdown_html",
    "audience_segments": "audience_segments_html",
    "persona_cards": "audience_segments_html",  # Merge with audience_segments, structured personas not supported yet
    "value_proposition_map": "value_proposition_html",
    "messaging_framework": "messaging_framework_html",
    "awareness_strategy": "awareness_strategy_html",
    "consideration_strategy": "consideration_strategy_html",
    "conversion_strategy": "conversion_strategy_html",
    "retention_strategy": "retention_strategy_html",
    "landing_page_blueprint": "landing_page_html",
    "email_automation_flows": "email_flows_html",
    "remarketing_strategy": "remarketing_html",
    "ad_concepts_multi_platform": "ad_concepts_html",
    "creative_direction": "creative_direction_html",
    "full_30_day_calendar": "calendar_html",
    "kpi_and_budget_plan": "kpi_budget_html",
    "measurement_framework": "measurement_html",
    "execution_roadmap": "execution_html",
    "optimization_opportunities": "optimization_html",
    "final_summary": "final_summary_html",
}

# Launch & GTM Pack
LAUNCH_GTM_SECTION_MAP = {
    "overview": "overview_html",
    "market_landscape": "market_landscape_html",
    "product_positioning": "positioning_html",
    "messaging_framework": "messaging_framework_html",
    "launch_phases": "launch_phases_html",
    "channel_plan": "channel_plan_html",
    "audience_segments": "audience_segments_html",
    "creative_direction": "creative_direction_html",
    "launch_campaign_ideas": "campaign_ideas_html",
    "content_calendar_launch": "calendar_html",
    "ad_concepts": "ad_concepts_html",
    "execution_roadmap": "execution_html",
    "final_summary": "final_summary_html",
}

# Brand Turnaround Lab
BRAND_TURNAROUND_SECTION_MAP = {
    "overview": "overview_html",
    "brand_audit": "brand_audit_html",
    "customer_insights": "customer_insights_html",
    "competitor_analysis": "competitor_analysis_html",
    "problem_diagnosis": "problem_diagnosis_html",
    "new_positioning": "positioning_html",
    "messaging_framework": "messaging_framework_html",
    "creative_direction": "creative_direction_html",
    "channel_reset_strategy": "channel_strategy_html",
    "reputation_recovery_plan": "reputation_recovery_html",
    "promotions_and_offers": "promotions_html",
    "30_day_recovery_calendar": "calendar_html",
    "execution_roadmap": "execution_html",
    "final_summary": "final_summary_html",
}

# Retention & CRM Booster
RETENTION_CRM_SECTION_MAP = {
    "overview": "overview_html",
    "customer_segments": "customer_segments_html",
    "persona_cards": "customer_segments_html",  # Merge with segments, structured personas not supported yet
    "customer_journey_map": "journey_map_html",
    "churn_diagnosis": "churn_diagnosis_html",
    "email_automation_flows": "email_flows_html",
    "sms_and_whatsapp_flows": "sms_flows_html",
    "loyalty_program_concepts": "loyalty_program_html",
    "winback_sequence": "winback_html",
    "post_purchase_experience": "post_purchase_html",
    "ugc_and_community_plan": "ugc_community_html",
    "kpi_plan_retention": "kpi_plan_html",
    "execution_roadmap": "execution_html",
    "final_summary": "final_summary_html",
}

# Performance Audit & Revamp
PERFORMANCE_AUDIT_SECTION_MAP = {
    "overview": "overview_html",
    "account_audit": "account_audit_html",
    "campaign_level_findings": "campaign_findings_html",
    "creative_performance_analysis": "creative_performance_html",
    "audience_analysis": "audience_analysis_html",
    "funnel_breakdown": "funnel_breakdown_html",
    "competitor_benchmark": "competitor_benchmark_html",
    "problem_diagnosis": "problem_diagnosis_html",
    "revamp_strategy": "revamp_strategy_html",
    "new_ad_concepts": "new_ad_concepts_html",
    "creative_direction": "creative_direction_html",
    "conversion_audit": "conversion_audit_html",
    "remarketing_strategy": "remarketing_html",
    "kpi_reset_plan": "kpi_reset_html",
    "execution_roadmap": "execution_html",
    "final_summary": "final_summary_html",
}

# Central registry: pack_key → section mapping dict
PACK_SECTION_MAPS = {
    "quick_social_basic": QUICK_SOCIAL_SECTION_MAP,
    "strategy_campaign_standard": STRATEGY_CAMPAIGN_SECTION_MAP,
    "strategy_campaign_basic": STRATEGY_CAMPAIGN_SECTION_MAP,  # Shares template
    "strategy_campaign_premium": STRATEGY_CAMPAIGN_SECTION_MAP,  # Shares template
    "strategy_campaign_enterprise": STRATEGY_CAMPAIGN_SECTION_MAP,  # Shares template
    "full_funnel_growth_suite": FULL_FUNNEL_SECTION_MAP,
    "launch_gtm_pack": LAUNCH_GTM_SECTION_MAP,
    "brand_turnaround_lab": BRAND_TURNAROUND_SECTION_MAP,
    "retention_crm_booster": RETENTION_CRM_SECTION_MAP,
    "performance_audit_revamp": PERFORMANCE_AUDIT_SECTION_MAP,
}


def build_pdf_context_for_wow_package(
    report_data: Dict[str, Any], wow_package_key: str
) -> Dict[str, Any]:
    """
    Take raw report_data dict and flatten it into a template-friendly context.

    ENHANCED: Now converts markdown sections to HTML automatically.

    Process:
    1. Extract base metadata (brand_name, campaign_title, etc.)
    2. Look for `sections` list in report_data
    3. Convert each section's markdown body to HTML
    4. Map section IDs to template field names using pack-specific mappings
    5. Return flattened context dict

    Args:
        report_data: Raw report dict with optional `sections` list
        wow_package_key: WOW package identifier

    Returns:
        Flattened context dict with *_html fields populated
    """
    # Base context with metadata
    base_context = {
        "brand_name": report_data.get("brand_name")
        or report_data.get("brand", {}).get("name")
        or "Your Brand",
        "campaign_title": report_data.get("campaign_title")
        or report_data.get("title")
        or "Campaign",
        "primary_channel": report_data.get("primary_channel") or "Instagram",
        # Initialize structured data fields as empty for templates that expect them
        "personas": [],
        "competitor_snapshot": [],
        "roi_model": {},
        "brand_identity": {},
    }

    # Select section mapping from central registry
    section_map = PACK_SECTION_MAPS.get(wow_package_key, {})

    # Process sections if available
    sections = report_data.get("sections", [])

    if sections and section_map:
        # Get header map for this package (for WOW markdown parsing)
        header_map = {}
        if wow_package_key == "quick_social_basic":
            header_map = QUICK_SOCIAL_HEADER_MAP

        # Track accumulated content for fields that combine multiple sections
        field_accumulator = {}

        for section in sections:
            section_id = section.get("id", "")
            section_title = section.get("title", "")

            # Try direct section_id match first
            html_field_name = section_map.get(section_id)

            # If not found, try header map (WOW display name → section ID → html field)
            if not html_field_name and section_title and header_map:
                mapped_section_id = header_map.get(section_title)
                if mapped_section_id:
                    html_field_name = section_map.get(mapped_section_id)

            # Fuzzy matching: check if section_id starts with any key in map
            if not html_field_name:
                for map_key, map_value in section_map.items():
                    if section_id.startswith(map_key):
                        html_field_name = map_value
                        break

            if html_field_name:
                # Convert markdown body to HTML
                markdown_body = section.get("body", "")
                html_body = convert_markdown_to_html(markdown_body)

                # For Quick Social: combine kpi_plan_light + execution_roadmap into one field
                if wow_package_key == "quick_social_basic" and html_field_name == "kpi_plan_html":
                    if html_field_name not in field_accumulator:
                        field_accumulator[html_field_name] = []
                    field_accumulator[html_field_name].append(html_body)
                else:
                    base_context[html_field_name] = html_body

        # Merge accumulated fields
        for field_name, html_parts in field_accumulator.items():
            base_context[field_name] = "\n\n".join(html_parts)

    # Fallback: Check for pre-converted *_md or *_html fields
    if wow_package_key == "quick_social_basic":
        for section_id, html_field in QUICK_SOCIAL_SECTION_MAP.items():
            if html_field not in base_context or not base_context[html_field]:
                # Try *_md field
                md_field = html_field.replace("_html", "_md")
                base_context[html_field] = (
                    report_data.get(html_field)
                    or convert_markdown_to_html(report_data.get(md_field, ""))
                    or ""
                )

    elif wow_package_key == "strategy_campaign_standard":
        base_context.update(
            {
                "campaign_duration": report_data.get("campaign_duration") or "",
                "competitor_snapshot": report_data.get("competitor_snapshot") or [],
                "personas": report_data.get("personas") or [],
                "roi_model": report_data.get("roi_model") or {},
                "brand_identity": report_data.get("brand_identity") or {},
            }
        )
        for section_id, html_field in STRATEGY_CAMPAIGN_SECTION_MAP.items():
            if html_field not in base_context or not base_context[html_field]:
                md_field = html_field.replace("_html", "_md")
                base_context[html_field] = (
                    report_data.get(html_field)
                    or convert_markdown_to_html(report_data.get(md_field, ""))
                    or ""
                )

    # Create a copy to pass as 'report' for templates that use report.get()
    # This allows both {{ field_name }} and {{ report.get('field_name') }} patterns
    result = dict(base_context)
    result["report"] = base_context

    return result


def render_agency_pdf(report_data: Dict[str, Any], wow_package_key: str) -> bytes:
    """
    Entry point for generating the full agency-grade PDF.

    Uses a pack-specific template with a flattened, template-friendly context.
    This does NOT replace the existing ReportLab-based PDFs; it is only used
    when explicitly requested via the UI toggle.

    Args:
        report_data: Raw report dict (may be nested)
        wow_package_key: WOW package identifier (e.g., "quick_social_basic")

    Returns:
        PDF file as bytes

    Raises:
        RuntimeError: If template rendering or PDF generation fails

    Design:
        1. Resolve template name from wow_package_key
        2. Build flattened context via build_pdf_context_for_wow_package
        3. Render HTML template with context
        4. Convert HTML to PDF with WeasyPrint + CSS
    """
    template_name = resolve_pdf_template_for_pack(wow_package_key)
    pdf_context = build_pdf_context_for_wow_package(report_data, wow_package_key)

    print("\n" + "=" * 80)
    print("🎨 RENDER_AGENCY_PDF DEBUG:")
    print(f"   wow_package_key     = {wow_package_key}")
    print(f"   template_name       = {template_name}")
    print(f"   context_keys        = {sorted(pdf_context.keys())}")
    print("=" * 80 + "\n")

    return render_html_template_to_pdf(template_name, pdf_context)
