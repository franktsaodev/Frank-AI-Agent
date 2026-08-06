import pytest

from app.config_models.session_config import SessionConfig


def test_should_store_session_ttl() -> None:
    config = SessionConfig(
        ttl_seconds=3600,
        cleanup_interval_seconds=300,
    )

    assert config.ttl_seconds == 3600


def test_should_reject_ttl_less_than_one() -> None:
    with pytest.raises(
        ValueError,
        match="ttl_seconds must be at least 1",
    ):
        SessionConfig(
            ttl_seconds=0,
            cleanup_interval_seconds=300,
        )
