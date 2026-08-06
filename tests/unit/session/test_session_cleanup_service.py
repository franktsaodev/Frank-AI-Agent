import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.session.session_cleanup_service import (
    SessionCleanupService,
)
from app.session.session_manager_protocol import (
    SessionManagerProtocol,
)


@pytest.mark.asyncio
async def test_run_should_purge_expired_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = MagicMock(
        spec=SessionManagerProtocol,
    )

    manager.purge_expired.return_value = 2

    sleep_mock = AsyncMock(
        side_effect=[
            None,
            asyncio.CancelledError(),
        ]
    )

    monkeypatch.setattr(
        asyncio,
        "sleep",
        sleep_mock,
    )

    service = SessionCleanupService(
        session_manager=manager,
        interval_seconds=300,
    )

    with pytest.raises(
        asyncio.CancelledError,
    ):
        await service.run()

    manager.purge_expired.assert_called_once_with()


def test_run_once_should_purge_expired_sessions() -> None:
    manager = MagicMock(
        spec=SessionManagerProtocol,
    )

    manager.purge_expired.return_value = 2

    service = SessionCleanupService(
        session_manager=manager,
        interval_seconds=300,
    )

    result = service.run_once()

    assert result == 2
    manager.purge_expired.assert_called_once_with()


def test_should_reject_invalid_interval() -> None:
    manager = MagicMock(
        spec=SessionManagerProtocol,
    )

    with pytest.raises(
        ValueError,
        match="interval_seconds must be at least 1",
    ):
        SessionCleanupService(
            session_manager=manager,
            interval_seconds=0,
        )
