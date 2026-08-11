from datetime import UTC, datetime

from app.agent.chat_agent_dependencies import (
    ChatAgentDependencies,
)
from app.agent.chat_agent_factory import ChatAgentFactory
from app.config_models.memory_config import MemoryConfig
from app.config_models.memory_policy_config import (
    MemoryPolicyConfig,
)
from app.config_models.prompt_config import PromptConfig
from app.config_models.session_config import SessionConfig
from app.extractors.regex_fact_extractor import (
    RegexFactExtractor,
)
from app.models.client_response import ClientResponse
from app.policies.simple_memory_policy import (
    SimpleMemoryPolicy,
)
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_template import PromptTemplate
from app.retrieval.policies.never_retrieve_policy import NeverRetrievePolicy
from app.session.in_memory_session_manager import (
    InMemorySessionManager,
)
from app.session.session_factory import SessionFactory
from tests.fakes.fake_agent_runner import FakeAgentRunner
from tests.fakes.fake_retriever import FakeRetriever
from tests.fakes.fake_session_clock import (
    FakeSessionClock,
)


def create_session_manager() -> InMemorySessionManager:
    dependencies = ChatAgentDependencies(
        prompt_template=PromptTemplate(
            config=PromptConfig(
                prompt_name="system_prompt.txt",
                language="Traditional Chinese",
            ),
        ),
        agent_runner=FakeAgentRunner(
            response=ClientResponse(
                content="測試回覆",
            ),
        ),
        memory_config=MemoryConfig(
            max_history_rounds=10,
        ),
        fact_extractor=RegexFactExtractor(),
        memory_policy=SimpleMemoryPolicy(
            config=MemoryPolicyConfig(
                allowed_keys=frozenset(
                    {
                        "user_name",
                    }
                ),
            ),
        ),
        prompt_composer=PromptComposer(),
        retriever=FakeRetriever(),
        retrieval_policy=NeverRetrievePolicy(),
    )

    return InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=ChatAgentFactory(
            dependencies=dependencies,
        ),
        clock=FakeSessionClock(
            current_time=datetime(
                2026,
                8,
                6,
                3,
                0,
                tzinfo=UTC,
            ),
        ),
        config=SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
    )


def test_sessions_should_have_independent_fact_memory() -> None:
    manager = create_session_manager()

    first_session = manager.create()
    second_session = manager.create()

    first_session.agent.chat(
        "My name is Frank.",
    )

    assert first_session.agent.get_fact("user_name") == "Frank"

    assert second_session.agent.get_fact("user_name") is None


def test_sessions_should_have_independent_conversation_history() -> None:
    manager = create_session_manager()

    first_session = manager.create()
    second_session = manager.create()

    first_session.agent.chat(
        "Hello",
    )

    assert len(first_session.agent.get_history()) == 2

    assert second_session.agent.get_history() == ()


def test_session_manager_should_preserve_session_agent() -> None:
    manager = create_session_manager()

    created_session = manager.create()

    retrieved_session = manager.get(
        created_session.session_id,
    )

    assert retrieved_session is not created_session
    assert retrieved_session.session_id == created_session.session_id
    assert retrieved_session.agent is created_session.agent
    assert retrieved_session.created_at == created_session.created_at
