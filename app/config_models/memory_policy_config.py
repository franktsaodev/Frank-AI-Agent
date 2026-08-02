from dataclasses import dataclass, field


@dataclass(frozen=True)
class MemoryPolicyConfig:
    allowed_keys: frozenset[str] = field(
        default_factory=frozenset,
    )
