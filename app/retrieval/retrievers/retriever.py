from typing import Protocol

from app.retrieval.vector_stores.search_result import SearchResult


class Retriever(Protocol):
    def retrieve(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> list[SearchResult]: ...
