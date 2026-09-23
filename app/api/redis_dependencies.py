from functools import lru_cache

from redis import Redis

from app.config_loaders.redis_config_loader import (
    RedisConfigLoader,
)
from app.session.redis_client_factory import RedisClientFactory


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    config = RedisConfigLoader().load()

    return RedisClientFactory().create(
        config,
    )
