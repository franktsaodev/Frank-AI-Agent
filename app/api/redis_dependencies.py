from functools import lru_cache

from redis import Redis

from app.config_loaders.redis_config_loader import (
    RedisConfigLoader,
)
from app.session.redis_client_factory import RedisClientFactory
from app.session.redis_session_repository import (
    RedisSessionRepository,
)
from app.session.session_repository_protocol import (
    SessionRepositoryProtocol,
)
from app.session.stored_session_codec import StoredSessionCodec


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    config = RedisConfigLoader().load()

    return RedisClientFactory().create(
        config,
    )


@lru_cache(maxsize=1)
def get_session_repository() -> SessionRepositoryProtocol:
    config = RedisConfigLoader().load()

    return RedisSessionRepository(
        redis_client=get_redis_client(),
        codec=StoredSessionCodec(),
        key_prefix=config.session_key_prefix,
    )
