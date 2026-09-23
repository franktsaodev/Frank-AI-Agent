from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from redis import Redis
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
)

from app.api.lifespan import create_lifespan
from app.config_models.session_config import SessionConfig
from app.session.session_manager_protocol import (
    SessionManagerProtocol,
)


@pytest.mark.asyncio
async def test_lifespan_should_start_and_stop_runtime_resources() -> None:
    manager = MagicMock(
        spec=SessionManagerProtocol,
    )
    redis_client = MagicMock(
        spec=Redis,
    )

    lifespan = create_lifespan(
        get_session_manager=lambda: manager,
        get_session_config=lambda: SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
        get_redis_client=lambda: redis_client,
    )

    app = FastAPI()

    async with lifespan(app):
        redis_client.ping.assert_called_once_with()
        redis_client.close.assert_not_called()

    redis_client.close.assert_called_once_with()


@pytest.mark.asyncio
async def test_lifespan_should_close_redis_client_when_ping_fails() -> None:
    manager = MagicMock(
        spec=SessionManagerProtocol,
    )
    redis_client = MagicMock(
        spec=Redis,
    )
    redis_client.ping.side_effect = RedisConnectionError(
        "Redis unavailable",
    )

    lifespan = create_lifespan(
        get_session_manager=lambda: manager,
        get_session_config=lambda: SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
        get_redis_client=lambda: redis_client,
    )

    app = FastAPI()

    with pytest.raises(
        RedisConnectionError,
        match="Redis unavailable",
    ):
        async with lifespan(app):
            pass

    redis_client.ping.assert_called_once_with()
    redis_client.close.assert_called_once_with()
