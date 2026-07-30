from collections.abc import Callable

import pytest

from app.agent.chat_agent import ChatAgent
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


@pytest.fixture
def create_agent() -> Callable[..., ChatAgent]:
    def _create_agent(
        *,
        agent_runner: FakeAgentRunner,
    ) -> ChatAgent:
        return ChatAgent(
            prompt_template=PromptTemplate(
                config=PromptConfig(
                    prompt_name="system_prompt.txt",
                    user_name="Frank",
                    language="Traditional Chinese",
                ),
            ),
            agent_runner=agent_runner,
            memory=SlidingWindowMemory(
                max_rounds=10,
            ),
            fact_memory=InMemoryFactMemory(),
            fact_extractor=RegexFactExtractor(),
            memory_policy=SimpleMemoryPolicy(),
            prompt_composer=PromptComposer(),
        )

    return _create_agent


def test_chat_returns_final_response_from_agent_runner(
    create_agent,
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
    create_agent,
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
