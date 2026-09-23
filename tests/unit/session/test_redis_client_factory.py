from unittest.mock import MagicMock, patch

from redis import Redis
from redis.maint_notifications import MaintNotificationsConfig

from app.config_models.redis_config import RedisConfig
from app.session.redis_client_factory import RedisClientFactory


@patch(
    "app.session.redis_client_factory.Redis.from_url",
)
def test_create_should_configure_redis_client(
    mock_from_url: MagicMock,
) -> None:
    expected_client = MagicMock(
        spec=Redis,
    )
    mock_from_url.return_value = expected_client

    config = RedisConfig(
        url="redis://redis:6379/0",
        session_key_prefix="frank-ai-agent:sessions",
    )

    result = RedisClientFactory().create(
        config,
    )

    assert result is expected_client
    mock_from_url.assert_called_once()

    call_args = mock_from_url.call_args

    assert call_args.args == ("redis://redis:6379/0",)
    assert call_args.kwargs["decode_responses"] is True

    maintenance_config = call_args.kwargs["maint_notifications_config"]

    assert isinstance(
        maintenance_config,
        MaintNotificationsConfig,
    )
    assert maintenance_config.enabled is False
