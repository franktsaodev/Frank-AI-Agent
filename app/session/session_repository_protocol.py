from datetime import datetime
from typing import Protocol

from app.session.session_id import SessionId
from app.session.stored_session import StoredSession


class SessionRepositoryProtocol(Protocol):
    def save(
        self,
        session: StoredSession,
        *,
        ttl_seconds: int,
    ) -> None: ...

    def save_if_revision(
        self,
        session: StoredSession,
        *,
        expected_revision: int,
        ttl_seconds: int,
    ) -> None: ...

    def get(
        self,
        session_id: SessionId,
    ) -> StoredSession | None: ...

    def exists(
        self,
        session_id: SessionId,
    ) -> bool: ...

    def delete(
        self,
        session_id: SessionId,
    ) -> bool: ...

    def get_and_refresh(
        self,
        session_id: SessionId,
        *,
        last_activity_at: datetime,
        ttl_seconds: int,
    ) -> StoredSession | None: ...
