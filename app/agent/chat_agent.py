import logging

from app.clients.base_client import BaseClient
from app.extractors.base_fact_extractor import BaseFactExtractor
from app.memory.base_fact_memory import BaseFactMemory
from app.memory.base_memory import BaseMemory
from app.models.message import Message
from app.models.message_role import MessageRole
from app.policies.base_memory_policy import BaseMemoryPolicy
from app.prompts.base_prompt_template import BasePromptTemplate
from app.prompts.prompt_composer import PromptComposer

logger = logging.getLogger(__name__)


class ChatAgent:
    def __init__(
        self,
        prompt_template: BasePromptTemplate,
        client: BaseClient,
        memory: BaseMemory,
        fact_memory: BaseFactMemory,
        fact_extractor: BaseFactExtractor,
        memory_policy: BaseMemoryPolicy,
        prompt_composer: PromptComposer,
    ) -> None:
        logger.info("ChatAgent initialized")

        self.prompt_template = prompt_template
        self.client = client
        self.memory = memory
        self.fact_memory = fact_memory
        self.fact_extractor = fact_extractor
        self.memory_policy = memory_policy
        self.prompt_composer = prompt_composer

        rendered_prompt = self.prompt_template.render()

        if not rendered_prompt.strip():
            raise ValueError("Rendered system prompt cannot be empty")

        self.system_message = Message(
            role=MessageRole.SYSTEM,
            content=rendered_prompt,
        )

    def _remember_extracted_facts(
        self,
        facts: dict[str, str],
    ) -> None:
        if not facts:
            logger.debug("No facts extracted from user message")
            return

        for key, value in facts.items():
            if not self.memory_policy.should_remember(key, value):
                logger.debug(
                    "Rejected extracted fact key=%s value=%r",
                    key,
                    value,
                )
                continue

            self.fact_memory.set(
                key,
                value,
            )

            logger.debug(
                "Remembered extracted fact key=%s value=%r",
                key,
                value,
            )

    def remember_fact(
        self,
        key: str,
        value: str,
    ) -> None:
        self.fact_memory.set(key, value)

    def get_fact(
        self,
        key: str,
    ) -> str | None:
        return self.fact_memory.get(key)

    def forget_fact(
        self,
        key: str,
    ) -> None:
        self.fact_memory.delete(key)

    def chat(
        self,
        message: str,
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

        extracted_facts = self.fact_extractor.extract(
            user_message.content,
        )

        self._remember_extracted_facts(
            extracted_facts,
        )

        history_messages = self.memory.get_messages()
        known_facts = self.fact_memory.get_all()

        messages = self.prompt_composer.compose(
            system_message=self.system_message,
            history_messages=history_messages,
            facts=known_facts,
            user_message=user_message,
        )

        response = self.client.chat(messages)

        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=response,
        )

        self.memory.add_turn(
            user_message=user_message,
            assistant_message=assistant_message,
        )

        logger.info("Chat request completed")

        return response
