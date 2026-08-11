import pytest

from app.retrieval.document import Document
from app.retrieval.splitters.fixed_size_text_splitter import FixedSizeTextSplitter


def test_should_split_document_into_fixed_size_chunks() -> None:
    document = Document(content="abcdefghij")

    splitter = FixedSizeTextSplitter(
        chunk_size=4,
    )

    chunks = splitter.split(document)

    assert [chunk.content for chunk in chunks] == [
        "abcd",
        "efgh",
        "ij",
    ]


def test_should_split_with_overlap() -> None:
    document = Document(content="abcdefghij")

    splitter = FixedSizeTextSplitter(
        chunk_size=4,
        chunk_overlap=1,
    )

    chunks = splitter.split(document)

    assert [chunk.content for chunk in chunks] == [
        "abcd",
        "defg",
        "ghij",
    ]


def test_should_preserve_document_metadata() -> None:
    document = Document(
        content="abcdefgh",
        metadata={
            "source": "README.md",
        },
    )

    splitter = FixedSizeTextSplitter(
        chunk_size=4,
    )

    chunks = splitter.split(document)

    assert chunks[0].metadata == {
        "source": "README.md",
        "chunk_index": 0,
    }

    assert chunks[1].metadata == {
        "source": "README.md",
        "chunk_index": 1,
    }


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [
        (0, 0),
        (-1, 0),
        (4, -1),
        (4, 4),
        (4, 5),
    ],
)
def test_should_reject_invalid_chunk_configuration(
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    with pytest.raises(ValueError):
        FixedSizeTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
