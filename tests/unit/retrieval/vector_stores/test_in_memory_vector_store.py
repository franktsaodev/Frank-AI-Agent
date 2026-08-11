import pytest

from app.retrieval.document import Document
from app.retrieval.vector_stores.in_memory_vector_store import InMemoryVectorStore


def test_should_add_and_search_documents() -> None:
    store = InMemoryVectorStore()

    documents = [
        Document(content="Python"),
        Document(content="Docker"),
    ]

    embeddings = [
        [1.0, 0.0],
        [0.0, 1.0],
    ]

    store.add(documents, embeddings)

    results = store.search(
        [1.0, 0.0],
        limit=1,
    )

    assert len(results) == 1
    assert results[0].document.content == "Python"
    assert results[0].score == pytest.approx(1.0)


def test_should_return_results_ordered_by_similarity() -> None:
    store = InMemoryVectorStore()

    store.add(
        [
            Document(content="A"),
            Document(content="B"),
            Document(content="C"),
        ],
        [
            [1.0, 0.0],
            [0.8, 0.2],
            [0.0, 1.0],
        ],
    )

    results = store.search(
        [1.0, 0.0],
        limit=2,
    )

    assert [result.document.content for result in results] == ["A", "B"]


def test_should_reject_mismatched_documents_and_embeddings() -> None:
    store = InMemoryVectorStore()

    with pytest.raises(
        ValueError,
        match="same length",
    ):
        store.add(
            [Document(content="A")],
            [
                [1.0, 0.0],
                [0.0, 1.0],
            ],
        )


@pytest.mark.parametrize("limit", [0, -1])
def test_should_reject_invalid_limit(limit: int) -> None:
    store = InMemoryVectorStore()

    with pytest.raises(
        ValueError,
        match="limit must be greater than 0",
    ):
        store.search(
            [1.0, 0.0],
            limit=limit,
        )
