from collections.abc import Mapping, Sequence
from typing import Protocol

from app.models.message import Message


class PromptComposerProtocol(Protocol):
    def compose(
        self,
        *,
        system_message: Message,
        history_messages: Sequence[Message],
        facts: Mapping[str, str],
        user_message: Message,
    ) -> list[Message]:
        ...