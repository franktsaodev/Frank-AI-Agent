import pytest

from app.config_models.logging_config import LoggingConfig


def test_should_accept_supported_log_level() -> None:
    config = LoggingConfig(
        level="INFO",
    )

    assert config.level == "INFO"


def test_should_reject_unsupported_log_level() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported logging level",
    ):
        LoggingConfig(
            level="VERBOSE",
        )
