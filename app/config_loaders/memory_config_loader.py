from app.config_loaders.environment_reader import (
    EnvironmentReader,
)
from app.config_models.memory_config import MemoryConfig


class MemoryConfigLoader:
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
    ) -> MemoryConfig:
        return MemoryConfig(
            max_history_rounds=self._environment_reader.get_int(
                name="MEMORY_MAX_HISTORY_ROUNDS",
                default=2,
            ),
        )
