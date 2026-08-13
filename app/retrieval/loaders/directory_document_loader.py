import logging
from pathlib import Path

from app.retrieval.document import Document
from app.retrieval.loaders.pdf_document_loader import PDFDocumentLoader
from app.retrieval.loaders.text_file_loader import TextFileLoader

logger = logging.getLogger(__name__)


class DirectoryDocumentLoader:
    def __init__(
        self,
        path: Path,
    ) -> None:
        self._path = path

    def load(self) -> list[Document]:
        documents: list[Document] = []

        for file_path in sorted(self._path.rglob("*")):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.casefold()

            if suffix in {
                ".txt",
                ".md",
            }:
                loader = TextFileLoader(file_path)
            elif suffix == ".pdf":
                loader = PDFDocumentLoader(file_path)
            else:
                continue

            try:
                documents.extend(loader.load())
            except Exception:
                logger.warning(
                    "Failed to load knowledge document: %s",
                    file_path,
                    exc_info=True,
                )

        return documents
