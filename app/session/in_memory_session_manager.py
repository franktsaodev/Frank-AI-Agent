from dataclasses import replace
from datetime import timedelta

from app.agent.chat_agent_factory_protocol import (
    ChatAgentFactoryProtocol,
)
from app.config_models.session_config import SessionConfig
from app.session.agent_session import AgentSession
from app.session.session_clock_protocol import (
    SessionClockProtocol,
)
from app.session.session_expired_error import (
    SessionExpiredError,
)
from app.session.session_factory import SessionFactory
from app.session.session_id import SessionId
from app.session.session_not_found_error import (
    SessionNotFoundError,
)


class InMemorySessionManager:
    def __init__(
        self,
        session_factory: SessionFactory,
        agent_factory: ChatAgentFactoryProtocol,
        clock: SessionClockProtocol,
        config: SessionConfig,
    ) -> None:
        self._session_factory = session_factory
        self._agent_factory = agent_factory
        self._clock = clock
        self._config = config
        self._sessions: dict[
            SessionId,
            AgentSession,
        ] = {}

    def create(
        self,
    ) -> AgentSession:
        session_id = self._session_factory.create()
        now = self._clock.now()

        session = AgentSession(
            session_id=session_id,
            agent=self._agent_factory.create(),
            created_at=now,
            last_activity_at=now,
        )

        self._sessions[session_id] = session

        return session

    def get(
        self,
        session_id: SessionId,
    ) -> AgentSession:
        try:
            session = self._sessions[session_id]
        except KeyError as error:
            raise SessionNotFoundError(
                session_id=session_id,
            ) from error

        if self._is_expired(
            session,
        ):
            del self._sessions[session_id]

            raise SessionExpiredError(
                session_id=session_id,
            )

        active_session = replace(
            session,
            last_activity_at=self._clock.now(),
        )

        self._sessions[session_id] = active_session

        return active_session

    def contains(
        self,
        session_id: SessionId,
    ) -> bool:
        session = self._sessions.get(
            session_id,
        )

        if session is None:
            return False

        if self._is_expired(
            session,
        ):
            del self._sessions[session_id]

            return False

        return True

    def delete(
        self,
        session_id: SessionId,
    ) -> None:
        try:
            session = self._sessions[session_id]
        except KeyError as error:
            raise SessionNotFoundError(
                session_id=session_id,
            ) from error

        if self._is_expired(
            session,
        ):
            del self._sessions[session_id]

            raise SessionExpiredError(
                session_id=session_id,
            )

        del self._sessions[session_id]

    def _is_expired(
        self,
        session: AgentSession,
    ) -> bool:
        expires_at = session.last_activity_at + timedelta(
            seconds=self._config.ttl_seconds,
        )

        return self._clock.now() >= expires_at

    def purge_expired(
        self,
    ) -> int:
        expired_session_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if self._is_expired(session)
        ]

        for session_id in expired_session_ids:
            del self._sessions[session_id]

        return len(
            expired_session_ids,
        )
