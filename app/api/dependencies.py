from functools import lru_cache

from app.agent.chat_agent import ChatAgent
from app.bootstrap import create_chat_agent


@lru_cache(maxsize=1)
def get_chat_agent() -> ChatAgent:
    return create_chat_agent()
