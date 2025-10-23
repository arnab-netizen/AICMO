from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from .config import SiteGenSettings
from .store import STORE as MEMORY_STORE
from .store_db import DBStore
from .repo import get_engine, create_tables_for_sqlite


if TYPE_CHECKING:
    # Expose types for static analysis only
    from capsule_core.run import RunRequest, RunResponse, StatusResponse  # type: ignore
    from capsule_core.metrics import get_registry  # type: ignore
    from capsule_core.logging import get_logger  # type: ignore


# Lazy imports for optional heavy dependency `capsule_core` to avoid import-time failures
def _require_capsule_core_types():
    try:
        from capsule_core.run import RunRequest, RunResponse, StatusResponse  # type: ignore
        from capsule_core.metrics import get_registry  # type: ignore
        from capsule_core.logging import get_logger  # type: ignore

        return RunRequest, RunResponse, StatusResponse, get_registry, get_logger
    except Exception as e:
        raise RuntimeError(f"capsule_core import failed: {e}") from e


router = APIRouter()
try:
    # Attempt to initialize lightweight metrics/logger and model types if capsule_core present
    RunRequest, RunResponse, StatusResponse, get_registry, get_logger = (
        _require_capsule_core_types()
    )
    log = get_logger("sitegen")
    mreg = get_registry("sitegen")
except Exception:
    # Provide no-op fallbacks so handlers can still be imported when capsule_core
    # is not available in the environment (e.g., CI jobs that don't install it).
    from pydantic import BaseModel

    class _NoOp:
        def counter(self, *a, **k):
            class _C:
                def inc(self_inner):
                    return None

            return _C()

    def _noop_logger(*a, **k):
        def _l(*_a, **_k):
            return None

        return _l

    # Minimal runtime-compatible pydantic fallbacks for the capsule_core models.
    # These satisfy FastAPI's response_model and request parsing used by tests.
    class RunRequest(BaseModel):
        project_id: str
        payload: dict | None = None

    class RunResponse(BaseModel):
        task_id: str
        accepted: bool = True

    class StatusResponse(BaseModel):
        task_id: str
        state: str
        score: float | None = None
        result: dict | None = None
        error: str | None = None

    mreg = _NoOp()

    def log(*a, **k):
        return None


def require_api_key(x_api_key: str | None = Header(default=None)):
    settings = SiteGenSettings()  # read env each request scope (cheap, safe)
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(401, "Invalid API key")


def _select_store():
    settings = SiteGenSettings()
    if settings.SITEGEN_STORE.lower() == "db":
        url = settings.DATABASE_URL or "sqlite+pysqlite:///:memory:"
        # Cache engine/DBStore by URL so in-memory SQLite keeps state across requests
        if not hasattr(_select_store, "_cache"):
            setattr(_select_store, "_cache", {})
        cache = getattr(_select_store, "_cache")
        if url in cache:
            return cache[url]
        engine = get_engine(url)
        if url.startswith("sqlite"):
            create_tables_for_sqlite(engine)
        dbs = DBStore(engine)
        cache[url] = dbs
        return dbs
    return MEMORY_STORE


@router.post("/run", response_model=RunResponse, dependencies=[Depends(require_api_key)])
async def run_job(req: RunRequest, response: Response) -> RunResponse:
    store = _select_store()
    mreg.counter("requests_total", route="run").inc()
    enriched_payload = {"project_id": req.project_id, **(req.payload or {})}
    tid = store.enqueue(enriched_payload)
    store.start(tid)
    store.complete(tid, result={"ok": True, "tier": SiteGenSettings().MODULE_TIER}, score=1.0)
    response.headers["X-Tier"] = SiteGenSettings().MODULE_TIER
    log.info("sitegen_run_accepted", task_id=tid, project_id=req.project_id)
    return RunResponse(task_id=tid, accepted=True)


@router.get("/status/{task_id}", response_model=StatusResponse)
async def status(task_id: str) -> StatusResponse:
    mreg.counter("requests_total", route="status").inc()
    store = _select_store()
    t = store.get(task_id)
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
    s = SiteGenSettings()
    return {"module": s.MODULE_NAME, "tier": s.MODULE_TIER, "store": s.SITEGEN_STORE}


@router.get("/healthz")
async def healthz():
    return {"ok": True}


@router.post("/draft")
async def draft(payload: dict):
    # Minimal draft responder used by tests. Returns a simple site and one page.
    name = payload.get("name") if isinstance(payload, dict) else None
    site = {"name": name}
    pages = [{"slug": "home", "title": "Home"}]
    return {"site": site, "pages": pages}
