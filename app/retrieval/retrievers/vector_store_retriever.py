from app.retrieval.embeddings.embedding_provider import EmbeddingProvider
from app.retrieval.vector_stores.search_result import SearchResult
from app.retrieval.vector_stores.vector_store import VectorStore


class VectorStoreRetriever:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def retrieve(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("query cannot be empty")

        query_embedding = self._embedding_provider.embed([query])[0]

        return self._vector_store.search(
            query_embedding,
            limit=limit,
        )
