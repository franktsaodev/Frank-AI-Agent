from pathlib import Path

from app.config_loaders.environment_reader import (
    EnvironmentReader,
)
from app.config_models.tracing_config import (
    TracingConfig,
)


class TracingConfigLoader:
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
    ) -> TracingConfig:
        json_file_path = self._environment_reader.get_str(
            name="TRACE_JSON_FILE_PATH",
            default="logs/traces.jsonl",
        )

        return TracingConfig(
            enable_logging=self._environment_reader.get_bool(
                name="TRACE_LOGGING_ENABLED",
                default=True,
            ),
            json_file_path=Path(
                json_file_path,
            ),
        )
