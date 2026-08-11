from typing import Protocol

from app.retrieval.document import Document


class DocumentLoader(Protocol):
    def load(self) -> list[Document]: ...
