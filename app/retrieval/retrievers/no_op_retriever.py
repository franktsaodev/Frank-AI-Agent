from app.retrieval.vector_stores.search_result import SearchResult


class NoOpRetriever:
    def retrieve(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[SearchResult]:
        return []
