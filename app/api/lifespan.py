import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
) -> Lifespan:
    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ) -> AsyncGenerator[None]:
        del app

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

    return lifespan
