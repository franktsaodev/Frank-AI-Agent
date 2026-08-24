import pytest

from app.config_models.retrieval_config import RetrievalConfig


def create_retrieval_config(
    *,
    knowledge_path: str = "knowledge",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    top_k: int = 5,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    trigger_keywords: frozenset[str] = frozenset(
        {
            "documentation",
            "manual",
            "session",
        }
    ),
) -> RetrievalConfig:
    return RetrievalConfig(
        enabled=True,
        knowledge_path=knowledge_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k=top_k,
        embedding_model=embedding_model,
        trigger_keywords=trigger_keywords,
    )


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [
        (0, 0),
        (-1, 0),
        (100, -1),
        (100, 100),
        (100, 101),
    ],
)
def test_should_reject_invalid_chunk_configuration(
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    with pytest.raises(ValueError):
        create_retrieval_config(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )


@pytest.mark.parametrize(
    "top_k",
    [0, -1],
)
def test_should_reject_invalid_top_k(
    top_k: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="top_k must be greater than 0",
    ):
        create_retrieval_config(
            top_k=top_k,
        )


@pytest.mark.parametrize(
    ("knowledge_path", "embedding_model"),
    [
        ("", "model"),
        ("   ", "model"),
        ("knowledge", ""),
        ("knowledge", "   "),
    ],
)
def test_should_reject_blank_required_values(
    knowledge_path: str,
    embedding_model: str,
) -> None:
    with pytest.raises(ValueError):
        create_retrieval_config(
            knowledge_path=knowledge_path,
            embedding_model=embedding_model,
        )


def test_should_allow_empty_trigger_keywords() -> None:
    config = create_retrieval_config(
        trigger_keywords=frozenset(),
    )

    assert config.trigger_keywords == frozenset()
