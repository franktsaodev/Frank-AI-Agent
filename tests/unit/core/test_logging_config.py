import logging

from app.config_models.logging_config import LoggingConfig
from app.core.logging_config import configure_logging


def test_configure_logging_should_apply_configured_log_level() -> None:
    config = LoggingConfig(
        level="INFO",
    )

    configure_logging(
        config=config,
    )

    assert logging.getLogger().level == logging.INFO


def test_configure_logging_should_suppress_noisy_third_party_loggers() -> None:
    config = LoggingConfig(
        level="DEBUG",
    )

    configure_logging(
        config=config,
    )

    assert logging.getLogger("groq").level == logging.WARNING
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
    assert logging.getLogger("filelock").level == logging.WARNING
    assert logging.getLogger("huggingface_hub").level == logging.WARNING
    assert logging.getLogger("sentence_transformers").level == logging.WARNING
    assert logging.getLogger("transformers").level == logging.WARNING
