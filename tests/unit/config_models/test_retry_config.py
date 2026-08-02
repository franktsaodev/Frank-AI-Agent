import pytest

from app.config_models.retry_config import RetryConfig


def test_should_store_retry_settings() -> None:
    config = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=1.0,
        backoff_multiplier=2.0,
    )

    assert config.max_attempts == 3
    assert config.initial_delay_seconds == 1.0
    assert config.backoff_multiplier == 2.0


def test_should_reject_max_attempts_less_than_one() -> None:
    with pytest.raises(
        ValueError,
        match="max_attempts must be at least 1",
    ):
        RetryConfig(
            max_attempts=0,
            initial_delay_seconds=1.0,
            backoff_multiplier=2.0,
        )


def test_should_reject_negative_initial_delay() -> None:
    with pytest.raises(
        ValueError,
        match="initial_delay_seconds cannot be negative",
    ):
        RetryConfig(
            max_attempts=3,
            initial_delay_seconds=-1.0,
            backoff_multiplier=2.0,
        )


def test_should_reject_backoff_multiplier_less_than_one() -> None:
    with pytest.raises(
        ValueError,
        match="backoff_multiplier must be at least 1",
    ):
        RetryConfig(
            max_attempts=3,
            initial_delay_seconds=1.0,
            backoff_multiplier=0.5,
        )
