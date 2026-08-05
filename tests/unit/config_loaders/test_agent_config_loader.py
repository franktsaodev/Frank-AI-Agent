import pytest

from app.config_loaders.agent_config_loader import (
    AgentConfigLoader,
)


def test_load_should_use_default_max_iterations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "AGENT_MAX_ITERATIONS",
        raising=False,
    )

    config = AgentConfigLoader().load()

    assert config.max_iterations == 10


def test_load_should_parse_max_iterations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AGENT_MAX_ITERATIONS",
        "5",
    )

    config = AgentConfigLoader().load()

    assert config.max_iterations == 5


def test_load_should_use_default_for_blank_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AGENT_MAX_ITERATIONS",
        "   ",
    )

    config = AgentConfigLoader().load()

    assert config.max_iterations == 10


def test_load_should_reject_non_integer_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AGENT_MAX_ITERATIONS",
        "invalid",
    )

    with pytest.raises(
        RuntimeError,
        match=("Environment variable AGENT_MAX_ITERATIONS must be an integer"),
    ):
        AgentConfigLoader().load()


def test_load_should_reject_value_less_than_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AGENT_MAX_ITERATIONS",
        "0",
    )

    with pytest.raises(
        ValueError,
        match="max_iterations",
    ):
        AgentConfigLoader().load()
