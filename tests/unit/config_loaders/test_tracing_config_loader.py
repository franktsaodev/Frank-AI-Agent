from pathlib import Path

import pytest

from app.config_loaders.tracing_config_loader import (
    TracingConfigLoader,
)


def test_load_should_use_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "TRACE_LOGGING_ENABLED",
        raising=False,
    )
    monkeypatch.delenv(
        "TRACE_JSON_FILE_PATH",
        raising=False,
    )

    config = TracingConfigLoader().load()

    assert config.enable_logging is True
    assert config.json_file_path == Path(
        "logs/traces.jsonl",
    )


def test_load_should_parse_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TRACE_LOGGING_ENABLED",
        "false",
    )
    monkeypatch.setenv(
        "TRACE_JSON_FILE_PATH",
        "custom/traces.jsonl",
    )

    config = TracingConfigLoader().load()

    assert config.enable_logging is False
    assert config.json_file_path == Path(
        "custom/traces.jsonl",
    )


def test_load_should_use_defaults_for_blank_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TRACE_LOGGING_ENABLED",
        "   ",
    )
    monkeypatch.setenv(
        "TRACE_JSON_FILE_PATH",
        "   ",
    )

    config = TracingConfigLoader().load()

    assert config.enable_logging is True
    assert config.json_file_path == Path(
        "logs/traces.jsonl",
    )


def test_load_should_reject_invalid_logging_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TRACE_LOGGING_ENABLED",
        "sometimes",
    )

    with pytest.raises(
        RuntimeError,
        match=("Environment variable TRACE_LOGGING_ENABLED must be a boolean"),
    ):
        TracingConfigLoader().load()
