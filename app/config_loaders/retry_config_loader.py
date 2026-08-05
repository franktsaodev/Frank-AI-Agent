from app.config_loaders.environment_reader import EnvironmentReader
from app.config_models.retry_config import RetryConfig


class RetryConfigLoader:
    def load(
        self,
    ) -> RetryConfig:
        reader = EnvironmentReader()

        return RetryConfig(
            max_attempts=reader.get_int(
                name="GROQ_RETRY_MAX_ATTEMPTS",
                default=3,
            ),
            initial_delay_seconds=reader.get_float(
                name="GROQ_RETRY_INITIAL_DELAY_SECONDS",
                default=1.0,
            ),
            backoff_multiplier=reader.get_float(
                name="GROQ_RETRY_BACKOFF_MULTIPLIER",
                default=2.0,
            ),
        )
