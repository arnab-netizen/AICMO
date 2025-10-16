import time
import logging
from fastapi import FastAPI
from backend.core.config import settings
from backend.db import ping_db
from backend.routers.health import router as health_router
from backend.routers.test import router as test_router
from backend.routers.sites import router as sites_router
from backend.routers.sitegen import router as sitegen_router
from backend.routers.sitegen_draft import router as sitegen_draft_router
from backend.routers.deployments import router as deployments_router
from backend.routers.workflows import router as workflows_router

log = logging.getLogger("uvicorn.error")

app = FastAPI(title=settings.APP_NAME)

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(test_router, tags=["test"])
app.include_router(sites_router)
app.include_router(sitegen_router)
app.include_router(sitegen_draft_router)
app.include_router(deployments_router)
app.include_router(workflows_router)

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
