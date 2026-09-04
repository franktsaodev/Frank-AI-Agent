from app.config_loaders.environment_reader import EnvironmentReader
from app.config_models.cors_config import CorsConfig


class CorsConfigLoader:
    def __init__(
        self,
        environment_reader: EnvironmentReader,
    ) -> None:
        self._environment_reader = environment_reader

    def load(self) -> CorsConfig:
        allowed_origins_value = self._environment_reader.get_str(
            name="CORS_ALLOWED_ORIGINS",
            default="http://localhost:5173",
        )

        allowed_origins = tuple(
            origin.strip()
            for origin in allowed_origins_value.split(",")
            if origin.strip()
        )

        return CorsConfig(
            allowed_origins=allowed_origins,
        )
