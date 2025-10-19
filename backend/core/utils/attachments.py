import base64
from typing import TypedDict, Literal

AllowedImg = {"image/png", "image/jpeg", "image/webp"}
AllowedVid = {"video/mp4", "video/webm", "video/ogg"}
MAX_MB = 12


class B64Asset(TypedDict, total=False):
    kind: Literal["image_base64", "video_base64"]
    mime: str
    base64: str
    role: str  # "logo" | "reference"


def validate_b64_asset(asset: B64Asset) -> None:
    mime = asset.get("mime", "")
    b64 = asset.get("base64", "")
    if not mime or not b64:
        raise ValueError("Attachment missing mime or base64")
    if mime not in AllowedImg and mime not in AllowedVid:
        raise ValueError(f"Unsupported mime: {mime}")
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception:
        raise ValueError("Invalid base64 data")
    mb = len(raw) / (1024 * 1024)
    if mb > MAX_MB:
        raise ValueError(f"Attachment too large: {mb:.1f}MB > {MAX_MB}MB")


def classify_attachment(asset: B64Asset) -> str:
    """Return 'image' or 'video'."""
    mime = asset["mime"]
    if mime in AllowedImg:
        return "image"
    if mime in AllowedVid:
        return "video"
    return "unknown"
