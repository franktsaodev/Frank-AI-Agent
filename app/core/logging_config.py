import logging

from app.config_models.logging_config import LoggingConfig


def configure_logging(
    config: LoggingConfig,
) -> None:
    log_level = getattr(
        logging,
        config.level.upper(),
    )

    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
    )

    logging.getLogger().setLevel(
        log_level,
    )

    logging.getLogger("groq").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("filelock").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
