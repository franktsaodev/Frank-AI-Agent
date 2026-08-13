from pathlib import Path
from unittest.mock import patch

import pytest

from app.retrieval.document import Document
from app.retrieval.loaders.directory_document_loader import DirectoryDocumentLoader


def test_should_load_supported_files_recursively(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "README content",
        encoding="utf-8",
    )

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "architecture.md").write_text(
        "Architecture content",
        encoding="utf-8",
    )

    (docs_dir / "notes.txt").write_text(
        "Notes content",
        encoding="utf-8",
    )

    loader = DirectoryDocumentLoader(tmp_path)

    documents = loader.load()

    assert {document.content for document in documents} == {
        "README content",
        "Architecture content",
        "Notes content",
    }


def test_should_ignore_unsupported_files(
    tmp_path: Path,
) -> None:
    (tmp_path / "knowledge.md").write_text(
        "Knowledge",
        encoding="utf-8",
    )

    (tmp_path / "image.png").write_bytes(b"fake")

    loader = DirectoryDocumentLoader(tmp_path)

    documents = loader.load()

    assert len(documents) == 1
    assert documents[0].content == "Knowledge"


def test_should_return_empty_list_for_empty_directory(
    tmp_path: Path,
) -> None:
    loader = DirectoryDocumentLoader(tmp_path)

    assert loader.load() == []


def test_should_preserve_source_metadata(
    tmp_path: Path,
) -> None:
    path = tmp_path / "README.md"

    path.write_text(
        "Knowledge",
        encoding="utf-8",
    )

    documents = DirectoryDocumentLoader(tmp_path).load()

    assert documents[0].metadata["source"] == str(path)


def test_should_load_pdf_files(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "manual.pdf"
    pdf_path.write_bytes(b"fake pdf")

    expected_documents = [
        Document(
            content="PDF knowledge",
            metadata={
                "source": str(pdf_path),
                "page": 1,
            },
        )
    ]

    with patch(
        "app.retrieval.loaders.directory_document_loader.PDFDocumentLoader"
    ) as loader_class:
        loader_instance = loader_class.return_value
        loader_instance.load.return_value = expected_documents

        documents = DirectoryDocumentLoader(tmp_path).load()

    loader_class.assert_called_once_with(pdf_path)
    loader_instance.load.assert_called_once_with()

    assert documents == expected_documents


def test_should_skip_document_when_loader_fails(
    tmp_path: Path,
) -> None:
    valid_path = tmp_path / "valid.txt"
    valid_path.write_text(
        "Valid knowledge",
        encoding="utf-8",
    )

    broken_pdf = tmp_path / "broken.pdf"
    broken_pdf.write_bytes(
        b"not a real pdf",
    )

    documents = DirectoryDocumentLoader(tmp_path).load()

    assert len(documents) == 1
    assert documents[0].content == "Valid knowledge"


def test_should_log_warning_when_document_loading_fails(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    broken_pdf = tmp_path / "broken.pdf"
    broken_pdf.write_bytes(
        b"not a real pdf",
    )

    DirectoryDocumentLoader(tmp_path).load()

    assert "Failed to load knowledge document" in caplog.text
    assert "broken.pdf" in caplog.text
