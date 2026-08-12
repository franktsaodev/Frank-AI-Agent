import pytest

from app.retrieval.retrievers.vector_store_retriever import VectorStoreRetriever
from tests.fakes.fake_embedding_provider import FakeEmbeddingProvider
from tests.fakes.fake_vector_store import FakeVectorStore


def test_should_embed_query_and_pass_embedding_to_vector_store() -> None:
    embedding_provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    retriever = VectorStoreRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    retriever.retrieve("Hello")

    assert vector_store.last_query_embedding == embedding_provider.embed(["Hello"])[0]


def test_should_pass_limit_to_vector_store() -> None:
    embedding_provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    retriever = VectorStoreRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    retriever.retrieve(
        "Hello",
        limit=3,
    )

    assert vector_store.last_limit == 3


def test_should_reject_empty_query() -> None:
    retriever = VectorStoreRetriever(
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore(),
    )

    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        retriever.retrieve("   ")


def test_should_use_default_limit_when_limit_is_not_provided() -> None:
    embedding_provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    retriever = VectorStoreRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        default_limit=3,
    )

    retriever.retrieve("Hello")

    assert vector_store.last_limit == 3


def test_should_override_default_limit_when_limit_is_provided() -> None:
    embedding_provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()

    retriever = VectorStoreRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        default_limit=5,
    )

    retriever.retrieve(
        "Hello",
        limit=2,
    )

    assert vector_store.last_limit == 2


@pytest.mark.parametrize(
    "default_limit",
    [
        0,
        -1,
    ],
)
def test_should_reject_invalid_default_limit(
    default_limit: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="default_limit must be greater than 0",
    ):
        VectorStoreRetriever(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=FakeVectorStore(),
            default_limit=default_limit,
        )
