import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis import Redis

from app.api.lifespan_types import Lifespan
from app.config_models.session_config import SessionConfig
from app.session.session_cleanup_service import (
    SessionCleanupService,
)
from app.session.session_manager_protocol import (
    SessionManagerProtocol,
)


def create_lifespan(
    *,
    get_session_manager: Callable[
        [],
        SessionManagerProtocol,
    ],
    get_session_config: Callable[
        [],
        SessionConfig,
    ],
    get_redis_client: Callable[
        [],
        Redis,
    ],
) -> Lifespan:
    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ) -> AsyncGenerator[None]:
        del app

        redis_client = get_redis_client()

        try:
            redis_client.ping()

            session_manager = get_session_manager()
            session_config = get_session_config()

            cleanup_service = SessionCleanupService(
                session_manager=session_manager,
                interval_seconds=(session_config.cleanup_interval_seconds),
            )

            cleanup_task = asyncio.create_task(
                cleanup_service.run(),
                name="session-cleanup",
            )

            try:
                yield
            finally:
                cleanup_task.cancel()

                try:
                    await cleanup_task
                except asyncio.CancelledError:
                    pass
        finally:
            redis_client.close()

    return lifespan
