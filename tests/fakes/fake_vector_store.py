from app.retrieval.document import Document
from app.retrieval.vector_stores.search_result import SearchResult


class FakeVectorStore:
    def __init__(self) -> None:
        self.last_query_embedding: list[float] | None = None
        self.last_limit: int | None = None
        self.added_documents: list[Document] = []
        self.added_embeddings: list[list[float]] = []

    def add(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
    ) -> None:
        self.added_documents = list(documents)
        self.added_embeddings = [list(embedding) for embedding in embeddings]

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[SearchResult]:
        self.last_query_embedding = query_embedding
        self.last_limit = limit

        return []
