from pathlib import Path
from unittest.mock import MagicMock, patch

from app.retrieval.loaders.pdf_document_loader import (
    PDFDocumentLoader,
)


def test_should_load_each_pdf_page_as_document() -> None:
    first_page = MagicMock()
    first_page.extract_text.return_value = "First page"

    second_page = MagicMock()
    second_page.extract_text.return_value = "Second page"

    reader = MagicMock()
    reader.pages = [
        first_page,
        second_page,
    ]

    with patch(
        "app.retrieval.loaders.pdf_document_loader.PdfReader",
        return_value=reader,
    ):
        documents = PDFDocumentLoader(
            Path("manual.pdf"),
        ).load()

    assert len(documents) == 2

    assert documents[0].content == "First page"
    assert documents[0].metadata == {
        "source": "manual.pdf",
        "page": 1,
    }

    assert documents[1].content == "Second page"
    assert documents[1].metadata == {
        "source": "manual.pdf",
        "page": 2,
    }


def test_should_skip_pages_without_text() -> None:
    empty_page = MagicMock()
    empty_page.extract_text.return_value = None

    blank_page = MagicMock()
    blank_page.extract_text.return_value = "   "

    content_page = MagicMock()
    content_page.extract_text.return_value = "Knowledge"

    reader = MagicMock()
    reader.pages = [
        empty_page,
        blank_page,
        content_page,
    ]

    with patch(
        "app.retrieval.loaders.pdf_document_loader.PdfReader",
        return_value=reader,
    ):
        documents = PDFDocumentLoader(
            Path("manual.pdf"),
        ).load()

    assert len(documents) == 1
    assert documents[0].content == "Knowledge"
    assert documents[0].metadata["page"] == 3
