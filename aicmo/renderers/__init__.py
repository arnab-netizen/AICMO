"""Report rendering utilities for AICMO output.

Provides safe, chunked rendering of large markdown reports to Streamlit.
Handles token limits, truncation, and multi-section stitching.
"""

from aicmo.renderers.report_renderer import (
    render_full_report,
    stitch_sections,
    truncate_safe,
)

__all__ = [
    "render_full_report",
    "stitch_sections",
    "truncate_safe",
]
