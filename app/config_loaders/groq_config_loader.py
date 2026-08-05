from app.config_loaders.environment_reader import EnvironmentReader
from app.config_models.groq_config import GroqConfig


class GroqConfigLoader:
    def load(
        self,
    ) -> GroqConfig:
        reader = EnvironmentReader()

        return GroqConfig(
            api_key=reader.get_required(
                "GROQ_API_KEY",
            ),
            model=reader.get_required(
                "GROQ_MODEL",
            ),
        )
