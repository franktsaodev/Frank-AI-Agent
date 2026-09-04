from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.application_lifespan import (
    application_lifespan,
)
from app.api.exception_handlers import (
    register_exception_handlers,
)
from app.api.health_routes import router as health_router
from app.api.lifespan_types import Lifespan
from app.api.runtime_provider import get_runtime_info
from app.api.v1.session_routes import (
    router as session_router,
)
from app.config_loaders.cors_config_loader import CorsConfigLoader
from app.config_loaders.environment_reader import EnvironmentReader
from app.config_loaders.logging_config_loader import LoggingConfigLoader
from app.core.logging_config import configure_logging


def create_app(
    *,
    lifespan: Lifespan | None = None,
) -> FastAPI:
    environment_reader = EnvironmentReader()

    logging_config = LoggingConfigLoader(
        environment_reader=environment_reader,
    ).load()

    configure_logging(
        config=logging_config,
    )

    cors_config = CorsConfigLoader(
        environment_reader=environment_reader,
    ).load()

    runtime = get_runtime_info()

    actual_lifespan = lifespan if lifespan is not None else application_lifespan

    app = FastAPI(
        title=f"{runtime.service_name} API",
        description=(
            "A modular AI Agent service with memory, "
            "tool calling, tracing, plugin architecture, "
            "and configurable runtime components."
        ),
        version=runtime.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=actual_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_config.allowed_origins),
        allow_credentials=False,
        allow_methods=[
            "GET",
            "POST",
            "DELETE",
        ],
        allow_headers=[
            "Content-Type",
        ],
    )

    register_exception_handlers(
        app,
    )

    app.include_router(
        health_router,
    )

    app.include_router(
        session_router,
        prefix="/api/v1",
    )

    return app
