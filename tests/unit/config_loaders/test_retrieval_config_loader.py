from app.config_loaders.environment_reader import EnvironmentReader
from app.config_loaders.retrieval_config_loader import RetrievalConfigLoader


def test_load_should_use_default_values(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "RETRIEVAL_TRIGGER_KEYWORDS",
        raising=False,
    )
    monkeypatch.delenv(
        "RETRIEVAL_ENABLED",
        raising=False,
    )
    monkeypatch.delenv(
        "RETRIEVAL_KNOWLEDGE_PATH",
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
        "RETRIEVAL_MIN_SCORE",
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
    assert config.knowledge_path == "knowledge"
    assert config.chunk_size == 500
    assert config.chunk_overlap == 50
    assert config.top_k == 5
    assert config.min_score == 0.0
    assert config.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert config.trigger_keywords == frozenset(
        {
            "documentation",
            "manual",
            "session",
            "deployment",
            "architecture",
        }
    )


def test_load_should_read_environment_values(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "RETRIEVAL_TRIGGER_KEYWORDS",
        "docs,manual,system design",
    )
    monkeypatch.setenv(
        "RETRIEVAL_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "RETRIEVAL_KNOWLEDGE_PATH",
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
        "RETRIEVAL_MIN_SCORE",
        "0.65",
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
    assert config.min_score == 0.65
    assert config.embedding_model == "custom-model"
    assert config.trigger_keywords == frozenset(
        {
            "docs",
            "manual",
            "system design",
        }
    )


def test_load_should_trim_and_ignore_empty_trigger_keywords(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "RETRIEVAL_TRIGGER_KEYWORDS",
        " docs , manual , , architecture ",
    )

    loader = RetrievalConfigLoader(
        environment_reader=EnvironmentReader(),
    )

    config = loader.load()

    assert config.trigger_keywords == frozenset(
        {
            "docs",
            "manual",
            "architecture",
        }
    )
