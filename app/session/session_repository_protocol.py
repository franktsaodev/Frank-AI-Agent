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
