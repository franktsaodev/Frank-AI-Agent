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
from app.prompts.prompt_composer_protocol import PromptComposerProtocol
from app.prompts.prompt_template import PromptTemplate
from app.retrieval.document import Document
from app.retrieval.policies.always_retrieve_policy import AlwaysRetrievePolicy
from app.retrieval.policies.never_retrieve_policy import NeverRetrievePolicy
from app.retrieval.policies.retrieval_policy import RetrievalPolicy
from app.retrieval.retrieved_context import RetrievedContext
from app.retrieval.retrievers.retriever import Retriever
from app.retrieval.vector_stores.search_result import SearchResult
from tests.fakes.fake_agent_runner import FakeAgentRunner
from tests.fakes.fake_prompt_composer import FakePromptComposer
from tests.fakes.fake_retriever import FakeRetriever


class ChatAgentFactory(Protocol):
    def __call__(
        self,
        *,
        agent_runner: FakeAgentRunner | None = None,
        memory: SlidingWindowMemory | None = None,
        prompt_composer: PromptComposerProtocol | None = None,
        retriever: Retriever | None = None,
        retrieval_policy: RetrievalPolicy | None = None,
    ) -> ChatAgent: ...


@pytest.fixture
def create_agent() -> ChatAgentFactory:
    def _create_agent(
        *,
        agent_runner: FakeAgentRunner | None = None,
        memory: SlidingWindowMemory | None = None,
        prompt_composer: PromptComposerProtocol | None = None,
        retriever: Retriever | None = None,
        retrieval_policy: RetrievalPolicy | None = None,
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

        actual_prompt_composer = (
            prompt_composer if prompt_composer is not None else PromptComposer()
        )

        return ChatAgent(
            prompt_template=PromptTemplate(
                config=PromptConfig(
                    prompt_name="system_prompt.txt",
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
            prompt_composer=actual_prompt_composer,
            retriever=retriever or FakeRetriever(),
            retrieval_policy=(
                retrieval_policy
                if retrieval_policy is not None
                else NeverRetrievePolicy()
            ),
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


def test_should_not_retrieve_when_policy_returns_false(
    create_agent: ChatAgentFactory,
) -> None:
    retriever = FakeRetriever()

    agent = create_agent(
        retriever=retriever,
        retrieval_policy=NeverRetrievePolicy(),
    )

    agent.chat("Hello")

    assert retriever.call_count == 0


def test_should_retrieve_when_policy_returns_true(
    create_agent: ChatAgentFactory,
) -> None:
    retriever = FakeRetriever()

    agent = create_agent(
        retriever=retriever,
        retrieval_policy=AlwaysRetrievePolicy(),
    )

    agent.chat("What is the session TTL?")

    assert retriever.call_count == 1
    assert retriever.last_query == "What is the session TTL?"


def test_chat_passes_retrieved_contexts_to_prompt_composer(
    create_agent: ChatAgentFactory,
) -> None:
    retriever = FakeRetriever(
        results=[
            SearchResult(
                document=Document(
                    content="Session TTL is 3600 seconds.",
                    metadata={
                        "source": "README.md",
                    },
                ),
                score=0.9,
            ),
            SearchResult(
                document=Document(
                    content="Sessions use sliding expiration.",
                    metadata={
                        "source": "architecture.md",
                    },
                ),
                score=0.8,
            ),
        ],
    )

    fake_prompt_composer = FakePromptComposer(
        composed_messages=[
            Message(
                role=MessageRole.SYSTEM,
                content="Composed system prompt",
            ),
            Message(
                role=MessageRole.USER,
                content="How do sessions expire?",
            ),
        ],
    )

    agent = create_agent(
        retriever=retriever,
        retrieval_policy=AlwaysRetrievePolicy(),
        prompt_composer=fake_prompt_composer,
    )

    agent.chat("How do sessions expire?")

    assert fake_prompt_composer.received_retrieved_contexts == [
        RetrievedContext(
            content="Session TTL is 3600 seconds.",
            source="README.md",
        ),
        RetrievedContext(
            content="Sessions use sliding expiration.",
            source="architecture.md",
        ),
    ]
