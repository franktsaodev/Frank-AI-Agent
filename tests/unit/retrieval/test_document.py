import pytest

from app.retrieval.document import Document


def test_should_store_content_and_metadata() -> None:
    document = Document(
        content="Hello RAG",
        metadata={"source": "README.md"},
    )

    assert document.content == "Hello RAG"
    assert document.metadata == {"source": "README.md"}


def test_should_use_empty_metadata_by_default() -> None:
    document = Document(content="Hello RAG")

    assert document.metadata == {}


def test_should_reject_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="content cannot be empty",
    ):
        Document(content="   ")
