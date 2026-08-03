from collections.abc import Mapping, Sequence

from app.models.message import Message


class PromptComposer:
    def _format_facts(
        self,
        facts: Mapping[str, str],
    ) -> str | None:
        if not facts:
            return None

        formatted_facts = "\n".join(f"- {key}: {value}" for key, value in facts.items())

        return f"User facts:\n{formatted_facts}"

    def compose(
        self,
        *,
        system_message: Message,
        history_messages: Sequence[Message],
        facts: Mapping[str, str],
        user_message: Message,
    ) -> list[Message]:
        composed_system_message = system_message

        facts_content = self._format_facts(
            facts,
        )

        if facts_content is not None:
            system_content = system_message.content

            if system_content is None:
                raise ValueError("System message content cannot be None.")

            composed_system_message = Message(
                role=system_message.role,
                content=(f"{system_content}\n\n{facts_content}"),
            )

        return [
            composed_system_message,
            *history_messages,
            user_message,
        ]
