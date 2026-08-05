import pytest

from app.config_loaders.retry_config_loader import (
    RetryConfigLoader,
)


def test_load_should_use_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "GROQ_RETRY_MAX_ATTEMPTS",
        raising=False,
    )
    monkeypatch.delenv(
        "GROQ_RETRY_INITIAL_DELAY_SECONDS",
        raising=False,
    )
    monkeypatch.delenv(
        "GROQ_RETRY_BACKOFF_MULTIPLIER",
        raising=False,
    )

    config = RetryConfigLoader().load()

    assert config.max_attempts == 3
    assert config.initial_delay_seconds == 1.0
    assert config.backoff_multiplier == 2.0


def test_load_should_parse_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GROQ_RETRY_MAX_ATTEMPTS",
        "5",
    )
    monkeypatch.setenv(
        "GROQ_RETRY_INITIAL_DELAY_SECONDS",
        "0.5",
    )
    monkeypatch.setenv(
        "GROQ_RETRY_BACKOFF_MULTIPLIER",
        "3.0",
    )

    config = RetryConfigLoader().load()

    assert config.max_attempts == 5
    assert config.initial_delay_seconds == 0.5
    assert config.backoff_multiplier == 3.0


def test_load_should_reject_non_integer_max_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GROQ_RETRY_MAX_ATTEMPTS",
        "invalid",
    )

    with pytest.raises(
        RuntimeError,
        match=("Environment variable GROQ_RETRY_MAX_ATTEMPTS must be an integer"),
    ):
        RetryConfigLoader().load()


def test_load_should_reject_non_numeric_delay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GROQ_RETRY_INITIAL_DELAY_SECONDS",
        "invalid",
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "Environment variable GROQ_RETRY_INITIAL_DELAY_SECONDS must be a number"
        ),
    ):
        RetryConfigLoader().load()


def test_load_should_reject_invalid_max_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GROQ_RETRY_MAX_ATTEMPTS",
        "0",
    )

    with pytest.raises(
        ValueError,
        match="max_attempts",
    ):
        RetryConfigLoader().load()
