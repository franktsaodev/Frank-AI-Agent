from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from app.agent.chat_agent_state import ChatAgentState
from app.session.session_id import SessionId
from app.session.stored_session import (
    STORED_SESSION_SCHEMA_VERSION,
    StoredSession,
)


def test_create_stored_session() -> None:
    created_at = datetime(
        2026,
        9,
        22,
        10,
        0,
        tzinfo=UTC,
    )
    last_activity_at = datetime(
        2026,
        9,
        22,
        10,
        30,
        tzinfo=UTC,
    )
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
        created_at=created_at,
        last_activity_at=last_activity_at,
        agent_state=agent_state,
    )

    assert stored_session.session_id == SessionId(
        value="session-123",
    )
    assert stored_session.created_at == created_at
    assert stored_session.last_activity_at == last_activity_at
    assert stored_session.agent_state == agent_state
    assert stored_session.schema_version == STORED_SESSION_SCHEMA_VERSION


def test_stored_session_is_frozen() -> None:
    stored_session = StoredSession(
        session_id=SessionId(
            value="session-123",
        ),
        created_at=datetime(
            2026,
            9,
            22,
            10,
            0,
            tzinfo=UTC,
        ),
        last_activity_at=datetime(
            2026,
            9,
            22,
            10,
            30,
            tzinfo=UTC,
        ),
        agent_state=ChatAgentState(
            messages=(),
            facts={},
        ),
    )

    with pytest.raises(FrozenInstanceError):
        stored_session.last_activity_at = (  # pyright: ignore[reportAttributeAccessIssue]
            datetime.now(
                UTC,
            )
        )
