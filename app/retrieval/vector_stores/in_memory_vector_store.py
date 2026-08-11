import math

from app.retrieval.document import Document
from app.retrieval.vector_stores.search_result import SearchResult


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._entries: list[tuple[Document, list[float]]] = []

    def add(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
    ) -> None:
        if len(documents) != len(embeddings):
            raise ValueError("documents and embeddings must have the same length")

        self._entries.extend(zip(documents, embeddings))

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[SearchResult]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        results = [
            SearchResult(
                document=document,
                score=self._cosine_similarity(
                    query_embedding,
                    embedding,
                ),
            )
            for document, embedding in self._entries
        ]

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[:limit]

    @staticmethod
    def _cosine_similarity(
        left: list[float],
        right: list[float],
    ) -> float:
        if len(left) != len(right):
            raise ValueError("embedding dimensions must match")

        dot_product = sum(a * b for a, b in zip(left, right))

        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return dot_product / (left_norm * right_norm)
