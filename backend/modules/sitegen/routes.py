from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException, Response
from capsule_core.run import RunRequest, RunResponse, StatusResponse
from capsule_core.metrics import get_registry
from capsule_core.logging import get_logger
from .config import SiteGenSettings
from .store import STORE

router = APIRouter()
log = get_logger("sitegen")
mreg = get_registry("sitegen")
settings = SiteGenSettings()


def require_api_key(x_api_key: str | None = Header(default=None)):
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(401, "Invalid API key")


@router.post("/run", response_model=RunResponse, dependencies=[Depends(require_api_key)])
async def run_job(req: RunRequest, response: Response) -> RunResponse:
    mreg.counter("requests_total", route="run").inc()
    tid = STORE.enqueue(req.payload)
    # simulate immediate start + a trivial “result”
    STORE.start(tid)
    STORE.complete(tid, result={"ok": True, "tier": settings.MODULE_TIER}, score=1.0)
    response.headers["X-Tier"] = settings.MODULE_TIER
    log.info("sitegen_run_accepted", task_id=tid, project_id=req.project_id)
    return RunResponse(task_id=tid, accepted=True)


@router.get("/status/{task_id}", response_model=StatusResponse)
async def status(task_id: str) -> StatusResponse:
    mreg.counter("requests_total", route="status").inc()
    t = STORE.get(task_id)
    return StatusResponse(
        task_id=t.task_id, state=t.state, score=t.score, result=t.result, error=t.error
    )


@router.post("/feedback")
async def feedback(payload: dict):
    mreg.counter("feedback_total").inc()
    log.info("sitegen_feedback", payload=payload)
    return {"ok": True}


@router.get("/metrics")
async def metrics():
    # For now, return a small JSON metrics view (Prometheus integration can follow).
    # Expose total request/feedback counters presence as a quick liveness check.
    return {"module": settings.MODULE_NAME, "tier": settings.MODULE_TIER}


@router.get("/healthz")
async def healthz():
    return {"ok": True}
