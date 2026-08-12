from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbeddingProvider:
    def __init__(
        self,
        *,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self._model = SentenceTransformer(model_name)

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
        )

        return [embedding.tolist() for embedding in embeddings]
