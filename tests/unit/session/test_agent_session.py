from datetime import datetime
from unittest.mock import MagicMock

from app.agent.chat_agent import ChatAgent
from app.session.agent_session import AgentSession
from app.session.session_id import SessionId


def test_should_store_session_information(
    session_timestamp: datetime,
) -> None:
    session_id = SessionId(
        value="session-123",
    )

    agent = MagicMock(
        spec=ChatAgent,
    )

    session = AgentSession(
        session_id=session_id,
        agent=agent,
        created_at=session_timestamp,
        last_activity_at=session_timestamp,
    )

    assert session.session_id is session_id
    assert session.agent is agent
    assert session.created_at == session_timestamp
    assert session.last_activity_at == session_timestamp
