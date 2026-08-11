from app.retrieval.document import Document
from app.retrieval.vector_stores.search_result import SearchResult


class FakeVectorStore:
    def __init__(self) -> None:
        self.last_query_embedding: list[float] | None = None
        self.last_limit: int | None = None

    def add(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
    ) -> None:
        pass

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[SearchResult]:
        self.last_query_embedding = query_embedding
        self.last_limit = limit

        return []
