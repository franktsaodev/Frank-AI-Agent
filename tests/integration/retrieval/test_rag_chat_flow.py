from pathlib import Path

from app.agent.chat_agent import ChatAgent
from app.config_models.memory_config import MemoryConfig
from app.config_models.memory_policy_config import MemoryPolicyConfig
from app.config_models.prompt_config import PromptConfig
from app.extractors.regex_fact_extractor import RegexFactExtractor
from app.memory.in_memory_fact_memory import InMemoryFactMemory
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.models.client_response import ClientResponse
from app.policies.simple_memory_policy import SimpleMemoryPolicy
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_template import PromptTemplate
from app.retrieval.embeddings.sentence_transformer_embedding_provider import (
    SentenceTransformerEmbeddingProvider,
)
from app.retrieval.indexing.knowledge_indexer import KnowledgeIndexer
from app.retrieval.loaders.text_file_loader import TextFileLoader
from app.retrieval.policies.always_retrieve_policy import AlwaysRetrievePolicy
from app.retrieval.retrievers.vector_store_retriever import (
    VectorStoreRetriever,
)
from app.retrieval.splitters.fixed_size_text_splitter import (
    FixedSizeTextSplitter,
)
from app.retrieval.vector_stores.in_memory_vector_store import (
    InMemoryVectorStore,
)
from tests.fakes.fake_agent_runner import FakeAgentRunner


def test_chat_should_include_retrieved_knowledge_in_agent_runner_messages(
    tmp_path: Path,
) -> None:
    knowledge_file = tmp_path / "knowledge.txt"

    knowledge_file.write_text(
        (
            "Session Management\n"
            "Frank AI Agent sessions use sliding expiration. "
            "Each session has a configurable time-to-live value. "
            "Expired sessions are removed from the session manager.\n\n"
            "Deployment\n"
            "Frank AI Agent uses Docker to package and deploy the application."
        ),
        encoding="utf-8",
    )

    embedding_provider = SentenceTransformerEmbeddingProvider()
    vector_store = InMemoryVectorStore()

    indexer = KnowledgeIndexer(
        splitter=FixedSizeTextSplitter(
            chunk_size=120,
            chunk_overlap=20,
        ),
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    indexer.index(
        TextFileLoader(
            knowledge_file,
        )
    )

    retriever = VectorStoreRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    agent_runner = FakeAgentRunner(
        response=ClientResponse(
            content="Sessions use sliding expiration.",
        ),
    )

    agent = ChatAgent(
        prompt_template=PromptTemplate(
            config=PromptConfig(
                prompt_name="system_prompt.txt",
                language="Traditional Chinese",
            ),
        ),
        agent_runner=agent_runner,
        memory=SlidingWindowMemory(
            config=MemoryConfig(
                max_history_rounds=10,
            ),
        ),
        fact_memory=InMemoryFactMemory(),
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
        retriever=retriever,
        retrieval_policy=AlwaysRetrievePolicy(),
    )

    agent.chat("How do sessions expire?")

    assert len(agent_runner.received_message_batches) == 1

    messages = agent_runner.received_message_batches[0]

    system_message = messages[0]

    assert system_message.content is not None
    assert "Retrieved knowledge:" in system_message.content
    assert "sliding expiration" in system_message.content
    assert "knowledge.txt" in system_message.content
