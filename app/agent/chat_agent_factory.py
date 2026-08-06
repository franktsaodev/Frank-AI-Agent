from app.agent.chat_agent import ChatAgent
from app.agent.chat_agent_dependencies import (
    ChatAgentDependencies,
)
from app.memory.in_memory_fact_memory import (
    InMemoryFactMemory,
)
from app.memory.sliding_window_memory import (
    SlidingWindowMemory,
)


class ChatAgentFactory:
    def __init__(
        self,
        dependencies: ChatAgentDependencies,
    ) -> None:
        self._dependencies = dependencies

    def create(
        self,
    ) -> ChatAgent:
        return ChatAgent(
            prompt_template=self._dependencies.prompt_template,
            agent_runner=self._dependencies.agent_runner,
            memory=SlidingWindowMemory(
                config=self._dependencies.memory_config,
            ),
            fact_memory=InMemoryFactMemory(),
            fact_extractor=self._dependencies.fact_extractor,
            memory_policy=self._dependencies.memory_policy,
            prompt_composer=self._dependencies.prompt_composer,
        )
