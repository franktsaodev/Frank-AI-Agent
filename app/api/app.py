import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.routing import Route

from app.api.application_lifespan import (
    application_lifespan,
)
from app.api.exception_handlers import (
    register_exception_handlers,
)
from app.api.health_routes import router as health_router
from app.api.http_metrics import HttpMetrics
from app.api.lifespan_types import Lifespan
from app.api.runtime_provider import get_runtime_info
from app.api.v1.session_routes import (
    router as session_router,
)
from app.config_loaders.cors_config_loader import CorsConfigLoader
from app.config_loaders.environment_reader import EnvironmentReader
from app.config_loaders.logging_config_loader import LoggingConfigLoader
from app.core.logging_config import configure_logging

logger = logging.getLogger(__name__)


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

    http_metrics = HttpMetrics()

    @app.get("/metrics", include_in_schema=False)
    async def get_metrics() -> Response:
        return Response(
            content=http_metrics.render(),
            headers={
                "Content-Type": CONTENT_TYPE_LATEST,
            },
        )

    @app.middleware("http")
    async def add_request_id(
        request: Request,
        call_next,
    ) -> Response:
        started_at = perf_counter()
        request_id = str(uuid4())
        request.state.request_id = request_id

        try:
            response: Response = await call_next(request)
        except Exception:  # noqa: BLE001
            # This HTTP boundary converts unexpected errors into a sanitized 500.
            logger.error(
                "Unhandled HTTP request request_id=%s method=%s status=500",
                request_id,
                request.method,
            )

            response = PlainTextResponse(
                "Internal Server Error",
                status_code=500,
            )

        response.headers["X-Request-ID"] = request_id

        duration_seconds = perf_counter() - started_at
        duration_ms = duration_seconds * 1000

        matched_route = request.scope.get("route")
        route_label = (
            matched_route.path if isinstance(matched_route, Route) else "unmatched"
        )

        if route_label != "/metrics":
            http_metrics.observe_response(
                method=request.method,
                route=route_label,
                status=response.status_code,
                duration_seconds=duration_seconds,
            )

        logger.info(
            "HTTP response started request_id=%s method=%s status=%s duration_ms=%.3f",
            request_id,
            request.method,
            response.status_code,
            duration_ms,
        )

        return response

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
        expose_headers=[
            "X-Request-ID",
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
