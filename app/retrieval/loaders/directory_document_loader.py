from pathlib import Path

from app.retrieval.document import Document
from app.retrieval.loaders.pdf_document_loader import PDFDocumentLoader
from app.retrieval.loaders.text_file_loader import TextFileLoader


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

            documents.extend(loader.load())

        return documents
