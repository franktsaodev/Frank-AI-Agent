from app.retrieval.vector_stores.search_result import SearchResult


class FakeRetriever:
    def __init__(
        self,
        results: list[SearchResult] | None = None,
    ) -> None:
        self._results = results or []
        self.call_count = 0
        self.last_query: str | None = None

    def retrieve(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[SearchResult]:
        self.call_count += 1
        self.last_query = query

        return self._results[:limit]
