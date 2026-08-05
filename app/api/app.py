from fastapi import FastAPI

from app.api.exception_handlers import (
    register_exception_handlers,
)
from app.api.routes import router as health_router
from app.api.v1.routes import router as v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Frank AI Agent API",
        description=(
            "A modular AI Agent service with memory, "
            "tool calling, tracing, plugin architecture, "
            "and configurable runtime components."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    register_exception_handlers(
        app,
    )

    app.include_router(
        health_router,
    )

    app.include_router(
        v1_router,
        prefix="/api/v1",
    )

    return app
