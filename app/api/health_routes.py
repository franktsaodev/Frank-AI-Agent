import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis import Redis
from redis.exceptions import RedisError

from app.api.models import (
    ErrorResponse,
    HealthResponse,
    ReadinessResponse,
)
from app.api.redis_dependencies import get_redis_client
from app.api.runtime import RuntimeInfo
from app.api.runtime_provider import (
    get_runtime_info,
)

logger = logging.getLogger(__name__)

router = APIRouter()

RuntimeInfoDependency = Annotated[
    RuntimeInfo,
    Depends(get_runtime_info),
]

RedisClientDependency = Annotated[
    Redis,
    Depends(get_redis_client),
]


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=[
        "Health",
    ],
)
def health(
    runtime: RuntimeInfoDependency,
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=runtime.service_name,
        version=runtime.version,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "A required service dependency is unavailable.",
        },
    },
    tags=[
        "Health",
    ],
)
def readiness(
    redis_client: RedisClientDependency,
) -> ReadinessResponse | JSONResponse:
    try:
        if not redis_client.ping():
            raise RedisError("Redis PING returned false.")
    except RedisError as error:
        logger.warning(
            "Redis readiness check failed: %s",
            error,
        )

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "service_unavailable",
                "message": "The service is not ready.",
            },
        )

    return ReadinessResponse(
        status="ready",
        redis="ok",
    )
