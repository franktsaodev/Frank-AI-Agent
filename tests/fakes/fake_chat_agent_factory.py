from app.agent.chat_agent import ChatAgent
from app.agent.chat_agent_state import ChatAgentState


class FakeChatAgentFactory:
    def __init__(
        self,
        agents: list[ChatAgent],
    ) -> None:
        self._agents = list(agents)
        self.call_count = 0
        self.received_states: list[ChatAgentState | None] = []

    def create(
        self,
        *,
        state: ChatAgentState | None = None,
    ) -> ChatAgent:
        self.call_count += 1
        self.received_states.append(state)

        if not self._agents:
            raise RuntimeError("No fake ChatAgent available.")

        return self._agents.pop(0)
