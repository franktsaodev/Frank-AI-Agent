from app.retrieval.document import Document
from app.retrieval.indexing.knowledge_indexer import KnowledgeIndexer
from app.retrieval.splitters.fixed_size_text_splitter import FixedSizeTextSplitter
from tests.fakes.fake_document_loader import FakeDocumentLoader
from tests.fakes.fake_embedding_provider import FakeEmbeddingProvider
from tests.fakes.fake_vector_store import FakeVectorStore


def test_should_load_split_embed_and_store_documents() -> None:
    loader = FakeDocumentLoader(
        documents=[
            Document(
                content="abcdefgh",
                metadata={"source": "README.md"},
            )
        ]
    )

    splitter = FixedSizeTextSplitter(
        chunk_size=4,
    )

    embedding_provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    indexer = KnowledgeIndexer(
        splitter=splitter,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    indexer.index(loader)

    assert vector_store.added_documents == [
        Document(
            content="abcd",
            metadata={
                "source": "README.md",
                "chunk_index": 0,
            },
        ),
        Document(
            content="efgh",
            metadata={
                "source": "README.md",
                "chunk_index": 1,
            },
        ),
    ]


def test_should_not_embed_or_store_when_loader_returns_no_documents() -> None:
    loader = FakeDocumentLoader(
        documents=[],
    )

    embedding_provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    indexer = KnowledgeIndexer(
        splitter=FixedSizeTextSplitter(
            chunk_size=4,
        ),
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    indexer.index(loader)

    assert vector_store.added_documents == []
    assert vector_store.added_embeddings == []
