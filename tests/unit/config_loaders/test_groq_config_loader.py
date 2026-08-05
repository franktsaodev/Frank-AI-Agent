import pytest

from app.config_loaders.groq_config_loader import (
    GroqConfigLoader,
)


def test_load_should_return_groq_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GROQ_API_KEY",
        "test-api-key",
    )
    monkeypatch.setenv(
        "GROQ_MODEL",
        "test-model",
    )

    config = GroqConfigLoader().load()

    assert config.api_key == "test-api-key"
    assert config.model == "test-model"


def test_load_should_reject_missing_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "GROQ_API_KEY",
        raising=False,
    )
    monkeypatch.setenv(
        "GROQ_MODEL",
        "test-model",
    )

    with pytest.raises(
        RuntimeError,
        match=("Required environment variable is missing: GROQ_API_KEY"),
    ):
        GroqConfigLoader().load()


def test_load_should_reject_missing_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GROQ_API_KEY",
        "test-api-key",
    )
    monkeypatch.delenv(
        "GROQ_MODEL",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match=("Required environment variable is missing: GROQ_MODEL"),
    ):
        GroqConfigLoader().load()
