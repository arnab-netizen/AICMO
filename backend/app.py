import time
import logging
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from backend.core.config import settings
from backend.db import ping_db
from backend.routers.health import router as health_router
from backend.routers.test import router as test_router
from backend.modules.sitegen.routes import router as sitegen_router

# NEW imports for the modules we added
from backend.modules.copyhook.api.router import router as copyhook_router
from backend.modules.visualgen.api.router import router as visualgen_router
from backend.modules.taste.router import router as taste_router

log = logging.getLogger("uvicorn.error")

app = FastAPI(title=settings.APP_NAME)

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(test_router, tags=["test"])
app.include_router(sitegen_router, prefix="/sitegen", tags=["sitegen"])

# Mount the new module routers
app.include_router(copyhook_router, prefix="/api/copyhook", tags=["copyhook"])
app.include_router(visualgen_router, prefix="/api/visualgen", tags=["visualgen"])
app.include_router(taste_router)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.on_event("startup")
def startup():
    # Retry for a bounded time so dev server doesn't crash if DB is late
    deadline = time.time() + settings.DB_STARTUP_RETRY_SECS
    logged_once = False
    while time.time() < deadline:
        if ping_db():
            log.info("Database reachable.")
            return
        if not logged_once:
            log.warning("Database not reachable yet; will retry until ready...")
            logged_once = True
        time.sleep(1.0)
    # Out of budget: continue to serve liveness, but readiness will be false
    log.error("Database not reachable within startup budget; continuing without DB.")


@app.get("/health")
def health():
    return {"ok": True}
