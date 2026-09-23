import pytest

from app.config_models.redis_config import RedisConfig


def test_should_store_redis_configuration() -> None:
    config = RedisConfig(
        url="redis://localhost:6379/0",
        session_key_prefix="frank-ai-agent:sessions",
    )

    assert config.url == "redis://localhost:6379/0"
    assert config.session_key_prefix == "frank-ai-agent:sessions"


@pytest.mark.parametrize(
    ("url", "session_key_prefix", "expected_message"),
    [
        (
            "",
            "frank-ai-agent:sessions",
            "url cannot be empty",
        ),
        (
            "redis://localhost:6379/0",
            "",
            "session_key_prefix cannot be empty",
        ),
    ],
)
def test_should_reject_empty_configuration(
    url: str,
    session_key_prefix: str,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        RedisConfig(
            url=url,
            session_key_prefix=session_key_prefix,
        )
