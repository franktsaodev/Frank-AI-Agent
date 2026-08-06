import pytest

from app.config_loaders.session_config_loader import (
    SessionConfigLoader,
)


def test_load_should_use_default_ttl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "SESSION_TTL_SECONDS",
        raising=False,
    )

    config = SessionConfigLoader().load()

    assert config.ttl_seconds == 3600


def test_load_should_parse_ttl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "SESSION_TTL_SECONDS",
        "1800",
    )

    config = SessionConfigLoader().load()

    assert config.ttl_seconds == 1800
