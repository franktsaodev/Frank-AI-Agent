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

        if any(context.source is not None for context in contexts):
            parts.append(
                "When using the retrieved knowledge, cite it with the "
                "corresponding [source:N] token. Use only the citation tokens "
                "shown below. Do not invent citation tokens, source names, "
                "or page numbers."
            )

        citation_number = 1

        for context in contexts:
            source_label = self._format_source(
                context,
                citation_number=citation_number,
            )

            if source_label is not None:
                parts.append(source_label)
                citation_number += 1

            parts.append(context.content)

        return "\n".join(parts)

    def _format_source(
        self,
        context: RetrievedContext,
        *,
        citation_number: int,
    ) -> str | None:
        if context.source is None:
            return None

        citation_token = f"[source:{citation_number}]"

        if context.page is not None:
            return f"{citation_token} Source: {context.source} (page {context.page})"

        return f"{citation_token} Source: {context.source}"
