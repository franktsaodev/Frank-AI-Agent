from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.agent.chat_agent import ChatAgent
from app.config_models.session_config import SessionConfig
from app.session.in_memory_session_manager import (
    InMemorySessionManager,
)
from app.session.session_expired_error import (
    SessionExpiredError,
)
from app.session.session_factory import SessionFactory
from app.session.session_id import SessionId
from app.session.session_not_found_error import (
    SessionNotFoundError,
)
from tests.fakes.fake_chat_agent_factory import (
    FakeChatAgentFactory,
)
from tests.fakes.fake_session_clock import (
    FakeSessionClock,
)


def test_create_should_store_new_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=session_clock,
        config=session_config,
    )

    session = manager.create()

    assert manager.contains(session.session_id)
    assert session.agent is agent


def test_get_should_return_created_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=session_clock,
        config=session_config,
    )

    created_session = manager.create()

    result = manager.get(
        created_session.session_id,
    )

    assert result is not created_session
    assert result.session_id == created_session.session_id
    assert result.agent is created_session.agent
    assert result.created_at == created_session.created_at


def test_create_should_use_different_agent_for_each_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    first_agent = MagicMock(
        spec=ChatAgent,
    )
    second_agent = MagicMock(
        spec=ChatAgent,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                first_agent,
                second_agent,
            ],
        ),
        clock=session_clock,
        config=session_config,
    )

    first_session = manager.create()
    second_session = manager.create()

    assert first_session.agent is first_agent
    assert second_session.agent is second_agent
    assert first_session.agent is not second_session.agent


def test_contains_should_return_false_for_unknown_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[],
        ),
        clock=session_clock,
        config=session_config,
    )

    assert (
        manager.contains(
            SessionId(
                value="unknown-session",
            )
        )
        is False
    )


def test_get_should_reject_unknown_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[],
        ),
        clock=session_clock,
        config=session_config,
    )

    session_id = SessionId(
        value="unknown-session",
    )

    with pytest.raises(
        SessionNotFoundError,
        match="Session not found: unknown-session",
    ) as exception_info:
        manager.get(
            session_id,
        )

    assert exception_info.value.session_id is session_id


def test_delete_should_remove_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=session_clock,
        config=session_config,
    )

    session = manager.create()

    manager.delete(
        session.session_id,
    )

    assert manager.contains(session.session_id) is False


def test_delete_should_reject_unknown_session(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[],
        ),
        clock=session_clock,
        config=session_config,
    )

    with pytest.raises(
        SessionNotFoundError,
        match="Session not found: unknown-session",
    ):
        manager.delete(
            SessionId(
                value="unknown-session",
            )
        )


def test_create_should_store_session_timestamps(
    session_timestamp: datetime,
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=session_clock,
        config=session_config,
    )

    session = manager.create()

    assert session.created_at == session_timestamp
    assert session.last_activity_at == session_timestamp


def test_get_should_update_last_activity_time(
    session_config: SessionConfig,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    created_at = datetime(
        2026,
        8,
        6,
        3,
        0,
        tzinfo=UTC,
    )

    later_time = datetime(
        2026,
        8,
        6,
        3,
        30,
        tzinfo=UTC,
    )

    clock = FakeSessionClock(
        current_time=created_at,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=clock,
        config=session_config,
    )

    created_session = manager.create()

    clock.set(
        later_time,
    )

    active_session = manager.get(
        created_session.session_id,
    )

    assert active_session.created_at == created_at
    assert active_session.last_activity_at == later_time
    assert active_session.agent is agent
    assert active_session is not created_session


def test_get_should_return_session_before_expiration(
    session_timestamp: datetime,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    clock = FakeSessionClock(
        current_time=session_timestamp,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=clock,
        config=SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
    )

    session = manager.create()

    clock.set(
        session_timestamp
        + timedelta(
            seconds=3599,
        )
    )

    result = manager.get(
        session.session_id,
    )

    assert result.agent is agent


def test_get_should_reject_expired_session(
    session_timestamp: datetime,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    clock = FakeSessionClock(
        current_time=session_timestamp,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=clock,
        config=SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
    )

    session = manager.create()

    clock.set(
        session_timestamp
        + timedelta(
            seconds=3600,
        )
    )

    with pytest.raises(
        SessionExpiredError,
        match=f"Session expired: {session.session_id.value}",
    ):
        manager.get(
            session.session_id,
        )

    assert (
        manager.contains(
            session.session_id,
        )
        is False
    )


def test_get_should_extend_session_lifetime_after_activity(
    session_timestamp: datetime,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    clock = FakeSessionClock(
        current_time=session_timestamp,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=clock,
        config=SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
    )

    session = manager.create()

    first_activity_time = session_timestamp + timedelta(
        seconds=1800,
    )

    clock.set(
        first_activity_time,
    )

    manager.get(
        session.session_id,
    )

    clock.set(
        session_timestamp
        + timedelta(
            seconds=4000,
        )
    )

    result = manager.get(
        session.session_id,
    )

    assert result.agent is agent


def test_purge_expired_should_return_zero_when_no_session_is_expired(
    session_clock: FakeSessionClock,
    session_config: SessionConfig,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=session_clock,
        config=session_config,
    )

    session = manager.create()

    result = manager.purge_expired()

    assert result == 0
    assert manager.contains(
        session.session_id,
    )


def test_purge_expired_should_remove_expired_session(
    session_timestamp: datetime,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    clock = FakeSessionClock(
        current_time=session_timestamp,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=clock,
        config=SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
    )

    session = manager.create()

    clock.set(
        session_timestamp
        + timedelta(
            seconds=3600,
        )
    )

    result = manager.purge_expired()

    assert result == 1
    assert (
        manager.contains(
            session.session_id,
        )
        is False
    )


def test_purge_expired_should_keep_active_sessions(
    session_timestamp: datetime,
) -> None:
    first_agent = MagicMock(
        spec=ChatAgent,
    )
    second_agent = MagicMock(
        spec=ChatAgent,
    )

    clock = FakeSessionClock(
        current_time=session_timestamp,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                first_agent,
                second_agent,
            ],
        ),
        clock=clock,
        config=SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
    )

    expired_session = manager.create()

    clock.set(
        session_timestamp
        + timedelta(
            seconds=1800,
        )
    )

    active_session = manager.create()

    clock.set(
        session_timestamp
        + timedelta(
            seconds=3600,
        )
    )

    result = manager.purge_expired()

    assert result == 1

    assert (
        manager.contains(
            expired_session.session_id,
        )
        is False
    )

    assert (
        manager.contains(
            active_session.session_id,
        )
        is True
    )


def test_purge_expired_should_keep_recently_active_session(
    session_timestamp: datetime,
) -> None:
    agent = MagicMock(
        spec=ChatAgent,
    )

    clock = FakeSessionClock(
        current_time=session_timestamp,
    )

    manager = InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=FakeChatAgentFactory(
            agents=[
                agent,
            ],
        ),
        clock=clock,
        config=SessionConfig(
            ttl_seconds=3600,
            cleanup_interval_seconds=300,
        ),
    )

    session = manager.create()

    clock.set(
        session_timestamp
        + timedelta(
            seconds=1800,
        )
    )

    manager.get(
        session.session_id,
    )

    clock.set(
        session_timestamp
        + timedelta(
            seconds=4000,
        )
    )

    result = manager.purge_expired()

    assert result == 0
    assert manager.contains(
        session.session_id,
    )
