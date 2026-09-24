from unittest.mock import MagicMock, patch

from redis import Redis

from app.api.redis_dependencies import (
    get_redis_client,
    get_session_repository,
)
from app.config_models.redis_config import RedisConfig
from app.session.stored_session_codec import StoredSessionCodec


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


@patch(
    "app.api.redis_dependencies.RedisSessionRepository",
)
@patch(
    "app.api.redis_dependencies.StoredSessionCodec",
)
@patch(
    "app.api.redis_dependencies.RedisConfigLoader",
)
@patch(
    "app.api.redis_dependencies.get_redis_client",
)
def test_get_session_repository_should_create_and_cache_repository(
    mock_get_redis_client: MagicMock,
    mock_loader_class: MagicMock,
    mock_codec_class: MagicMock,
    mock_repository_class: MagicMock,
) -> None:
    config = RedisConfig(
        url="redis://redis:6379/0",
        session_key_prefix="frank-ai-agent:sessions",
    )
    redis_client = MagicMock(
        spec=Redis,
    )
    codec = MagicMock(
        spec=StoredSessionCodec,
    )
    expected_repository = MagicMock()

    mock_loader_class.return_value.load.return_value = config
    mock_get_redis_client.return_value = redis_client
    mock_codec_class.return_value = codec
    mock_repository_class.return_value = expected_repository

    get_session_repository.cache_clear()

    try:
        first_result = get_session_repository()
        second_result = get_session_repository()
    finally:
        get_session_repository.cache_clear()

    assert first_result is expected_repository
    assert second_result is expected_repository

    mock_loader_class.return_value.load.assert_called_once_with()
    mock_get_redis_client.assert_called_once_with()
    mock_codec_class.assert_called_once_with()
    mock_repository_class.assert_called_once_with(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )
