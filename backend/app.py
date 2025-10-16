from fastapi import FastAPI
from backend.routers import sites as sites_router

from backend.startup import init_views

def create_app() -> FastAPI:
	app = FastAPI(title="AI-CMO API")
	app.include_router(sites_router.router)
	# initialize views (idempotent)
	init_views()
	return app


app = create_app()

# ...existing includes / middleware / health endpoints...
