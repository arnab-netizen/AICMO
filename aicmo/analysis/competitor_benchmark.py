"""Competitor visual analysis and benchmarking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from PIL import Image
import io


@dataclass
class CompetitorCreativeStats:
    """Stats for a competitor's creative assets."""

    competitor: str
    num_assets: int
    dominant_colors_hex: List[str]
    avg_brightness: float
    style_note: str


def analyze_competitor_images(
    files_by_competitor: dict[str, list[bytes]],
) -> List[CompetitorCreativeStats]:
    """Analyze uploaded competitor images."""
    stats = []

    for comp_name, file_bytes_list in files_by_competitor.items():
        if not file_bytes_list:
            continue

        colors = set()
        brightness_vals = []

        for file_bytes in file_bytes_list:
            try:
                img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                img.thumbnail((100, 100))
                pixels = list(img.getdata())

                for r, g, b in pixels:
                    b_val = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                    brightness_vals.append(b_val)
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    colors.add(hex_color)
            except Exception:
                pass

        dominant = list(colors)[:5]
        avg_bright = sum(brightness_vals) / len(brightness_vals) if brightness_vals else 0.5

        style_note = "Modern, minimal aesthetic" if avg_bright > 0.6 else "Dark, bold aesthetic"

        stats.append(
            CompetitorCreativeStats(
                competitor=comp_name,
                num_assets=len(file_bytes_list),
                dominant_colors_hex=dominant,
                avg_brightness=avg_bright,
                style_note=style_note,
            )
        )

    return stats
