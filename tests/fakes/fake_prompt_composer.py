from collections.abc import Mapping, Sequence

from app.models.message import Message


class FakePromptComposer:
    def __init__(
        self,
        composed_messages: Sequence[Message],
    ) -> None:
        self._composed_messages = list(
            composed_messages,
        )

        self.received_system_message: Message | None = None
        self.received_history_messages: list[Message] | None = None
        self.received_facts: dict[str, str] | None = None
        self.received_user_message: Message | None = None

    def compose(
        self,
        *,
        system_message: Message,
        history_messages: Sequence[Message],
        facts: Mapping[str, str],
        user_message: Message,
    ) -> list[Message]:
        self.received_system_message = system_message
        self.received_history_messages = list(
            history_messages,
        )
        self.received_facts = dict(facts)
        self.received_user_message = user_message

        return list(
            self._composed_messages,
        )
