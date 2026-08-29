from typing import Protocol
from unittest.mock import MagicMock

import pytest

from app.agent.agent_runner import AgentRunner
from app.agent.chat_agent import ChatAgent
from app.clients.base_client import BaseClient
from app.clock.system_clock import SystemClock
from app.config_models.agent_config import AgentConfig
from app.config_models.memory_config import MemoryConfig
from app.config_models.memory_policy_config import (
    MemoryPolicyConfig,
)
from app.config_models.prompt_config import PromptConfig
from app.extractors.base_fact_extractor import BaseFactExtractor
from app.extractors.regex_fact_extractor import RegexFactExtractor
from app.memory.base_fact_memory import BaseFactMemory
from app.memory.base_memory import BaseMemory
from app.memory.in_memory_fact_memory import InMemoryFactMemory
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.models.client_response import ClientResponse
from app.models.message import Message
from app.models.message_role import MessageRole
from app.policies.base_memory_policy import BaseMemoryPolicy
from app.policies.simple_memory_policy import SimpleMemoryPolicy
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_composer_protocol import (
    PromptComposerProtocol,
)
from app.prompts.prompt_template import PromptTemplate
from app.retrieval.citations.citation_guard import CitationGuard
from app.retrieval.citations.citation_guard_protocol import CitationGuardProtocol
from app.retrieval.policies.never_retrieve_policy import NeverRetrievePolicy
from app.retrieval.policies.retrieval_policy import RetrievalPolicy
from app.retrieval.retrievers.retriever import Retriever
from app.tools.tool_executor_protocol import (
    ToolExecutorProtocol,
)
from app.tracing.base_tracer import BaseTracer
from tests.fakes.fake_client import FakeClient
from tests.fakes.fake_memory_policy import FakeMemoryPolicy
from tests.fakes.fake_prompt_composer import FakePromptComposer
from tests.fakes.fake_retriever import FakeRetriever
from tests.fakes.fake_tool_executor import FakeToolExecutor


class ChatAgentFactory(Protocol):
    def __call__(
        self,
        *,
        client: BaseClient | None = None,
        tool_executor: ToolExecutorProtocol | None = None,
        memory: BaseMemory | None = None,
        fact_memory: BaseFactMemory | None = None,
        fact_extractor: BaseFactExtractor | None = None,
        memory_policy: BaseMemoryPolicy | None = None,
        prompt_composer: PromptComposerProtocol | None = None,
        citation_guard: CitationGuardProtocol | None = None,
        retriever: Retriever | None = None,
        retrieval_policy: RetrievalPolicy | None = None,
    ) -> ChatAgent: ...


@pytest.fixture
def create_agent(
    memory_policy_config: MemoryPolicyConfig,
) -> ChatAgentFactory:
    def _create_agent(
        *,
        client: BaseClient | None = None,
        tool_executor: ToolExecutorProtocol | None = None,
        memory: BaseMemory | None = None,
        fact_memory: BaseFactMemory | None = None,
        fact_extractor: BaseFactExtractor | None = None,
        memory_policy: BaseMemoryPolicy | None = None,
        prompt_composer: PromptComposerProtocol | None = None,
        citation_guard: CitationGuardProtocol | None = None,
        retriever: Retriever | None = None,
        retrieval_policy: RetrievalPolicy | None = None,
    ) -> ChatAgent:
        actual_client = (
            client
            if client is not None
            else FakeClient(
                response=ClientResponse(
                    content="測試回覆",
                ),
            )
        )

        actual_tool_executor = (
            tool_executor if tool_executor is not None else FakeToolExecutor()
        )

        actual_memory = (
            memory
            if memory is not None
            else SlidingWindowMemory(
                config=MemoryConfig(
                    max_history_rounds=10,
                ),
            )
        )

        actual_fact_memory = (
            fact_memory if fact_memory is not None else InMemoryFactMemory()
        )

        actual_fact_extractor = (
            fact_extractor if fact_extractor is not None else RegexFactExtractor()
        )

        actual_memory_policy = (
            memory_policy
            if memory_policy is not None
            else SimpleMemoryPolicy(
                config=memory_policy_config,
            )
        )

        actual_prompt_composer = (
            prompt_composer if prompt_composer is not None else PromptComposer()
        )

        tracer = MagicMock(
            spec=BaseTracer,
        )

        agent_runner = AgentRunner(
            client=actual_client,
            tool_executor=actual_tool_executor,
            tracer=tracer,
            clock=SystemClock(),
            config=AgentConfig(),
        )

        actual_retriever = retriever if retriever is not None else FakeRetriever()

        actual_retrieval_policy = (
            retrieval_policy if retrieval_policy is not None else NeverRetrievePolicy()
        )

        actual_citation_guard = (
            citation_guard if citation_guard is not None else CitationGuard()
        )

        return ChatAgent(
            prompt_template=PromptTemplate(
                config=PromptConfig(
                    prompt_name="system_prompt.txt",
                    language="Traditional Chinese",
                ),
            ),
            agent_runner=agent_runner,
            memory=actual_memory,
            fact_memory=actual_fact_memory,
            fact_extractor=actual_fact_extractor,
            memory_policy=actual_memory_policy,
            prompt_composer=actual_prompt_composer,
            citation_guard=actual_citation_guard,
            retriever=actual_retriever,
            retrieval_policy=actual_retrieval_policy,
        )

    return _create_agent


