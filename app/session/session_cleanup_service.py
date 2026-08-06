import asyncio
import logging

from app.session.session_manager_protocol import (
    SessionManagerProtocol,
)

logger = logging.getLogger(__name__)


class SessionCleanupService:
    def __init__(
        self,
        *,
        session_manager: SessionManagerProtocol,
        interval_seconds: int,
    ) -> None:
        if interval_seconds < 1:
            raise ValueError("interval_seconds must be at least 1.")

        self._session_manager = session_manager
        self._interval_seconds = interval_seconds

    def run_once(
        self,
    ) -> int:
        purged_count = self._session_manager.purge_expired()

        if purged_count > 0:
            logger.info(
                "Purged %d expired session(s)",
                purged_count,
            )

        return purged_count

    async def run(
        self,
    ) -> None:
        try:
            while True:
                await asyncio.sleep(
                    self._interval_seconds,
                )

                self.run_once()
        except asyncio.CancelledError:
            logger.info("Session cleanup service stopped")

            raise
