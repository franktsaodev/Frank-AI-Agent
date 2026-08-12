from pathlib import Path

from pypdf import PdfReader

from app.retrieval.document import Document


class PDFDocumentLoader:
    def __init__(
        self,
        path: Path,
    ) -> None:
        self._path = path

    def load(self) -> list[Document]:
        reader = PdfReader(self._path)

        documents: list[Document] = []

        for page_index, page in enumerate(
            reader.pages,
            start=1,
        ):
            content = page.extract_text()

            if content is None or not content.strip():
                continue

            documents.append(
                Document(
                    content=content,
                    metadata={
                        "source": str(self._path),
                        "page": page_index,
                    },
                )
            )

        return documents
