import pytest

from app.config_loaders.memory_policy_config_loader import (
    MemoryPolicyConfigLoader,
)


def test_load_should_use_default_allowed_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "MEMORY_ALLOWED_KEYS",
        raising=False,
    )

    config = MemoryPolicyConfigLoader().load()

    assert config.allowed_keys == frozenset(
        {
            "user_name",
            "favorite_music",
            "occupation",
        }
    )


def test_load_should_parse_allowed_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MEMORY_ALLOWED_KEYS",
        "user_name,location,language",
    )

    config = MemoryPolicyConfigLoader().load()

    assert config.allowed_keys == frozenset(
        {
            "user_name",
            "location",
            "language",
        }
    )


def test_load_should_ignore_surrounding_whitespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MEMORY_ALLOWED_KEYS",
        " user_name , location , language ",
    )

    config = MemoryPolicyConfigLoader().load()

    assert config.allowed_keys == frozenset(
        {
            "user_name",
            "location",
            "language",
        }
    )


def test_load_should_ignore_empty_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MEMORY_ALLOWED_KEYS",
        "user_name,,location,",
    )

    config = MemoryPolicyConfigLoader().load()

    assert config.allowed_keys == frozenset(
        {
            "user_name",
            "location",
        }
    )


def test_load_should_remove_duplicate_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MEMORY_ALLOWED_KEYS",
        "user_name,user_name,location",
    )

    config = MemoryPolicyConfigLoader().load()

    assert config.allowed_keys == frozenset(
        {
            "user_name",
            "location",
        }
    )
