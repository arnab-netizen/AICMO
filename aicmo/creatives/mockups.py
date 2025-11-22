"""Social mockup generation for marketing deliverables."""

from __future__ import annotations

import io
import zipfile
from typing import Any

from PIL import Image, ImageDraw


def build_mockup_zip_from_report(
    report: Any,
    brand_name: str = "Brand",
    max_posts: int = 10,
    default_kind: str = "feed",
) -> bytes:
    """Generate social mockups and return as ZIP."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(max_posts):
            img = Image.new("RGB", (1080, 1350), color=(240, 240, 240))
            draw = ImageDraw.Draw(img)
            draw.text((540, 675), f"{brand_name} Post {i+1}", fill=(0, 0, 0), anchor="mm")

            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            zf.writestr(f"post_{i+1:02d}.png", img_bytes.getvalue())

    zip_buffer.seek(0)
    return zip_buffer.getvalue()
