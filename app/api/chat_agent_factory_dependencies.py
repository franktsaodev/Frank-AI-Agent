from functools import lru_cache

from app.agent.chat_agent_factory import ChatAgentFactory
from app.bootstrap import create_chat_agent_factory


@lru_cache(maxsize=1)
def get_chat_agent_factory() -> ChatAgentFactory:
    return create_chat_agent_factory()
