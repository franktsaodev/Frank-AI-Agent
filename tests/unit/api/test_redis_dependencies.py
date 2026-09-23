from unittest.mock import MagicMock, patch

from redis import Redis

from app.api.redis_dependencies import get_redis_client
from app.config_models.redis_config import RedisConfig


@patch(
    "app.api.redis_dependencies.RedisClientFactory",
)
@patch(
    "app.api.redis_dependencies.RedisConfigLoader",
)
def test_get_redis_client_should_create_and_cache_client(
    mock_loader_class: MagicMock,
    mock_factory_class: MagicMock,
) -> None:
    config = RedisConfig(
        url="redis://redis:6379/0",
        session_key_prefix="frank-ai-agent:sessions",
    )
    expected_client = MagicMock(
        spec=Redis,
    )

    mock_loader_class.return_value.load.return_value = config
    mock_factory_class.return_value.create.return_value = expected_client

    get_redis_client.cache_clear()

    try:
        first_result = get_redis_client()
        second_result = get_redis_client()
    finally:
        get_redis_client.cache_clear()

    assert first_result is expected_client
    assert second_result is expected_client

    mock_loader_class.return_value.load.assert_called_once_with()
    mock_factory_class.return_value.create.assert_called_once_with(
        config,
    )
