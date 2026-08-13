from app.config_loaders.environment_reader import (
    EnvironmentReader,
)
from app.config_models.api_runtime_config import (
    ApiRuntimeConfig,
)


class ApiRuntimeConfigLoader:
    def __init__(
        self,
        environment_reader: EnvironmentReader | None = None,
    ) -> None:
        self._environment_reader = (
            environment_reader
            if environment_reader is not None
            else EnvironmentReader()
        )

    def load(
        self,
    ) -> ApiRuntimeConfig:
        return ApiRuntimeConfig(
            service_name=self._environment_reader.get_str(
                name="APP_SERVICE_NAME",
                default="Frank AI Agent",
            ),
            version=self._environment_reader.get_str(
                name="APP_VERSION",
                default="1.1.0",
            ),
        )
