import pytest

from app.config_loaders.api_runtime_config_loader import (
    ApiRuntimeConfigLoader,
)


def test_load_should_use_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "APP_SERVICE_NAME",
        raising=False,
    )
    monkeypatch.delenv(
        "APP_VERSION",
        raising=False,
    )

    config = ApiRuntimeConfigLoader().load()

    assert config.service_name == "Frank AI Agent"
    assert config.version == "1.0.1"


def test_load_should_parse_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "APP_SERVICE_NAME",
        "Test Agent",
    )
    monkeypatch.setenv(
        "APP_VERSION",
        "9.9.9",
    )

    config = ApiRuntimeConfigLoader().load()

    assert config.service_name == "Test Agent"
    assert config.version == "9.9.9"


def test_load_should_use_defaults_for_blank_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "APP_SERVICE_NAME",
        "   ",
    )
    monkeypatch.setenv(
        "APP_VERSION",
        "   ",
    )

    config = ApiRuntimeConfigLoader().load()

    assert config.service_name == "Frank AI Agent"
    assert config.version == "1.0.1"
