import pytest

from app.retrieval.document import Document
from app.retrieval.retrievers.vector_store_retriever import VectorStoreRetriever
from app.retrieval.vector_stores.search_result import SearchResult
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


def test_should_keep_results_with_score_above_min_score() -> None:
    expected_result = SearchResult(
        document=Document(content="Relevant document"),
        score=0.8,
    )
    vector_store = FakeVectorStore(
        search_results=[expected_result],
    )
    retriever = VectorStoreRetriever(
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=vector_store,
        min_score=0.7,
    )

    results = retriever.retrieve("Hello")

    assert results == [expected_result]


def test_should_filter_results_with_score_below_min_score() -> None:
    low_score_result = SearchResult(
        document=Document(content="Irrelevant document"),
        score=0.4,
    )
    vector_store = FakeVectorStore(
        search_results=[low_score_result],
    )
    retriever = VectorStoreRetriever(
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=vector_store,
        min_score=0.7,
    )

    results = retriever.retrieve("Hello")

    assert results == []


def test_should_keep_result_when_score_equals_min_score() -> None:
    boundary_result = SearchResult(
        document=Document(content="Boundary document"),
        score=0.7,
    )
    vector_store = FakeVectorStore(
        search_results=[boundary_result],
    )
    retriever = VectorStoreRetriever(
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=vector_store,
        min_score=0.7,
    )

    results = retriever.retrieve("Hello")

    assert results == [boundary_result]


def test_should_keep_all_results_when_min_score_uses_default() -> None:
    search_results = [
        SearchResult(
            document=Document(content="Positive-score document"),
            score=0.8,
        ),
        SearchResult(
            document=Document(content="Negative-score document"),
            score=-0.2,
        ),
    ]
    vector_store = FakeVectorStore(
        search_results=search_results,
    )
    retriever = VectorStoreRetriever(
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=vector_store,
    )

    results = retriever.retrieve("Hello")

    assert results == search_results


@pytest.mark.parametrize(
    "min_score",
    [
        -1.1,
        1.1,
    ],
)
def test_should_reject_invalid_min_score(
    min_score: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="min_score must be between -1.0 and 1.0",
    ):
        VectorStoreRetriever(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=FakeVectorStore(),
            min_score=min_score,
        )
