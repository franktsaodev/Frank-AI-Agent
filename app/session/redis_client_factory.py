from redis import Redis
from redis.maint_notifications import MaintNotificationsConfig

from app.config_models.redis_config import RedisConfig


class RedisClientFactory:
    def create(
        self,
        config: RedisConfig,
    ) -> Redis:
        return Redis.from_url(
            config.url,
            decode_responses=True,
            maint_notifications_config=(
                MaintNotificationsConfig(
                    enabled=False,
                )
            ),
        )
