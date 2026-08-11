from pathlib import Path

from app.retrieval.document import Document


class TextFileLoader:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> list[Document]:
        content = self._path.read_text(encoding="utf-8")

        return [
            Document(
                content=content,
                metadata={
                    "source": str(self._path),
                },
            )
        ]
