from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.models.message import Message


@dataclass(frozen=True)
class ChatAgentState:
    messages: tuple[Message, ...]
    facts: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "messages",
            tuple(self.messages),
        )
        object.__setattr__(
            self,
            "facts",
            MappingProxyType(
                dict(self.facts),
            ),
        )
