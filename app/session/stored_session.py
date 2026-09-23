from dataclasses import dataclass, field
from datetime import datetime

from app.agent.chat_agent_state import ChatAgentState
from app.session.session_id import SessionId

STORED_SESSION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StoredSession:
    session_id: SessionId
    created_at: datetime
    last_activity_at: datetime
    agent_state: ChatAgentState
    schema_version: int = field(
        default=STORED_SESSION_SCHEMA_VERSION,
        init=False,
    )
