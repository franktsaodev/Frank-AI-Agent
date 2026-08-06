from typing import Protocol

from app.session.agent_session import AgentSession
from app.session.session_id import SessionId


class SessionManagerProtocol(Protocol):
    def create(
        self,
    ) -> AgentSession: ...

    def get(
        self,
        session_id: SessionId,
    ) -> AgentSession: ...

    def contains(
        self,
        session_id: SessionId,
    ) -> bool: ...

    def delete(
        self,
        session_id: SessionId,
    ) -> None: ...

    def purge_expired(
        self,
    ) -> int: ...
