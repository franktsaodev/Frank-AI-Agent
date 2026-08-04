from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from app.types.json_types import JsonValue


@dataclass(frozen=True)
class AgentRunContext:
    metadata: Mapping[str, JsonValue] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata),
            ),
        )
