from dataclasses import replace

from app.agent.chat_agent_factory_protocol import (
    ChatAgentFactoryProtocol,
)
from app.config_models.session_config import SessionConfig
from app.session.agent_session import AgentSession
from app.session.session_clock_protocol import (
    SessionClockProtocol,
)
from app.session.session_factory import SessionFactory
from app.session.session_id import SessionId
from app.session.session_not_found_error import (
    SessionNotFoundError,
)
from app.session.session_repository_protocol import (
    SessionRepositoryProtocol,
)
from app.session.stored_session import StoredSession


class PersistentSessionManager:
    def __init__(
        self,
        session_factory: SessionFactory,
        agent_factory: ChatAgentFactoryProtocol,
        repository: SessionRepositoryProtocol,
        clock: SessionClockProtocol,
        config: SessionConfig,
    ) -> None:
        self._session_factory = session_factory
        self._agent_factory = agent_factory
        self._repository = repository
        self._clock = clock
        self._config = config

    def create(
        self,
    ) -> AgentSession:
        session_id = self._session_factory.create()
        now = self._clock.now()
        agent = self._agent_factory.create()

        session = AgentSession(
            session_id=session_id,
            agent=agent,
            created_at=now,
            last_activity_at=now,
        )

        self._repository.save(
            StoredSession(
                session_id=session.session_id,
                created_at=session.created_at,
                last_activity_at=session.last_activity_at,
                agent_state=agent.export_state(),
            ),
            ttl_seconds=self._config.ttl_seconds,
        )

        return session

    def get(
        self,
        session_id: SessionId,
    ) -> AgentSession:
        stored_session = self._repository.get(
            session_id,
        )

        if stored_session is None:
            raise SessionNotFoundError(
                session_id=session_id,
            )

        active_stored_session = replace(
            stored_session,
            last_activity_at=self._clock.now(),
        )
        agent = self._agent_factory.create(
            state=active_stored_session.agent_state,
        )

        self._repository.save(
            active_stored_session,
            ttl_seconds=self._config.ttl_seconds,
        )

        return AgentSession(
            session_id=active_stored_session.session_id,
            agent=agent,
            created_at=active_stored_session.created_at,
            last_activity_at=active_stored_session.last_activity_at,
        )

    def save(
        self,
        session: AgentSession,
    ) -> None:
        self._repository.save(
            StoredSession(
                session_id=session.session_id,
                created_at=session.created_at,
                last_activity_at=self._clock.now(),
                agent_state=session.agent.export_state(),
            ),
            ttl_seconds=self._config.ttl_seconds,
        )

    def contains(
        self,
        session_id: SessionId,
    ) -> bool:
        return self._repository.exists(
            session_id,
        )

    def delete(
        self,
        session_id: SessionId,
    ) -> None:
        deleted = self._repository.delete(
            session_id,
        )

        if not deleted:
            raise SessionNotFoundError(
                session_id=session_id,
            )

    def purge_expired(
        self,
    ) -> int:
        return 0
