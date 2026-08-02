from app.config_models.memory_policy_config import (
    MemoryPolicyConfig,
)
from app.policies.base_memory_policy import BaseMemoryPolicy


class SimpleMemoryPolicy(BaseMemoryPolicy):
    def __init__(
        self,
        config: MemoryPolicyConfig,
    ) -> None:
        self._config = config

    def should_remember(
        self,
        key: str,
        value: str,
    ) -> bool:
        if key not in self._config.allowed_keys:
            return False

        return bool(value.strip())
