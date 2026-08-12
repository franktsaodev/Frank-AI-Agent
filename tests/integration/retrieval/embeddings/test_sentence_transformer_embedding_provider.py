from app.retrieval.embeddings.sentence_transformer_embedding_provider import (
    SentenceTransformerEmbeddingProvider,
)


def test_should_generate_embeddings() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    embeddings = provider.embed(
        [
            "Hello world",
            "Frank AI Agent",
        ]
    )

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384


def test_should_return_empty_embeddings_for_empty_input() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    assert provider.embed([]) == []
