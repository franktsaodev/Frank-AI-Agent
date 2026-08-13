import pytest

from app.config_models.retrieval_config import RetrievalConfig


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
        RetrievalConfig(
            enabled=True,
            knowledge_path="knowledge",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=5,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
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
        RetrievalConfig(
            enabled=True,
            knowledge_path="knowledge",
            chunk_size=500,
            chunk_overlap=50,
            top_k=top_k,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
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
        RetrievalConfig(
            enabled=True,
            knowledge_path=knowledge_path,
            chunk_size=500,
            chunk_overlap=50,
            top_k=5,
            embedding_model=embedding_model,
        )
