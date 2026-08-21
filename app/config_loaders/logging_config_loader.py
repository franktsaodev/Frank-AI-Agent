from app.config_loaders.environment_reader import EnvironmentReader
from app.config_models.logging_config import LoggingConfig


class LoggingConfigLoader:
    def __init__(
        self,
        environment_reader: EnvironmentReader,
    ) -> None:
        self._environment_reader = environment_reader

    def load(self) -> LoggingConfig:
        return LoggingConfig(
            level=self._environment_reader.get_str(
                name="LOG_LEVEL",
                default="INFO",
            )
        )
