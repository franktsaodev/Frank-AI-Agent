from app.retrieval.embeddings.embedding_provider import EmbeddingProvider
from app.retrieval.vector_stores.search_result import SearchResult
from app.retrieval.vector_stores.vector_store import VectorStore


class VectorStoreRetriever:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        default_limit: int = 5,
        min_score: float = 0.0,
    ) -> None:
        if default_limit <= 0:
            raise ValueError("default_limit must be greater than 0")

        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0")

        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._default_limit = default_limit
        self._min_score = min_score

    def retrieve(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("query cannot be empty")

        effective_limit = self._default_limit if limit is None else limit

        query_embedding = self._embedding_provider.embed([query])[0]

        results = self._vector_store.search(
            query_embedding,
            limit=effective_limit,
        )

        return [result for result in results if result.score >= self._min_score]
