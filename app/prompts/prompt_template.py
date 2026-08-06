from pathlib import Path

from app.config_models.prompt_config import PromptConfig
from app.prompts.base_prompt_template import BasePromptTemplate


class PromptTemplate(BasePromptTemplate):
    def __init__(
        self,
        config: PromptConfig,
    ) -> None:
        self.config = config

    def _get_prompt_path(self) -> Path:
        return Path(__file__).parent / self.config.prompt_name

    def _load_template(self) -> str:
        prompt_path = self._get_prompt_path()

        return prompt_path.read_text(
            encoding="utf-8",
        )

    def render(self) -> str:
        template = self._load_template()

        return template.format(
            language=self.config.language,
        )
