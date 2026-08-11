from typing import Protocol

from app.retrieval.document import Document


class TextSplitter(Protocol):
    def split(self, document: Document) -> list[Document]: ...
