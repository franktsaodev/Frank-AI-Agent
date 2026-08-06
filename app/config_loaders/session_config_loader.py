from app.config_loaders.environment_reader import (
    EnvironmentReader,
)
from app.config_models.session_config import SessionConfig


class SessionConfigLoader:
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
    ) -> SessionConfig:
        return SessionConfig(
            ttl_seconds=self._environment_reader.get_int(
                name="SESSION_TTL_SECONDS",
                default=3600,
            ),
            cleanup_interval_seconds=self._environment_reader.get_int(
                name="SESSION_CLEANUP_INTERVAL_SECONDS",
                default=300,
            ),
        )
