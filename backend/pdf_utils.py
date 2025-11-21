"""Simple Text → PDF Helper using ReportLab."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def text_to_pdf_bytes(text: str) -> bytes:
    """
    Very simple text-to-PDF converter.
    For real client use, you may want styling & page breaks.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # basic text layout
    x_margin = 50
    y = height - 50
    line_height = 14

    for line in text.splitlines():
        if y <= 50:  # new page
            c.showPage()
            y = height - 50
        c.drawString(x_margin, y, line)
        y -= line_height

    c.save()
    buffer.seek(0)
    return buffer.read()