@pytest.fixture
def agent(
    create_agent: ChatAgentFactory,
) -> ChatAgent:
    return create_agent()


@pytest.fixture
def memory_policy_config() -> MemoryPolicyConfig:
    return MemoryPolicyConfig(
        allowed_keys=frozenset(
            {
                "user_name",
                "favorite_music",
                "occupation",
            }
        ),
    )


def test_chat_automatically_remembers_extracted_fact(
    agent: ChatAgent,
) -> None:
    agent.chat("My name is Frank.")

    assert agent.get_fact("user_name") == "Frank"


def test_chat_does_not_create_fact_when_none_is_extracted(
    agent: ChatAgent,
) -> None:
    agent.chat("How are you?")

    assert agent.get_fact("user_name") is None


def test_extracted_fact_is_injected_into_system_message(
    create_agent: ChatAgentFactory,
) -> None:
    client = FakeClient(
        response=ClientResponse(
            content="測試回覆",
        ),
    )

    agent = create_agent(
        client=client,
    )

    agent.chat("My name is Frank.")

    assert client.call_count == 1

    system_message = client.received_messages[0]

    assert system_message.content is not None
    assert "User facts:" in system_message.content
    assert "- user_name: Frank" in system_message.content


def test_chat_stores_conversation_turn(
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

    agent.chat("My name is Frank.")

    assert memory.get_messages() == (
        Message(
            role=MessageRole.USER,
            content="My name is Frank.",
        ),
        Message(
            role=MessageRole.ASSISTANT,
            content="測試回覆",
        ),
    )


def test_new_extracted_fact_overwrites_existing_fact(
    create_agent: ChatAgentFactory,
) -> None:
    client = FakeClient(
        responses=[
            ClientResponse(
                content="第一次測試回覆",
            ),
            ClientResponse(
                content="第二次測試回覆",
            ),
        ],
    )

    agent = create_agent(
        client=client,
    )

    agent.chat("My name is Frank.")
    agent.chat("My name is David.")

    assert agent.get_fact("user_name") == "David"


def test_chat_agent_stores_memory_policy(
    create_agent: ChatAgentFactory,
    memory_policy_config: MemoryPolicyConfig,
) -> None:
    memory_policy = SimpleMemoryPolicy(
        config=memory_policy_config,
    )

    agent = create_agent(
        memory_policy=memory_policy,
    )

    assert agent._memory_policy is memory_policy


def test_chat_does_not_store_fact_when_memory_policy_rejects_it(
    create_agent: ChatAgentFactory,
) -> None:
    memory_policy = FakeMemoryPolicy(
        should_remember_result=False,
    )

    agent = create_agent(
        memory_policy=memory_policy,
    )

    agent.chat("My name is Frank.")

    assert agent.get_fact("user_name") is None


def test_chat_stores_fact_when_memory_policy_allows_it(
    create_agent: ChatAgentFactory,
) -> None:
    memory_policy = FakeMemoryPolicy(
        should_remember_result=True,
    )

    agent = create_agent(
        memory_policy=memory_policy,
    )

    agent.chat("My name is Frank.")

    assert agent.get_fact("user_name") == "Frank"
    assert memory_policy.received_key == "user_name"
    assert memory_policy.received_value == "Frank"


def test_chat_passes_context_to_prompt_composer_and_sends_composed_messages_to_client(
    create_agent: ChatAgentFactory,
) -> None:
    composed_messages = [
        Message(
            role=MessageRole.SYSTEM,
            content="Composed system prompt",
        ),
        Message(
            role=MessageRole.USER,
            content="Hello",
        ),
    ]

    memory = SlidingWindowMemory(
        config=MemoryConfig(
            max_history_rounds=10,
        ),
    )

    memory.add_turn(
        user_message=Message(
            role=MessageRole.USER,
            content="Previous question",
        ),
        assistant_message=Message(
            role=MessageRole.ASSISTANT,
            content="Previous answer",
        ),
    )

    expected_history_messages = list(memory.get_messages())

    fact_memory = InMemoryFactMemory()

    fact_memory.set(
        key="user_name",
        value="Frank",
    )

    expected_facts = dict(fact_memory.get_all())

    fake_prompt_composer = FakePromptComposer(
        composed_messages=composed_messages,
    )

    client = FakeClient(
        response=ClientResponse(
            content="測試回覆",
        ),
    )

    agent = create_agent(
        client=client,
        memory=memory,
        fact_memory=fact_memory,
        prompt_composer=fake_prompt_composer,
    )

    agent.chat("Hello")

    assert fake_prompt_composer.received_system_message == agent.system_message

    assert fake_prompt_composer.received_history_messages == expected_history_messages

    assert fake_prompt_composer.received_facts == expected_facts

    assert fake_prompt_composer.received_user_message == Message(
        role=MessageRole.USER,
        content="Hello",
    )

    assert client.received_messages == composed_messages

    assert fake_prompt_composer.received_retrieved_contexts == []
