from app.agent.chat_agent_dependencies import (
    ChatAgentDependencies,
)
from app.agent.chat_agent_factory import ChatAgentFactory
from app.config_models.memory_config import MemoryConfig
from app.config_models.memory_policy_config import MemoryPolicyConfig
from app.config_models.prompt_config import PromptConfig
from app.extractors.regex_fact_extractor import RegexFactExtractor
from app.models.client_response import ClientResponse
from app.policies.simple_memory_policy import SimpleMemoryPolicy
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_template import PromptTemplate
from app.retrieval.citations.citation_guard import CitationGuard
from app.retrieval.policies.never_retrieve_policy import NeverRetrievePolicy
from tests.fakes.fake_agent_runner import FakeAgentRunner
from tests.fakes.fake_retriever import FakeRetriever

prompt_template = (
    PromptTemplate(
        config=PromptConfig(
            prompt_name="system_prompt.txt",
            language="Traditional Chinese",
        ),
    ),
)


def create_dependencies() -> ChatAgentDependencies:
    return ChatAgentDependencies(
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
        citation_guard=CitationGuard(),
        retriever=FakeRetriever(),
        retrieval_policy=NeverRetrievePolicy(),
    )


def test_create_should_return_agents_with_independent_history() -> None:
    factory = ChatAgentFactory(
        dependencies=create_dependencies(),
    )

    first_agent = factory.create()
    second_agent = factory.create()

    first_agent.chat("Hello")

    assert len(first_agent.get_history()) == 2
    assert second_agent.get_history() == ()


def test_create_should_return_agents_with_independent_fact_memory() -> None:
    factory = ChatAgentFactory(
        dependencies=create_dependencies(),
    )

    first_agent = factory.create()
    second_agent = factory.create()

    first_agent.chat("My name is Frank.")

    assert first_agent.get_fact("user_name") == "Frank"
    assert second_agent.get_fact("user_name") is None
