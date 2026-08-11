from collections.abc import Mapping, Sequence
from typing import Protocol

from app.models.message import Message
from app.retrieval.retrieved_context import RetrievedContext


class PromptComposerProtocol(Protocol):
    def compose(
        self,
        *,
        system_message: Message,
        history_messages: Sequence[Message],
        facts: Mapping[str, str],
        user_message: Message,
        retrieved_contexts: Sequence[RetrievedContext] = (),
    ) -> list[Message]: ...
