from pathlib import Path

import pytest

from app.retrieval.embeddings.sentence_transformer_embedding_provider import (
    SentenceTransformerEmbeddingProvider,
)
from app.retrieval.indexing.knowledge_indexer import KnowledgeIndexer
from app.retrieval.loaders.text_file_loader import TextFileLoader
from app.retrieval.retrievers.vector_store_retriever import VectorStoreRetriever
from app.retrieval.splitters.recursive_text_splitter import (
    RecursiveTextSplitter,
)
from app.retrieval.vector_stores.in_memory_vector_store import InMemoryVectorStore


@pytest.fixture
def semantic_retriever(
    tmp_path: Path,
) -> VectorStoreRetriever:
    knowledge_file = tmp_path / "knowledge.txt"

    knowledge_file.write_text(
        (
            "Session Management\n"
            "Frank AI Agent sessions use sliding expiration. "
            "Each session has a configurable time-to-live value. "
            "Expired sessions are removed from the session manager.\n\n"
            "Deployment\n"
            "Frank AI Agent uses Docker to package and deploy the application. "
            "The API service runs inside a Docker container.\n\n"
            "Memory\n"
            "Frank AI Agent supports conversation memory and structured fact memory. "
            "Conversation history and user facts are managed separately."
        ),
        encoding="utf-8",
    )

    embedding_provider = SentenceTransformerEmbeddingProvider()
    vector_store = InMemoryVectorStore()

    indexer = KnowledgeIndexer(
        splitter=RecursiveTextSplitter(
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

    return VectorStoreRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        min_score=0.2,
    )


def test_should_retrieve_session_related_document(
    semantic_retriever: VectorStoreRetriever,
) -> None:
    results = semantic_retriever.retrieve(
        "How do sessions expire?",
        limit=1,
    )

    assert len(results) == 1
    assert "sliding expiration" in results[0].document.content


def test_should_retrieve_deployment_related_document(
    semantic_retriever: VectorStoreRetriever,
) -> None:
    results = semantic_retriever.retrieve(
        "How is the application deployed?",
        limit=1,
    )

    assert len(results) == 1
    assert "Docker" in results[0].document.content


def test_should_filter_irrelevant_results_below_min_score(
    semantic_retriever: VectorStoreRetriever,
) -> None:
    results = semantic_retriever.retrieve(
        "What is the weather in Hanoi today?",
        limit=3,
    )

    assert results == []
