from functools import lru_cache

from app.api.runtime import RuntimeInfo
from app.config_loaders.api_runtime_config_loader import (
    ApiRuntimeConfigLoader,
)


@lru_cache(maxsize=1)
def get_runtime_info() -> RuntimeInfo:
    config = ApiRuntimeConfigLoader().load()

    return RuntimeInfo(
        service_name=config.service_name,
        version=config.version,
    )
