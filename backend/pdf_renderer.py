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


# FIX #3: Map WOW package to appropriate PDF template
TEMPLATE_BY_WOW_PACKAGE = {
    "quick_social_basic": "quick_social_basic.html",
    "strategy_campaign_standard": "campaign_strategy.html",  # Default/standard
    "full_funnel_growth_suite": "full_funnel_growth.html",
    "launch_gtm_pack": "launch_gtm.html",
    "brand_turnaround_lab": "brand_turnaround.html",
    "retention_crm_booster": "retention_crm.html",
    "performance_audit_revamp": "performance_audit.html",
}


def resolve_pdf_template_for_pack(wow_package_key: Optional[str]) -> str:
    """
    Resolve which PDF template to use for a given WOW package.

    Args:
        wow_package_key: The WOW package key (e.g., "quick_social_basic")

    Returns:
        Template filename to use (defaults to "campaign_strategy.html" if unknown)
    """
    if not wow_package_key:
        return "campaign_strategy.html"

    return TEMPLATE_BY_WOW_PACKAGE.get(wow_package_key, "campaign_strategy.html")


def render_agency_pdf(context: Dict[str, Any]) -> bytes:
    """
    Entry point for generating the full agency-grade PDF.

    Uses a pack-specific template that includes appropriate sections and design elements.
    This does NOT replace the existing ReportLab-based PDFs; it is only used
    when explicitly requested via the UI toggle.

    Args:
        context: Dictionary containing report data to pass to template
                 Should include 'wow_package_key' for proper template selection

    Returns:
        PDF file as bytes

    Raises:
        RuntimeError: If template rendering or PDF generation fails
    """
    # FIX #3: Select template based on WOW package, not hardcoded
    wow_package_key = context.get("wow_package_key")
    template_name = resolve_pdf_template_for_pack(wow_package_key)

    return render_html_template_to_pdf(template_name, context)
