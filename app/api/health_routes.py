from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.models import HealthResponse
from app.api.runtime import RuntimeInfo
from app.api.runtime_provider import (
    get_runtime_info,
)

router = APIRouter()

RuntimeInfoDependency = Annotated[
    RuntimeInfo,
    Depends(get_runtime_info),
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
