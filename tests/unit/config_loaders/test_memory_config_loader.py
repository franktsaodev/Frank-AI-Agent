import pytest

from app.config_loaders.memory_config_loader import (
    MemoryConfigLoader,
)


def test_load_should_use_default_max_history_rounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "MEMORY_MAX_HISTORY_ROUNDS",
        raising=False,
    )

    config = MemoryConfigLoader().load()

    assert config.max_history_rounds == 2


def test_load_should_parse_max_history_rounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MEMORY_MAX_HISTORY_ROUNDS",
        "5",
    )

    config = MemoryConfigLoader().load()

    assert config.max_history_rounds == 5


def test_load_should_use_default_for_blank_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MEMORY_MAX_HISTORY_ROUNDS",
        "   ",
    )

    config = MemoryConfigLoader().load()

    assert config.max_history_rounds == 2


def test_load_should_reject_non_integer_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MEMORY_MAX_HISTORY_ROUNDS",
        "invalid",
    )

    with pytest.raises(
        RuntimeError,
        match=("Environment variable MEMORY_MAX_HISTORY_ROUNDS must be an integer"),
    ):
        MemoryConfigLoader().load()


def test_load_should_reject_value_less_than_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MEMORY_MAX_HISTORY_ROUNDS",
        "0",
    )

    with pytest.raises(
        ValueError,
        match="max_history_rounds",
    ):
        MemoryConfigLoader().load()
