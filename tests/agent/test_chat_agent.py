from typing import Protocol

import pytest

from app.agent.chat_agent import ChatAgent
from app.config_models.memory_config import MemoryConfig
from app.config_models.memory_policy_config import (
    MemoryPolicyConfig,
)
from app.config_models.prompt_config import PromptConfig
from app.extractors.regex_fact_extractor import RegexFactExtractor
from app.memory.in_memory_fact_memory import InMemoryFactMemory
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.models.client_response import ClientResponse
from app.models.message import Message
from app.models.message_role import MessageRole
from app.policies.simple_memory_policy import SimpleMemoryPolicy
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_template import PromptTemplate
from tests.fakes.fake_agent_runner import FakeAgentRunner


class ChatAgentFactory(Protocol):
    def __call__(
        self,
        *,
        agent_runner: FakeAgentRunner | None = None,
        memory: SlidingWindowMemory | None = None,
    ) -> ChatAgent: ...


@pytest.fixture
def create_agent() -> ChatAgentFactory:
    def _create_agent(
        *,
        agent_runner: FakeAgentRunner | None = None,
        memory: SlidingWindowMemory | None = None,
    ) -> ChatAgent:
        actual_agent_runner = agent_runner or FakeAgentRunner(
            response=ClientResponse(
                content="測試回覆",
            ),
        )

        actual_memory = memory or SlidingWindowMemory(
            config=MemoryConfig(
                max_history_rounds=10,
            ),
        )

        return ChatAgent(
            prompt_template=PromptTemplate(
                config=PromptConfig(
                    prompt_name="system_prompt.txt",
                    user_name="Frank",
                    language="Traditional Chinese",
                ),
            ),
            agent_runner=actual_agent_runner,
            memory=actual_memory,
            fact_memory=InMemoryFactMemory(),
            fact_extractor=RegexFactExtractor(),
            memory_policy=SimpleMemoryPolicy(
                config=MemoryPolicyConfig(
                    allowed_keys=frozenset(
                        {
                            "user_name",
                            "favorite_music",
                            "occupation",
                        }
                    ),
                ),
            ),
            prompt_composer=PromptComposer(),
        )

    return _create_agent


def test_chat_returns_final_response_from_agent_runner(
    create_agent: ChatAgentFactory,
) -> None:
    agent_runner = FakeAgentRunner(
        response=ClientResponse(
            content="Hello Frank!",
        ),
    )

    agent = create_agent(
        agent_runner=agent_runner,
    )

    result = agent.chat("Hello")

    assert result == "Hello Frank!"


def test_chat_sends_composed_messages_to_agent_runner(
    create_agent: ChatAgentFactory,
) -> None:
    agent_runner = FakeAgentRunner(
        response=ClientResponse(
            content="Hello!",
        ),
    )

    agent = create_agent(
        agent_runner=agent_runner,
    )

    agent.chat("Hello")

    assert len(agent_runner.received_message_batches) == 1

    sent_messages = agent_runner.received_message_batches[0]

    assert (
        Message(
            role=MessageRole.USER,
            content="Hello",
        )
        in sent_messages
    )


def test_get_history_should_return_conversation_messages(
    create_agent: ChatAgentFactory,
) -> None:
    memory = SlidingWindowMemory(
        config=MemoryConfig(
            max_history_rounds=10,
        ),
    )

    agent = create_agent(
        memory=memory,
    )

    agent.chat("Hello")

    assert agent.get_history() == (
        Message(
            role=MessageRole.USER,
            content="Hello",
        ),
        Message(
            role=MessageRole.ASSISTANT,
            content="測試回覆",
        ),
    )


def test_clear_history_should_remove_conversation_messages(
    create_agent: ChatAgentFactory,
) -> None:
    memory = SlidingWindowMemory(
        config=MemoryConfig(
            max_history_rounds=10,
        ),
    )

    agent = create_agent(
        memory=memory,
    )

    agent.chat("Hello")

    agent.clear_history()

    assert agent.get_history() == ()


def test_chat_should_pass_metadata_to_agent_runner(
    create_agent: ChatAgentFactory,
) -> None:
    agent_runner = FakeAgentRunner(
        response=ClientResponse(
            content="Hello!",
        ),
    )

    agent = create_agent(
        agent_runner=agent_runner,
    )

    metadata = {
        "request_id": "request-123",
        "user_id": "frank",
        "source": "test",
    }

    agent.chat(
        "Hello",
        metadata=metadata,
    )

    assert len(agent_runner.received_contexts) == 1

    context = agent_runner.received_contexts[0]

    assert context is not None
    assert context.metadata == metadata


def test_chat_should_use_empty_metadata_by_default(
    create_agent: ChatAgentFactory,
) -> None:
    agent_runner = FakeAgentRunner(
        response=ClientResponse(
            content="Hello!",
        ),
    )

    agent = create_agent(
        agent_runner=agent_runner,
    )

    agent.chat(
        "Hello",
    )

    context = agent_runner.received_contexts[0]

    assert context is not None
    assert context.metadata == {}
