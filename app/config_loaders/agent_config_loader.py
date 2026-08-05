from app.config_loaders.environment_reader import (
    EnvironmentReader,
)
from app.config_models.agent_config import AgentConfig


class AgentConfigLoader:
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
    ) -> AgentConfig:
        return AgentConfig(
            max_iterations=self._environment_reader.get_int(
                name="AGENT_MAX_ITERATIONS",
                default=10,
            ),
        )
