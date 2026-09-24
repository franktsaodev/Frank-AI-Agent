from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.agent.chat_agent import ChatAgent
from app.agent.chat_agent_factory_protocol import (
    ChatAgentFactoryProtocol,
)
from app.agent.chat_agent_state import ChatAgentState
from app.config_models.session_config import SessionConfig
from app.session.agent_session import AgentSession
from app.session.persistent_session_manager import (
    PersistentSessionManager,
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
from tests.fakes.fake_chat_agent_factory import (
    FakeChatAgentFactory,
)
from tests.fakes.fake_session_clock import FakeSessionClock


def test_create_should_persist_new_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )
    agent_state = ChatAgentState(
        messages=(),
        facts={},
    )
    agent.export_state.return_value = agent_state

    repository = MagicMock(
        spec=SessionRepositoryProtocol,
    )

    manager = PersistentSessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        repository=repository,
        clock=session_clock,
        config=session_config,
    )

    session = manager.create()

    assert session.agent is agent
    assert session.created_at == session_clock.now()
    assert session.last_activity_at == session_clock.now()

    repository.save.assert_called_once_with(
        StoredSession(
            session_id=session.session_id,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
            agent_state=agent_state,
        ),
        ttl_seconds=session_config.ttl_seconds,
    )


def test_get_should_restore_session_and_refresh_ttl(
    session_timestamp: datetime,
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    agent_state = ChatAgentState(
        messages=(),
        facts={
            "user_name": "Frank",
        },
    )
    stored_session = StoredSession(
        session_id=SessionId(
            value="session-123",
        ),
        created_at=session_timestamp
        - timedelta(
            minutes=30,
        ),
        last_activity_at=session_timestamp
        - timedelta(
            minutes=10,
        ),
        agent_state=agent_state,
    )

    restored_agent = MagicMock(
        spec=ChatAgent,
    )
    agent_factory = MagicMock(
        spec=ChatAgentFactoryProtocol,
    )
    agent_factory.create.return_value = restored_agent

    repository = MagicMock(
        spec=SessionRepositoryProtocol,
    )
    repository.get.return_value = stored_session

    manager = PersistentSessionManager(
        session_factory=SessionFactory(),
        agent_factory=agent_factory,
        repository=repository,
        clock=session_clock,
        config=session_config,
    )

    result = manager.get(
        stored_session.session_id,
    )

    repository.get.assert_called_once_with(
        stored_session.session_id,
    )
    agent_factory.create.assert_called_once_with(
        state=agent_state,
    )

    assert result.session_id == stored_session.session_id
    assert result.agent is restored_agent
    assert result.created_at == stored_session.created_at
    assert result.last_activity_at == session_timestamp

    repository.save.assert_called_once_with(
        StoredSession(
            session_id=stored_session.session_id,
            created_at=stored_session.created_at,
            last_activity_at=session_timestamp,
            agent_state=agent_state,
        ),
        ttl_seconds=session_config.ttl_seconds,
    )


def test_get_should_reject_missing_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    session_id = SessionId(
        value="missing-session",
    )

    agent_factory = MagicMock(
        spec=ChatAgentFactoryProtocol,
    )
    repository = MagicMock(
        spec=SessionRepositoryProtocol,
    )
    repository.get.return_value = None

    manager = PersistentSessionManager(
        session_factory=SessionFactory(),
        agent_factory=agent_factory,
        repository=repository,
        clock=session_clock,
        config=session_config,
    )

    with pytest.raises(
        SessionNotFoundError,
        match="Session not found: missing-session",
    ) as exception_info:
        manager.get(
            session_id,
        )

    assert exception_info.value.session_id is session_id

    repository.get.assert_called_once_with(
        session_id,
    )
    repository.save.assert_not_called()
    agent_factory.create.assert_not_called()


def test_save_should_persist_current_agent_state(
    session_timestamp: datetime,
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    agent_state = ChatAgentState(
        messages=(),
        facts={
            "user_name": "Frank",
        },
    )
    agent = MagicMock(
        spec=ChatAgent,
    )
    agent.export_state.return_value = agent_state

    session = AgentSession(
        session_id=SessionId(
            value="session-123",
        ),
        agent=agent,
        created_at=session_timestamp
        - timedelta(
            minutes=30,
        ),
        last_activity_at=session_timestamp
        - timedelta(
            minutes=10,
        ),
    )

    repository = MagicMock(
        spec=SessionRepositoryProtocol,
    )

    manager = PersistentSessionManager(
        session_factory=SessionFactory(),
        agent_factory=MagicMock(
            spec=ChatAgentFactoryProtocol,
        ),
        repository=repository,
        clock=session_clock,
        config=session_config,
    )

    manager.save(
        session,
    )

    agent.export_state.assert_called_once_with()
    repository.save.assert_called_once_with(
        StoredSession(
            session_id=session.session_id,
            created_at=session.created_at,
            last_activity_at=session_timestamp,
            agent_state=agent_state,
        ),
        ttl_seconds=session_config.ttl_seconds,
    )


@pytest.mark.parametrize(
    ("repository_result", "expected_result"),
    [
        (False, False),
        (True, True),
    ],
)
def test_contains_should_delegate_to_repository(
    repository_result: bool,
    expected_result: bool,
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    session_id = SessionId(
        value="session-123",
    )

    repository = MagicMock(
        spec=SessionRepositoryProtocol,
    )
    repository.exists.return_value = repository_result

    manager = PersistentSessionManager(
        session_factory=SessionFactory(),
        agent_factory=MagicMock(
            spec=ChatAgentFactoryProtocol,
        ),
        repository=repository,
        clock=session_clock,
        config=session_config,
    )

    result = manager.contains(
        session_id,
    )

    assert result is expected_result
    repository.exists.assert_called_once_with(
        session_id,
    )


def test_delete_should_remove_stored_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    session_id = SessionId(
        value="session-123",
    )

    repository = MagicMock(
        spec=SessionRepositoryProtocol,
    )
    repository.delete.return_value = True

    manager = PersistentSessionManager(
        session_factory=SessionFactory(),
        agent_factory=MagicMock(
            spec=ChatAgentFactoryProtocol,
        ),
        repository=repository,
        clock=session_clock,
        config=session_config,
    )

    manager.delete(
        session_id,
    )

    repository.delete.assert_called_once_with(
        session_id,
    )


def test_delete_should_reject_missing_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    session_id = SessionId(
        value="missing-session",
    )

    repository = MagicMock(
        spec=SessionRepositoryProtocol,
    )
    repository.delete.return_value = False

    manager = PersistentSessionManager(
        session_factory=SessionFactory(),
        agent_factory=MagicMock(
            spec=ChatAgentFactoryProtocol,
        ),
        repository=repository,
        clock=session_clock,
        config=session_config,
    )

    with pytest.raises(
        SessionNotFoundError,
        match="Session not found: missing-session",
    ) as exception_info:
        manager.delete(
            session_id,
        )

    assert exception_info.value.session_id is session_id
    repository.delete.assert_called_once_with(
        session_id,
    )


def test_purge_expired_should_be_repository_no_op(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    repository = MagicMock(
        spec=SessionRepositoryProtocol,
    )

    manager = PersistentSessionManager(
        session_factory=SessionFactory(),
        agent_factory=MagicMock(
            spec=ChatAgentFactoryProtocol,
        ),
        repository=repository,
        clock=session_clock,
        config=session_config,
    )

    result = manager.purge_expired()

    assert result == 0
    assert repository.mock_calls == []
