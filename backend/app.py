import time
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from backend.core.config import settings
from backend.db import ping_db
from backend.routers.health import router as health_router
from backend.routers.test import router as test_router
from backend.modules.sitegen.routes import router as sitegen_router
from backend.routers.sites import router as sites_router

# NEW imports for the modules we added
from backend.modules.copyhook.api.router import router as copyhook_router
from backend.modules.visualgen.api.router import router as visualgen_router
from backend.modules.taste.router import router as taste_router

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry for a bounded time so dev server doesn't crash if DB is late
    deadline = time.time() + settings.DB_STARTUP_RETRY_SECS
    logged_once = False
    while time.time() < deadline:
        if ping_db():
            log.info("Database reachable.")
            break
        if not logged_once:
            log.warning("Database not reachable yet; will retry until ready...")
            logged_once = True
        await asyncio.sleep(1.0)
    else:
        # Out of budget: continue to serve liveness, but readiness will be false
        log.error("Database not reachable within startup budget; continuing without DB.")
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(test_router, tags=["test"])
app.include_router(sitegen_router, prefix="/sitegen", tags=["sitegen"])

# Sites router (provides /sites/{slug}/spec used in tests)
app.include_router(sites_router, tags=["sites"])

# Mount the new module routers
app.include_router(copyhook_router, prefix="/api/copyhook", tags=["copyhook"])
app.include_router(visualgen_router, prefix="/api/visualgen", tags=["visualgen"])
app.include_router(taste_router)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.exception_handler(RuntimeError)
def runtime_error_handler(request: Request, exc: RuntimeError):
    # Return a standardized JSON payload for runtime errors (e.g., dependency
    # construction failures) so health checks can surface a clear message.
    return JSONResponse(status_code=500, content={"status": "error", "detail": str(exc)[:200]})


@app.get("/health")
def health():
    return {"ok": True}
