from collections.abc import Mapping, Sequence

from app.models.message import Message
from app.retrieval.retrieved_context import RetrievedContext


class PromptComposer:
    def compose(
        self,
        *,
        system_message: Message,
        history_messages: Sequence[Message],
        facts: Mapping[str, str],
        user_message: Message,
        retrieved_contexts: Sequence[RetrievedContext] = (),
    ) -> list[Message]:
        system_content = system_message.content

        if system_content is None:
            raise ValueError("System message content cannot be None.")

        context_parts = [system_content]

        facts_content = self._format_facts(facts)

        if facts_content is not None:
            context_parts.append(facts_content)

        retrieved_content = self._format_retrieved_contexts(retrieved_contexts)

        if retrieved_content is not None:
            context_parts.append(retrieved_content)

        composed_system_message = Message(
            role=system_message.role,
            content="\n\n".join(context_parts),
        )

        return [
            composed_system_message,
            *history_messages,
            user_message,
        ]

    def _format_facts(
        self,
        facts: Mapping[str, str],
    ) -> str | None:
        if not facts:
            return None

        formatted_facts = "\n".join(f"- {key}: {value}" for key, value in facts.items())

        return f"User facts:\n{formatted_facts}"

    def _format_retrieved_contexts(
        self,
        contexts: Sequence[RetrievedContext],
    ) -> str | None:
        if not contexts:
            return None

        parts: list[str] = ["Retrieved knowledge:"]

        for context in contexts:
            if context.source is not None:
                parts.append(f"Source: {context.source}")

            parts.append(context.content)

        return "\n".join(parts)
