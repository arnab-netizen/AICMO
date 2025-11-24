"""
Agency-Grade PDF Renderer for AICMO Reports

Renders HTML templates with context data to PDF bytes using WeasyPrint.
Provides a clean abstraction for PDF generation with proper error handling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

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
