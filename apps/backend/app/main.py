from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.project import router as projects_router
from app.routes.chat import router as chat_router
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
    app.include_router(auth_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    return app


app = create_app()