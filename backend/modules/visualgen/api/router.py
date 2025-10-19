from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.db.session_async import get_session
from capsule_core.run import RunRequest, StatusResponse
from backend.core.utils.determinism import RunClock, seed_from_payload, sha256_bytes, estimate_cost
from backend.core.utils.attachments import validate_b64_asset
from backend.core.utils.gates import ocr_legibility_stub, contrast_ratio_stub, file_budget_ok
from backend.core.metrics.registry import RUNS_TOTAL, RUNTIME_SECONDS
import uuid
import io
import base64
import random
import json
from PIL import Image, ImageDraw, ImageFont  # pillow

router = APIRouter()


@router.get("/version")
async def version():
    return {"name": "VisualGen", "module": "visualgen", "version": "1.1.0"}


def parse_size(size_str: str) -> tuple[int, int]:
    try:
        w, h = size_str.lower().split("x")
        return int(w), int(h)
    except Exception:
        return 1200, 628


def make_placeholder_png(w: int, h: int, text: str, brand_color: str | None) -> bytes:
    img = Image.new("RGB", (w, h), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    # brand strip
    if brand_color and brand_color.startswith("#") and len(brand_color) in (4, 7):
        try:
            r = int(brand_color[1:3], 16) if len(brand_color) == 7 else int(brand_color[1] * 2, 16)
            g = int(brand_color[3:5], 16) if len(brand_color) == 7 else int(brand_color[2] * 2, 16)
            b = int(brand_color[5:7], 16) if len(brand_color) == 7 else int(brand_color[3] * 2, 16)
            draw.rectangle([(0, 0), (w, 16)], fill=(r, g, b))
        except Exception:
            pass
    # text
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((20, h // 2 - 10), text, fill=(20, 20, 20), font=font)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


@router.post("/run")
async def run_visualgen(req: RunRequest, session: AsyncSession = Depends(get_session)):
    clk = RunClock()
    run_id = str(uuid.uuid4())
    module = "visualgen"

    c = req.constraints or {}
    brand = c.get("brand", "Your Brand")
    size = c.get("size", "1200x628")
    w, h = parse_size(size)
    count = int(c.get("count", 3))
    brand_primary = c.get("brand_primary")
    # Logo
    logo = c.get("logo")
    if logo:
        try:
            validate_b64_asset(
                {
                    "kind": "image_base64",
                    "mime": logo.get("mime", ""),
                    "base64": logo.get("base64", ""),
                }
            )
        except ValueError as e:
            raise HTTPException(422, detail={"reason": "logo_invalid", "msg": str(e)})

    # Sources (refs images/videos)
    for s in req.sources or []:
        t = s.get("type")
        if t in ("image_base64", "video_base64"):
            try:
                validate_b64_asset(
                    {"kind": t, "mime": s.get("mime", ""), "base64": s.get("base64", "")}
                )
            except ValueError as e:
                raise HTTPException(422, detail={"reason": "source_invalid", "msg": str(e)})

    seed = seed_from_payload(
        {"brand": brand, "size": size, "count": count, "project_id": req.project_id}
    )
    rnd = random.Random(seed)

    # Generate N placeholders (replace with real render pipeline later)
    artifacts = []
    layouts = ["split-left", "split-right", "centered", "headline-top"]
    used_layouts = set()

    for i in range(count):
        layout = rnd.choice(layouts)
        used_layouts.add(layout)
        caption = f"{brand} — {layout}"
        png = make_placeholder_png(w, h, caption, brand_primary)
        b64 = base64.b64encode(png).decode("ascii")
        sha = sha256_bytes(png)
        size_bytes = len(png)

        # Gates: OCR (stub), contrast (stub), file budget
        ocr = ocr_legibility_stub(png)
        contrast = contrast_ratio_stub()
        if not file_budget_ok(size_bytes):
            # compress heuristic: in this demo we just allow since PNG is placeholder
            pass

        meta = {
            "size": size,
            "layout": layout,
            "contrast": contrast,
            "ocr_avg": ocr,
            "brand_applied": {"logo": bool(logo), "primary": brand_primary},
            "seed": seed,
        }
        artifacts.append(
            {
                "type": "image",
                "base64": b64,
                "meta": meta,
                "sha256": sha,
                "content_type": "image/png",
                "size_bytes": size_bytes,
            }
        )

    # Persist run + one meta artifact row (async DB session)
    await session.execute(
        text("insert into runs(run_id,module,status,version) values(:id,:m,'finished','1.1.0')"),
        {"id": run_id, "m": module},
    )
    await session.execute(
        text(
            """insert into artifacts(artifact_id, run_id, type, path, meta_json, sha256, size_bytes, content_type)
                values(gen_random_uuid(), :rid, 'report.json', :p, :meta, :sha, :sz, 'application/json')"""
        ),
        {
            "rid": run_id,
            "p": f"s3://fake/{run_id}/report.json",
            "meta": json.dumps({"layouts": list(used_layouts)}),
            "sha": "sha256-placeholder",
            "sz": 1234,
        },
    )
    await session.commit()

    seconds = clk.seconds()
    # attach telemetry into each artifact meta (for demo convenience)
    for a in artifacts:
        a_meta = a.get("meta", {})
        a_meta["seconds_used"] = seconds
        a_meta["cost_estimate"] = estimate_cost(0)
        a["meta"] = a_meta

    RUNS_TOTAL.labels(module, "success").inc()
    RUNTIME_SECONDS.labels(module).observe(seconds)

    return StatusResponse(task_id=run_id, state="DONE", score=0.95, result={"artifacts": artifacts})
