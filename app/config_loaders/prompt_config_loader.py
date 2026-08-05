from app.config_loaders.environment_reader import (
    EnvironmentReader,
)
from app.config_models.prompt_config import PromptConfig


class PromptConfigLoader:
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
    ) -> PromptConfig:
        return PromptConfig(
            prompt_name=self._environment_reader.get_str(
                name="PROMPT_NAME",
                default="system_prompt.txt",
            ),
            user_name=self._environment_reader.get_str(
                name="PROMPT_USER_NAME",
                default="Frank",
            ),
            language=self._environment_reader.get_str(
                name="PROMPT_LANGUAGE",
                default="Traditional Chinese",
            ),
        )
