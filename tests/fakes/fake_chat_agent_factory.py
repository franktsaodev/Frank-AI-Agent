from app.agent.chat_agent import ChatAgent


class FakeChatAgentFactory:
    def __init__(
        self,
        agents: list[ChatAgent],
    ) -> None:
        self._agents = list(agents)
        self.call_count = 0

    def create(
        self,
    ) -> ChatAgent:
        self.call_count += 1

        if not self._agents:
            raise RuntimeError("No fake ChatAgent available.")

        return self._agents.pop(0)
