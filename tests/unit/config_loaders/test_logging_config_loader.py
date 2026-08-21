import pytest

from app.config_loaders.environment_reader import EnvironmentReader
from app.config_loaders.logging_config_loader import LoggingConfigLoader
from app.config_models.logging_config import LoggingConfig


def test_should_reject_unsupported_log_level() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported logging level",
    ):
        LoggingConfig(
            level="VERBOSE",
        )


def test_load_should_read_log_level_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "LOG_LEVEL",
        "DEBUG",
    )

    config = LoggingConfigLoader(
        environment_reader=EnvironmentReader(),
    ).load()

    assert config.level == "DEBUG"
