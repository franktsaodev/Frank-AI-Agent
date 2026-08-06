from typing import Protocol

from app.agent.chat_agent import ChatAgent


class ChatAgentFactoryProtocol(Protocol):
    def create(
        self,
    ) -> ChatAgent: ...
