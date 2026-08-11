from typing import Protocol

from app.retrieval.vector_stores.search_result import SearchResult


class Retriever(Protocol):
    def retrieve(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[SearchResult]: ...
