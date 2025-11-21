"""Visual rendering engine for marketing images."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


@dataclass
class RenderInputs:
    """Input parameters for visual rendering."""

    width: int = 1200
    height: int = 628
    headline: str = ""
    subheadline: str = ""
    brand_color: str = "#0A84FF"
    text_color: str = "#ffffff"
    logo_b64: Optional[str] = None
    layout: str = "center"  # center | split-left | split-right


@dataclass
class RenderOutput:
    """Output from visual rendering."""

    pil_image: Image.Image
    bytes_data: bytes
    base64_data: str


class VisualRenderer:
    """
    Deterministic simple template renderer for marketing images.
    """

    def __init__(self, default_font: Optional[str] = None):
        self.default_font = default_font or "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    def _load_logo(self, logo_b64: Optional[str]) -> Optional[Image.Image]:
        """Load and resize logo from base64 string."""
        if not logo_b64:
            return None
        try:
            data = base64.b64decode(logo_b64)
            logo = Image.open(BytesIO(data)).convert("RGBA")
            return logo.resize((180, 180))
        except Exception:
            return None

    def _draw_center(
        self,
        img: Image.Image,
        d: ImageDraw.Draw,
        inputs: RenderInputs,
        font: ImageFont.FreeTypeFont,
    ):
        """Draw headline and subheadline in center layout."""
        w, h = img.size

        # Get text size for headline
        bbox = d.textbbox((0, 0), inputs.headline, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Draw headline in center
        d.text(
            ((w - text_w) / 2, (h - text_h) / 2 - 40),
            inputs.headline,
            font=font,
            fill=inputs.text_color,
        )

        # Subheadline below
        if inputs.subheadline:
            sub_font = ImageFont.truetype(self.default_font, 36)
            sub_bbox = d.textbbox((0, 0), inputs.subheadline, font=sub_font)
            sub_w = sub_bbox[2] - sub_bbox[0]
            d.text(
                ((w - sub_w) / 2, (h - text_h) / 2 + 40),
                inputs.subheadline,
                font=sub_font,
                fill=inputs.text_color,
            )

    def _draw_split_left(
        self,
        img: Image.Image,
        d: ImageDraw.Draw,
        inputs: RenderInputs,
        font: ImageFont.FreeTypeFont,
    ):
        """Draw headline and subheadline on left side."""
        w, h = img.size
        # Draw headline on left side
        d.text((80, h / 2 - 40), inputs.headline, font=font, fill=inputs.text_color)

        if inputs.subheadline:
            sub_font = ImageFont.truetype(self.default_font, 36)
            d.text((80, h / 2 + 30), inputs.subheadline, font=sub_font, fill=inputs.text_color)

    def _draw_split_right(
        self,
        img: Image.Image,
        d: ImageDraw.Draw,
        inputs: RenderInputs,
        font: ImageFont.FreeTypeFont,
    ):
        """Draw headline and subheadline on right side."""
        w, h = img.size
        # Draw headline on right side
        d.text((w / 2 + 40, h / 2 - 40), inputs.headline, font=font, fill=inputs.text_color)

        if inputs.subheadline:
            sub_font = ImageFont.truetype(self.default_font, 36)
            d.text(
                (w / 2 + 40, h / 2 + 30), inputs.subheadline, font=sub_font, fill=inputs.text_color
            )

    def render(self, inputs: RenderInputs) -> RenderOutput:
        """
        Render a marketing image based on input parameters.

        Returns RenderOutput with PIL image, bytes, and base64 data.
        """
        img = Image.new("RGB", (inputs.width, inputs.height), color=inputs.brand_color)
        d = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(self.default_font, 64)
        except Exception:
            # Fallback to default font if custom font not available
            font = ImageFont.load_default()

        # Layout dispatch
        if inputs.layout == "center":
            self._draw_center(img, d, inputs, font)
        elif inputs.layout == "split-left":
            self._draw_split_left(img, d, inputs, font)
        elif inputs.layout == "split-right":
            self._draw_split_right(img, d, inputs, font)

        # Logo in top-left corner
        logo = self._load_logo(inputs.logo_b64)
        if logo:
            img.paste(logo, (40, 40), logo)

        # Convert to bytes and base64
        buf = BytesIO()
        img.save(buf, format="PNG")
        bytes_data = buf.getvalue()
        base64_data = base64.b64encode(bytes_data).decode("utf-8")

        return RenderOutput(
            pil_image=img,
            bytes_data=bytes_data,
            base64_data=base64_data,
        )
