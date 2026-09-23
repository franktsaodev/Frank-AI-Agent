import pytest

from app.config_loaders.redis_config_loader import (
    RedisConfigLoader,
)


def test_load_should_use_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "REDIS_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "REDIS_SESSION_KEY_PREFIX",
        raising=False,
    )

    config = RedisConfigLoader().load()

    assert config.url == "redis://localhost:6379/0"
    assert config.session_key_prefix == "frank-ai-agent:sessions"


def test_load_should_use_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "REDIS_URL",
        "redis://redis:6379/1",
    )
    monkeypatch.setenv(
        "REDIS_SESSION_KEY_PREFIX",
        "test:sessions",
    )

    config = RedisConfigLoader().load()

    assert config.url == "redis://redis:6379/1"
    assert config.session_key_prefix == "test:sessions"
