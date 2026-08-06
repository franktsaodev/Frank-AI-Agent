from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI

from app.api.lifespan import create_lifespan
from app.config_models.session_config import SessionConfig
from app.session.session_manager_protocol import (
    SessionManagerProtocol,
)


@pytest.mark.asyncio
async def test_lifespan_should_start_and_stop_cleanup_task() -> None:
    manager = MagicMock(
        spec=SessionManagerProtocol,
    )

    lifespan = create_lifespan(
        get_session_manager=lambda: manager,
        get_session_config=lambda: SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
    )

    app = FastAPI()

    async with lifespan(app):
        pass
