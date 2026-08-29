import pytest

from app.retrieval.document import Document
from app.retrieval.splitters.recursive_text_splitter import (
    RecursiveTextSplitter,
)


def test_should_return_short_document_as_single_chunk() -> None:
    document = Document(
        content="Short document.",
        metadata={
            "source": "README.md",
        },
    )
    splitter = RecursiveTextSplitter(
        chunk_size=100,
    )

    chunks = splitter.split(document)

    assert len(chunks) == 1
    assert chunks[0].content == "Short document."
    assert chunks[0].metadata == {
        "source": "README.md",
        "chunk_index": 0,
    }


def test_should_prefer_paragraph_boundaries() -> None:
    document = Document(
        content="First paragraph.\n\nSecond paragraph.",
    )
    splitter = RecursiveTextSplitter(
        chunk_size=20,
    )

    chunks = splitter.split(document)

    assert [chunk.content for chunk in chunks] == [
        "First paragraph.",
        "Second paragraph.",
    ]


def test_should_fall_back_to_whitespace_boundaries() -> None:
    document = Document(
        content="alpha beta gamma delta",
    )
    splitter = RecursiveTextSplitter(
        chunk_size=12,
    )

    chunks = splitter.split(document)

    assert [chunk.content for chunk in chunks] == [
        "alpha beta",
        "gamma delta",
    ]


def test_should_hard_split_when_no_boundary_exists() -> None:
    document = Document(
        content="abcdefghij",
    )
    splitter = RecursiveTextSplitter(
        chunk_size=4,
    )

    chunks = splitter.split(document)

    assert [chunk.content for chunk in chunks] == [
        "abcd",
        "efgh",
        "ij",
    ]


def test_should_not_create_chunks_larger_than_chunk_size() -> None:
    document = Document(
        content=(
            "First paragraph contains several words.\n\n"
            "Second paragraph also contains several words."
        ),
    )
    splitter = RecursiveTextSplitter(
        chunk_size=20,
    )

    chunks = splitter.split(document)

    assert chunks
    assert all(len(chunk.content) <= 20 for chunk in chunks)


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
        RecursiveTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )


def test_should_apply_overlap_at_word_boundary() -> None:
    document = Document(
        content="alpha beta gamma delta",
    )
    splitter = RecursiveTextSplitter(
        chunk_size=16,
        chunk_overlap=6,
    )

    chunks = splitter.split(document)

    assert [chunk.content for chunk in chunks] == [
        "alpha beta gamma",
        "gamma delta",
    ]


def test_should_apply_character_overlap_to_long_unbroken_text() -> None:
    document = Document(
        content="abcdefghij",
    )
    splitter = RecursiveTextSplitter(
        chunk_size=4,
        chunk_overlap=1,
    )

    chunks = splitter.split(document)

    assert [chunk.content for chunk in chunks] == [
        "abcd",
        "defg",
        "ghij",
    ]


def test_should_apply_overlap_at_paragraph_boundary() -> None:
    document = Document(
        content=("Alpha paragraph.\n\nBeta paragraph.\n\nGamma paragraph."),
    )
    splitter = RecursiveTextSplitter(
        chunk_size=35,
        chunk_overlap=20,
    )

    chunks = splitter.split(document)

    assert [chunk.content for chunk in chunks] == [
        "Alpha paragraph.\n\nBeta paragraph.",
        "Beta paragraph.\n\nGamma paragraph.",
    ]


def test_should_preserve_metadata_for_each_chunk() -> None:
    document = Document(
        content="alpha beta gamma delta",
        metadata={
            "source": "knowledge.txt",
            "page": 2,
        },
    )
    splitter = RecursiveTextSplitter(
        chunk_size=12,
    )

    chunks = splitter.split(document)

    assert [chunk.metadata for chunk in chunks] == [
        {
            "source": "knowledge.txt",
            "page": 2,
            "chunk_index": 0,
        },
        {
            "source": "knowledge.txt",
            "page": 2,
            "chunk_index": 1,
        },
    ]


def test_should_merge_small_heading_with_following_content() -> None:
    document = Document(
        content=(
            "Deployment\n"
            "Frank AI Agent uses Docker containers "
            "to package and deploy the application."
        ),
    )
    splitter = RecursiveTextSplitter(
        chunk_size=40,
    )

    chunks = splitter.split(document)

    assert chunks[0].content.startswith("Deployment\nFrank AI Agent")
    assert all(len(chunk.content) <= 40 for chunk in chunks)
