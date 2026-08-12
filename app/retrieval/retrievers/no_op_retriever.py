from app.retrieval.vector_stores.search_result import SearchResult


class NoOpRetriever:
    def retrieve(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> list[SearchResult]:
        return []
