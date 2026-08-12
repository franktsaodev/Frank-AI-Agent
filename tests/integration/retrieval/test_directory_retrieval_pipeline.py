from pathlib import Path

import pytest

from app.retrieval.embeddings.sentence_transformer_embedding_provider import (
    SentenceTransformerEmbeddingProvider,
)
from app.retrieval.indexing.knowledge_indexer import KnowledgeIndexer
from app.retrieval.loaders.directory_document_loader import (
    DirectoryDocumentLoader,
)
from app.retrieval.retrievers.vector_store_retriever import (
    VectorStoreRetriever,
)
from app.retrieval.splitters.fixed_size_text_splitter import (
    FixedSizeTextSplitter,
)
from app.retrieval.vector_stores.in_memory_vector_store import (
    InMemoryVectorStore,
)


@pytest.fixture
def directory_retriever(
    tmp_path: Path,
) -> VectorStoreRetriever:
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()

    (knowledge_dir / "session.md").write_text(
        (
            "# Session Management\n\n"
            "Frank AI Agent sessions use sliding expiration. "
            "Each session has a configurable time-to-live value."
        ),
        encoding="utf-8",
    )

    (knowledge_dir / "deployment.txt").write_text(
        (
            "Deployment\n\n"
            "Frank AI Agent uses Docker to package and deploy the application. "
            "The API service runs inside a Docker container."
        ),
        encoding="utf-8",
    )

    memory_dir = knowledge_dir / "memory"
    memory_dir.mkdir()

    (memory_dir / "memory.md").write_text(
        (
            "# Memory\n\n"
            "Frank AI Agent supports conversation memory and structured fact memory. "
            "Conversation history and user facts are managed separately."
        ),
        encoding="utf-8",
    )

    embedding_provider = SentenceTransformerEmbeddingProvider()
    vector_store = InMemoryVectorStore()

    indexer = KnowledgeIndexer(
        splitter=FixedSizeTextSplitter(
            chunk_size=200,
            chunk_overlap=20,
        ),
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    indexer.index(
        DirectoryDocumentLoader(
            knowledge_dir,
        )
    )

    return VectorStoreRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        default_limit=3,
    )


def test_should_retrieve_session_document_from_directory(
    directory_retriever: VectorStoreRetriever,
) -> None:
    results = directory_retriever.retrieve(
        "How do sessions expire?",
        limit=1,
    )

    assert len(results) == 1
    assert "sliding expiration" in results[0].document.content
    assert "session.md" in results[0].document.metadata["source"]


def test_should_retrieve_deployment_document_from_directory(
    directory_retriever: VectorStoreRetriever,
) -> None:
    results = directory_retriever.retrieve(
        "How is the application deployed?",
        limit=1,
    )

    assert len(results) == 1
    assert "Docker" in results[0].document.content
    assert "deployment.txt" in results[0].document.metadata["source"]


def test_should_retrieve_nested_document_recursively(
    directory_retriever: VectorStoreRetriever,
) -> None:
    results = directory_retriever.retrieve(
        "What kinds of memory does the agent support?",
        limit=1,
    )

    assert len(results) == 1
    assert "structured fact memory" in results[0].document.content
    assert "memory.md" in results[0].document.metadata["source"]
