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

PDF_TEMPLATE_MAP = {
    "quick_social_basic": "quick_social_basic.html",
    "strategy_campaign_standard": "campaign_strategy.html",
    "full_funnel_growth_suite": "full_funnel_growth.html",
    "launch_gtm_pack": "launch_gtm.html",
    "brand_turnaround_lab": "brand_turnaround.html",
    "retention_crm_booster": "retention_crm.html",
    "performance_audit_revamp": "performance_audit.html",
}


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


def build_pdf_context_for_wow_package(
    report_data: Dict[str, Any], wow_package_key: str
) -> Dict[str, Any]:
    """
    Take raw report_data dict and flatten it into a template-friendly context
    depending on the WOW package.

    This is the ONLY place that knows how to map internal report structure
    to PDF template variables.

    Args:
        report_data: Raw report dict (may be nested)
        wow_package_key: WOW package identifier

    Returns:
        Flattened context dict with template-ready keys

    Design:
        Each WOW package gets a specific set of context keys that match
        what its template expects. This decouples report structure from
        template expectations.
    """
    # Quick Social Pack - lightweight social media playbook
    if wow_package_key == "quick_social_basic":
        return {
            "brand_name": report_data.get("brand_name")
            or report_data.get("brand", {}).get("name")
            or "Your Brand",
            "campaign_title": report_data.get("campaign_title")
            or report_data.get("title")
            or "Quick Social Playbook",
            "primary_channel": report_data.get("primary_channel") or "Instagram",
            "overview_html": report_data.get("overview_html") or "",
            "audience_segments_html": report_data.get("audience_segments_html") or "",
            "messaging_framework_html": report_data.get("messaging_framework_html") or "",
            "content_buckets_html": report_data.get("content_buckets_html") or "",
            "calendar_html": report_data.get("calendar_html") or "",
            "creative_direction_html": report_data.get("creative_direction_html") or "",
            "hashtags_html": report_data.get("hashtags_html") or "",
            "platform_guidelines_html": report_data.get("platform_guidelines_html") or "",
            "kpi_plan_html": report_data.get("kpi_plan_html") or "",
            "final_summary_html": report_data.get("final_summary_html") or "",
        }

    # Strategy/Campaign Pack - full campaign deck
    if wow_package_key == "strategy_campaign_standard":
        return {
            "brand_name": report_data.get("brand_name")
            or report_data.get("brand", {}).get("name")
            or "Brand",
            "campaign_title": report_data.get("campaign_title") or "Campaign Strategy",
            "campaign_duration": report_data.get("campaign_duration") or "",
            "objectives_html": report_data.get("objectives_html")
            or report_data.get("objectives_md")
            or "",
            "core_campaign_idea_html": report_data.get("core_campaign_idea_html")
            or report_data.get("core_campaign_idea_md")
            or "",
            "competitor_snapshot": report_data.get("competitor_snapshot") or [],
            "channel_plan_html": report_data.get("channel_plan_html")
            or report_data.get("channel_plan_md")
            or "",
            "audience_segments_html": report_data.get("audience_segments_html")
            or report_data.get("audience_segments_md")
            or "",
            "personas": report_data.get("personas") or [],
            "roi_model": report_data.get("roi_model") or {},
            "creative_direction_html": report_data.get("creative_direction_html")
            or report_data.get("creative_direction_md")
            or "",
            "brand_identity": report_data.get("brand_identity") or {},
            "calendar_html": report_data.get("calendar_html")
            or report_data.get("calendar_md")
            or "",
            "ad_concepts_html": report_data.get("ad_concepts_html")
            or report_data.get("ad_concepts_md")
            or "",
            "kpi_budget_html": report_data.get("kpi_budget_html")
            or report_data.get("kpi_budget_md")
            or "",
            "execution_html": report_data.get("execution_html")
            or report_data.get("execution_md")
            or "",
            "post_campaign_html": report_data.get("post_campaign_html")
            or report_data.get("post_campaign_md")
            or "",
            "final_summary_html": report_data.get("final_summary_html")
            or report_data.get("final_summary_md")
            or "",
        }

    # Generic fallback for unknown packages
    return {
        "brand_name": report_data.get("brand_name") or "Brand",
        "campaign_title": report_data.get("campaign_title") or "Campaign",
        "overview_html": report_data.get("overview_html") or "",
    }


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
