import logging
from collections.abc import Mapping

from app.agent.agent_run_context import AgentRunContext
from app.agent.agent_runner_protocol import (
    AgentRunnerProtocol,
)
from app.extractors.base_fact_extractor import BaseFactExtractor
from app.memory.base_fact_memory import BaseFactMemory
from app.memory.base_memory import BaseMemory
from app.models.message import Message
from app.models.message_role import MessageRole
from app.policies.base_memory_policy import BaseMemoryPolicy
from app.prompts.base_prompt_template import BasePromptTemplate
from app.prompts.prompt_composer_protocol import (
    PromptComposerProtocol,
)
from app.retrieval.citations.citation_guard_protocol import (
    CitationGuardProtocol,
)
from app.retrieval.citations.invalid_citation_error import (
    InvalidCitationError,
)
from app.retrieval.policies.retrieval_policy import RetrievalPolicy
from app.retrieval.retrieved_context import RetrievedContext
from app.retrieval.retrievers.retriever import Retriever
from app.types.json_types import JsonValue

logger = logging.getLogger(__name__)

_GROUNDED_FALLBACK_RESPONSE = (
    "I could not find enough information in the retrieved "
    "knowledge to answer this question."
)


class ChatAgent:
    def __init__(
        self,
        prompt_template: BasePromptTemplate,
        agent_runner: AgentRunnerProtocol,
        memory: BaseMemory,
        fact_memory: BaseFactMemory,
        fact_extractor: BaseFactExtractor,
        memory_policy: BaseMemoryPolicy,
        prompt_composer: PromptComposerProtocol,
        citation_guard: CitationGuardProtocol,
        retriever: Retriever,
        retrieval_policy: RetrievalPolicy,
    ) -> None:
        logger.info("ChatAgent initialized")

        self._prompt_template = prompt_template
        self._agent_runner = agent_runner
        self._memory = memory
        self._fact_memory = fact_memory
        self._fact_extractor = fact_extractor
        self._memory_policy = memory_policy
        self._prompt_composer = prompt_composer
        self._retriever = retriever
        self._retrieval_policy = retrieval_policy
        self._citation_guard = citation_guard
        rendered_prompt = self._prompt_template.render()

        if not rendered_prompt.strip():
            raise ValueError("Rendered system prompt cannot be empty")

        self.system_message = Message(
            role=MessageRole.SYSTEM,
            content=rendered_prompt,
        )

    def chat(
        self,
        message: str,
        *,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> str:
        if not message.strip():
            raise ValueError("User message cannot be empty")

        logger.info(
            "Processing chat request with message_length=%d",
            len(message),
        )

        user_message = Message(
            role=MessageRole.USER,
            content=message,
        )

        extracted_facts = self._fact_extractor.extract(message)

        self._remember_extracted_facts(extracted_facts)

        retrieval_attempted = self._retrieval_policy.should_retrieve(message)

        retrieved_contexts = (
            self._retrieve_contexts(message) if retrieval_attempted else []
        )

        if retrieval_attempted and not retrieved_contexts:
            logger.info("Using grounded fallback because retrieval returned no results")

            return self._complete_turn(
                user_message=user_message,
                response_content=_GROUNDED_FALLBACK_RESPONSE,
            )

        history_messages = self._memory.get_messages()
        known_facts = self._fact_memory.get_all()

        composed_messages = self._prompt_composer.compose(
            system_message=self.system_message,
            history_messages=history_messages,
            facts=known_facts,
            user_message=user_message,
            retrieved_contexts=retrieved_contexts,
        )

        run_context = AgentRunContext(
            metadata=(metadata if metadata is not None else {}),
        )

        response = self._agent_runner.run(
            messages=composed_messages,
            context=run_context,
        )

        if response.content is None:
            raise ValueError("Client response does not contain text content.")

        try:
            guarded_response = self._citation_guard.apply(
                response.content,
                retrieved_contexts,
            )
        except InvalidCitationError as error:
            logger.warning(
                "Rejected response with invalid citation: %s",
                error,
            )
            guarded_response = (
                "I could not provide a response because its citations "
                "could not be verified."
            )

        return self._complete_turn(
            user_message=user_message,
            response_content=guarded_response,
        )

    def remember_fact(
        self,
        key: str,
        value: str,
    ) -> None:
        self._fact_memory.set(key, value)

    def get_fact(
        self,
        key: str,
    ) -> str | None:
        return self._fact_memory.get(key)

    def forget_fact(
        self,
        key: str,
    ) -> None:
        self._fact_memory.delete(key)

    def get_history(
        self,
    ) -> tuple[Message, ...]:
        return tuple(self._memory.get_messages())

    def clear_history(
        self,
    ) -> None:
        self._memory.clear()

    def _complete_turn(
        self,
        *,
        user_message: Message,
        response_content: str,
    ) -> str:
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=response_content,
        )

        self._memory.add_turn(
            user_message=user_message,
            assistant_message=assistant_message,
        )

        logger.info("Chat request completed")

        return response_content

    def _remember_extracted_facts(
        self,
        facts: Mapping[str, str],
    ) -> None:
        if not facts:
            logger.debug(
                "No facts extracted from user message",
            )
            return

        for key, value in facts.items():
            if not self._memory_policy.should_remember(
                key,
                value,
            ):
                logger.debug(
                    "Rejected extracted fact key=%s value=%r",
                    key,
                    value,
                )
                continue

            self._fact_memory.set(
                key,
                value,
            )

            logger.debug(
                "Remembered extracted fact key=%s value=%r",
                key,
                value,
            )

    def _retrieve_contexts(
        self,
        user_input: str,
    ) -> list[RetrievedContext]:
        results = self._retriever.retrieve(user_input)

        return [
            RetrievedContext(
                content=result.document.content,
                source=self._get_source(result.document.metadata),
                page=self._get_page(result.document.metadata),
            )
            for result in results
        ]

    def _get_source(
        self,
        metadata: Mapping[str, object],
    ) -> str | None:
        source = metadata.get("source")

        if isinstance(source, str):
            return source

        return None

    def _get_page(
        self,
        metadata: Mapping[str, object],
    ) -> int | None:
        page = metadata.get("page")

        if isinstance(page, int):
            return page

        return None
