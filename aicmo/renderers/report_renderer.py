"""Safe rendering of large markdown reports in Streamlit.

Prevents truncation of long reports by chunking output and using
pagination with Streamlit components.
"""

from typing import List

try:
    import streamlit as st

    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


# ✨ FIX #3: Safe chunked rendering for Streamlit
# Prevents st.markdown() from truncating very large reports

# Maximum characters per chunk for safe rendering
# Streamlit's markdown has soft limits around 500KB, but we chunk at 100KB to be safe
CHUNK_SIZE_CHARS = 100_000


def truncate_safe(text: str, max_chars: int = None) -> str:
    """Safely truncate text for token limit handling.

    Args:
        text: Text to truncate
        max_chars: Maximum characters (default: no limit)

    Returns:
        Truncated text with graceful ending
    """
    if max_chars is None or len(text) <= max_chars:
        return text

    # Find the last complete line before cutoff
    truncated = text[:max_chars]

    # Find the last newline to avoid cutting mid-word
    last_newline = truncated.rfind("\n")
    if last_newline > max_chars * 0.8:  # Only use if we're not losing more than 20%
        truncated = truncated[:last_newline]

    # Add trailing note
    truncated += "\n\n_[Output truncated due to size limits]_"

    return truncated


def stitch_sections(sections: List[str]) -> str:
    """Combine multiple report sections into single markdown.

    Used for multi-phase generation where sections are created separately.

    Args:
        sections: List of markdown section strings

    Returns:
        Combined markdown with proper spacing
    """
    if not sections:
        return ""

    # Filter out empty sections
    sections = [s.strip() for s in sections if s and s.strip()]

    if not sections:
        return ""

    # Join sections with markdown divider
    return "\n\n---\n\n".join(sections)


def render_full_report(report_text: str, use_chunks: bool = True) -> None:
    """Safely render a full markdown report in Streamlit.

    Handles very large reports by chunking them into smaller pieces,
    preventing truncation at st.markdown() level.

    Args:
        report_text: Complete markdown report text
        use_chunks: If True, chunk large reports for safer rendering
    """
    if not STREAMLIT_AVAILABLE:
        raise RuntimeError("render_full_report() requires Streamlit to be installed and available")

    if not report_text:
        st.warning("No report content to display.")
        return

    report_text = report_text.strip()

    # For small reports, render directly
    if not use_chunks or len(report_text) <= CHUNK_SIZE_CHARS:
        st.markdown(report_text)
        return

    # For large reports, chunk into sections and render progressively
    # Split by major section headers (## ) to maintain readability
    sections = report_text.split("\n## ")

    # Reconstruct sections with header
    chunked_sections = []
    for i, section in enumerate(sections):
        if i > 0:
            section = f"## {section}"
        chunked_sections.append(section)

    # Group sections into chunks
    chunks = []
    current_chunk = ""

    for section in chunked_sections:
        # If adding this section would exceed chunk size, start new chunk
        if len(current_chunk) + len(section) > CHUNK_SIZE_CHARS and current_chunk:
            chunks.append(current_chunk)
            current_chunk = section
        else:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += section

    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk)

    # Render all chunks
    for chunk in chunks:
        st.markdown(chunk.strip())

    # Show progress indicator for chunked output
    if len(chunks) > 1:
        st.caption(f"📊 Report rendered in {len(chunks)} sections")
