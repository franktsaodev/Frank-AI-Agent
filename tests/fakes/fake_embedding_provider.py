class FakeEmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0] for text in texts]


def test_fake_embedding_provider_should_return_one_vector_per_text() -> None:
    provider = FakeEmbeddingProvider()

    vectors = provider.embed(
        [
            "hello",
            "world",
        ]
    )

    assert len(vectors) == 2
