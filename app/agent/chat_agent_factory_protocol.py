from typing import Protocol

from app.agent.chat_agent import ChatAgent
from app.agent.chat_agent_state import ChatAgentState


class ChatAgentFactoryProtocol(Protocol):
    def create(
        self,
        *,
        state: ChatAgentState | None = None,
    ) -> ChatAgent: ...
