from pathlib import Path

import pytest

from app.config_models.tracing_config import TracingConfig


def test_should_enable_logging_by_default() -> None:
    config = TracingConfig()

    assert config.enable_logging is True
    assert config.json_file_path is None


def test_should_store_json_file_path() -> None:
    file_path = Path("logs/traces.jsonl")

    config = TracingConfig(
        json_file_path=file_path,
    )

    assert config.enable_logging is True
    assert config.json_file_path == file_path


def test_should_allow_json_export_without_logging() -> None:
    file_path = Path("logs/traces.jsonl")

    config = TracingConfig(
        enable_logging=False,
        json_file_path=file_path,
    )

    assert config.enable_logging is False
    assert config.json_file_path == file_path


def test_should_reject_when_all_exporters_are_disabled() -> None:
    with pytest.raises(
        ValueError,
        match="At least one trace exporter must be enabled",
    ):
        TracingConfig(
            enable_logging=False,
            json_file_path=None,
        )
