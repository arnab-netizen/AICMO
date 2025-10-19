from PIL import Image, ImageDraw, ImageFont
import json
import io
import zipfile
import os
from typing import Dict


def make_gate_summary_png(scores: Dict, width=720, height=320) -> bytes:
    img = Image.new("RGB", (width, height), color=(250, 250, 250))
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    y = 20
    dr.text((20, y), "Gate Summary", fill=(20, 20, 20), font=font)
    y += 30
    for k, v in scores.items():
        dr.text((20, y), f"{k}: {v}", fill=(30, 30, 30), font=font)
        y += 20
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def write_report_bundle(
    out_zip_path: str,
    client: str,
    run_meta: Dict,
    copy_artifact: Dict | None,
    img_artifacts: list[Dict],
):
    os.makedirs(os.path.dirname(out_zip_path), exist_ok=True)
    with zipfile.ZipFile(out_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        # /meta/run.json
        z.writestr("meta/run.json", json.dumps(run_meta, indent=2))
        # /copy/copy.json
        if copy_artifact:
            z.writestr("copy/copy.json", json.dumps(copy_artifact["meta"], indent=2))
            top5 = "\n".join(copy_artifact["meta"].get("variants", [])[:5])
            z.writestr("copy/copy_top5.txt", top5)
        # /creatives/ images
        for idx, a in enumerate(img_artifacts, 1):
            if a.get("base64"):
                import base64

                raw = base64.b64decode(a["base64"])
                z.writestr(f"creatives/creative_{idx}.png", raw)
        # /reports/gate_report.json + gate_summary.png
        scores = {
            "seconds_used": run_meta.get("seconds_used", 0),
            "score": run_meta.get("score", 1.0),
        }
        z.writestr("reports/gate_report.json", json.dumps(scores, indent=2))
        z.writestr("reports/gate_summary.png", make_gate_summary_png(scores))
        # README
        z.writestr(
            "meta/README.txt",
            f"{client} — AI-CMO Sprint Bundle\nUse /copy/* for text and /creatives/* for images.",
        )
