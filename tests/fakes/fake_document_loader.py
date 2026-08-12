from app.retrieval.document import Document


class FakeDocumentLoader:
    def __init__(
        self,
        documents: list[Document],
    ) -> None:
        self._documents = documents

    def load(self) -> list[Document]:
        return list(self._documents)
