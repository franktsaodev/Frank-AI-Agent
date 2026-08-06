from dataclasses import dataclass
from datetime import datetime

from app.agent.chat_agent import ChatAgent
from app.session.session_id import SessionId


@dataclass(frozen=True)
class AgentSession:
    session_id: SessionId
    agent: ChatAgent
    created_at: datetime
    last_activity_at: datetime
