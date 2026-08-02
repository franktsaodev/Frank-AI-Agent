from typing import ClassVar

from app.policies.base_memory_policy import BaseMemoryPolicy


class SimpleMemoryPolicy(BaseMemoryPolicy):
    ALLOWED_KEYS: ClassVar[frozenset[str]] = frozenset(
        {
            "user_name",
            "favorite_music",
            "occupation",
        }
    )

    def should_remember(
        self,
        key: str,
        value: str,
    ) -> bool:
        if key not in self.ALLOWED_KEYS:
            return False

        return bool(value.strip())
