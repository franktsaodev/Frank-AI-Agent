from app.config_loaders.environment_reader import EnvironmentReader
from app.config_loaders.retrieval_config_loader import RetrievalConfigLoader


def test_load_should_use_default_values(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "RETRIEVAL_ENABLED",
        raising=False,
    )
    monkeypatch.delenv(
        "RETRIEVAL_KNOWLEDGE_FILE_PATH",
        raising=False,
    )
    monkeypatch.delenv(
        "RETRIEVAL_CHUNK_SIZE",
        raising=False,
    )
    monkeypatch.delenv(
        "RETRIEVAL_CHUNK_OVERLAP",
        raising=False,
    )
    monkeypatch.delenv(
        "RETRIEVAL_TOP_K",
        raising=False,
    )
    monkeypatch.delenv(
        "RETRIEVAL_EMBEDDING_MODEL",
        raising=False,
    )

    loader = RetrievalConfigLoader(
        environment_reader=EnvironmentReader(),
    )

    config = loader.load()

    assert config.enabled is False
    assert config.knowledge_path == "knowledge/knowledge.txt"
    assert config.chunk_size == 500
    assert config.chunk_overlap == 50
    assert config.top_k == 5
    assert config.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"


def test_load_should_read_environment_values(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "RETRIEVAL_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "RETRIEVAL_KNOWLEDGE_FILE_PATH",
        "docs/knowledge.txt",
    )
    monkeypatch.setenv(
        "RETRIEVAL_CHUNK_SIZE",
        "800",
    )
    monkeypatch.setenv(
        "RETRIEVAL_CHUNK_OVERLAP",
        "100",
    )
    monkeypatch.setenv(
        "RETRIEVAL_TOP_K",
        "3",
    )
    monkeypatch.setenv(
        "RETRIEVAL_EMBEDDING_MODEL",
        "custom-model",
    )

    loader = RetrievalConfigLoader(
        environment_reader=EnvironmentReader(),
    )

    config = loader.load()

    assert config.enabled is True
    assert config.knowledge_path == "docs/knowledge.txt"
    assert config.chunk_size == 800
    assert config.chunk_overlap == 100
    assert config.top_k == 3
    assert config.embedding_model == "custom-model"
