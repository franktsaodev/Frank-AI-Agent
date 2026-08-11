from typing import Protocol

from app.retrieval.document import Document
from app.retrieval.vector_stores.search_result import SearchResult


class VectorStore(Protocol):
    def add(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
    ) -> None: ...

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[SearchResult]: ...
