from app.session.agent_session import AgentSession
from app.session.session_id import SessionId
from app.session.session_not_found_error import (
    SessionNotFoundError,
)


class FakeSessionManager:
    def __init__(
        self,
        sessions: list[AgentSession] | None = None,
    ) -> None:
        self._sessions = {session.session_id: session for session in (sessions or [])}

        self.created_sessions: list[AgentSession] = []
        self.deleted_session_ids: list[SessionId] = []

    def create(
        self,
    ) -> AgentSession:
        if not self._sessions:
            raise RuntimeError("No fake session is available.")

        session = next(iter(self._sessions.values()))

        self.created_sessions.append(
            session,
        )

        return session

    def get(
        self,
        session_id: SessionId,
    ) -> AgentSession:
        try:
            return self._sessions[session_id]
        except KeyError as error:
            raise SessionNotFoundError(
                session_id=session_id,
            ) from error

    def contains(
        self,
        session_id: SessionId,
    ) -> bool:
        return session_id in self._sessions

    def delete(
        self,
        session_id: SessionId,
    ) -> None:
        try:
            del self._sessions[session_id]
        except KeyError as error:
            raise SessionNotFoundError(
                session_id=session_id,
            ) from error

        self.deleted_session_ids.append(
            session_id,
        )

    def purge_expired(
        self,
    ) -> int:
        return 0
