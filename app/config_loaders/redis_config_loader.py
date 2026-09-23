from app.config_loaders.environment_reader import (
    EnvironmentReader,
)
from app.config_models.redis_config import RedisConfig


class RedisConfigLoader:
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
    ) -> RedisConfig:
        return RedisConfig(
            url=self._environment_reader.get_str(
                name="REDIS_URL",
                default="redis://localhost:6379/0",
            ),
            session_key_prefix=self._environment_reader.get_str(
                name="REDIS_SESSION_KEY_PREFIX",
                default="frank-ai-agent:sessions",
            ),
        )
