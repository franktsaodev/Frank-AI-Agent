from typing import ClassVar

from app.config_loaders.environment_reader import (
    EnvironmentReader,
)
from app.config_models.memory_policy_config import (
    MemoryPolicyConfig,
)


class MemoryPolicyConfigLoader:
    DEFAULT_ALLOWED_KEYS: ClassVar[tuple[str, ...]] = (
        "user_name",
        "favorite_music",
        "occupation",
    )

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
    ) -> MemoryPolicyConfig:
        raw_value = self._environment_reader.get_str(
            name="MEMORY_ALLOWED_KEYS",
            default=",".join(
                self.DEFAULT_ALLOWED_KEYS,
            ),
        )

        allowed_keys = frozenset(
            item.strip() for item in raw_value.split(",") if item.strip()
        )

        return MemoryPolicyConfig(
            allowed_keys=allowed_keys,
        )
