from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.db.session_async import get_session
from capsule_core.run import RunRequest, StatusResponse
from backend.core.utils.determinism import RunClock, seed_from_payload, estimate_cost
from backend.core.utils.gates import readability_score, platform_limit_ok, dedup_jaccard_ok
from backend.core.metrics.registry import RUNS_TOTAL, RUNTIME_SECONDS
from fastapi import Depends
from typing import List, Dict
import uuid
import random
import json

router = APIRouter()


@router.get("/version")
async def version():
    return {"name": "CopyHook", "module": "copyhook", "version": "1.1.0"}


ANGLES = ["benefit", "proof", "urgency", "contrarian"]


def angle_variants(brand: str, topic: str, seed: int) -> List[Dict]:
    rnd = random.Random(seed)
    templates = {
        "benefit": f"{brand}: {topic} without the busywork.",
        "proof": f"{brand}: {topic} trusted by teams like Acme & Nova.",
        "urgency": f"{brand}: {topic} in days, not months.",
        "contrarian": f"{brand}: stop overbuilding—{topic} that actually ships.",
    }
    # shuffle angles but ensure coverage
    order = ANGLES[:]
    rnd.shuffle(order)
    return [{"angle": a, "line": templates[a]} for a in order]


def compliance_fail(line: str, banned: List[str]) -> List[str]:
    lowered = line.lower()
    hits = [b for b in banned if b.lower() in lowered]
    return hits


@router.post("/run", response_model=StatusResponse)
async def run_copyhook(req: RunRequest, session: AsyncSession = Depends(get_session)):
    clk = RunClock()
    run_id = str(uuid.uuid4())
    module = "copyhook"

    brand = (req.constraints or {}).get("brand", "Your Brand")
    topic = req.goal or "landing hero"
    tone = (req.constraints or {}).get("tone", "confident, simple")
    banned_terms = (req.constraints or {}).get("must_avoid", [])

    seed = seed_from_payload(
        {
            "brand": brand,
            "goal": req.goal,
            "tone": tone,
            "must_avoid": banned_terms,
            "project_id": req.project_id,
        }
    )

    # Produce 4 angle-covered variants deterministically
    av = angle_variants(brand, topic, seed)
    variants = [x["line"] for x in av]
    angles = [x["angle"] for x in av]

    # Gates: compliance, readability, dedup, platform limits
    comp_hits = []
    for v in variants:
        hits = compliance_fail(v, banned_terms)
        if hits:
            comp_hits.extend(list(set(hits)))
    if comp_hits:
        RUNS_TOTAL.labels(module, "rejected").inc()
        raise HTTPException(422, detail={"reason": "banned_terms", "hits": comp_hits})

    scores = [readability_score(v) for v in variants]
    if not all(s >= 55 for s in scores):
        RUNS_TOTAL.labels(module, "rejected").inc()
        raise HTTPException(422, detail={"reason": "readability_fail", "scores": scores})

    if not dedup_jaccard_ok(variants):
        RUNS_TOTAL.labels(module, "rejected").inc()
        raise HTTPException(422, detail={"reason": "dedup_fail"})

    platform_ok = [platform_limit_ok(v) for v in variants]
    # ensure at least one is valid for google/linkedin
    if not any(po["google"] and po["linkedin"] for po in platform_ok):
        RUNS_TOTAL.labels(module, "rejected").inc()
        raise HTTPException(
            422, detail={"reason": "platform_limits_fail", "platform_ok": platform_ok}
        )

    # Minimal A/B plan (2x2)
    ab_plan = {
        "matrix": [[variants[0], variants[1]], [variants[2], variants[3]]],
        "angles": [[angles[0], angles[1]], [angles[2], angles[3]]],
        "est_sample": 2500,
    }

    # Persist run + artifact (async DB session)
    meta = {
        "variants": variants,
        "angles": angles,
        "readability": scores,
        "platform_ok": platform_ok,
        "ab_plan": ab_plan,
        "seed": seed,
    }
    await session.execute(
        text("insert into runs(run_id,module,status,version) values(:id,:m,'finished','1.1.0')"),
        {"id": run_id, "m": module},
    )
    payload = json.dumps(meta).encode("utf-8")
    await session.execute(
        text(
            """insert into artifacts(artifact_id, run_id, type, path, meta_json, sha256, size_bytes, content_type)
                values(gen_random_uuid(), :rid, 'copy.json', :path, :meta, :sha, :sz, 'application/json')"""
        ),
        {
            "rid": run_id,
            "path": f"s3://fake/{run_id}/copy.json",
            "meta": json.dumps(meta),
            "sha": "sha256-placeholder",
            "sz": len(payload),
        },
    )
    tokens_used = 1200
    seconds = clk.seconds()
    await session.execute(
        text("update runs set tokens_used=:t, seconds_used=:s, cost_estimate=:c where run_id=:id"),
        {"t": tokens_used, "s": seconds, "c": estimate_cost(tokens_used), "id": run_id},
    )
    await session.commit()

    RUNS_TOTAL.labels(module, "success").inc()
    RUNTIME_SECONDS.labels(module).observe(seconds)

    # augment meta with telemetry
    meta["seconds_used"] = seconds
    meta["cost_estimate"] = estimate_cost(tokens_used)

    return StatusResponse(
        task_id=run_id,
        state="DONE",
        score=0.97,
        result={
            "artifacts": [
                {"type": "copy.json", "url": f"s3://fake/{run_id}/copy.json", "meta": meta}
            ]
        },
    )
