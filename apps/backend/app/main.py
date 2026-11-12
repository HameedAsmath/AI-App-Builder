from fastapi import FastAPI

from app.routes.health import router as health_router
from app.lib.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.include_router(health_router, prefix="/api")
    return app


app = create_app()