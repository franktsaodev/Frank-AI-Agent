from functools import lru_cache

from app.bootstrap import create_chat_agent_factory
from app.config_loaders.session_config_loader import (
    SessionConfigLoader,
)
from app.session.in_memory_session_manager import (
    InMemorySessionManager,
)
from app.session.session_factory import SessionFactory
from app.session.session_manager_protocol import (
    SessionManagerProtocol,
)
from app.session.system_session_clock import (
    SystemSessionClock,
)


@lru_cache(maxsize=1)
def get_session_manager() -> SessionManagerProtocol:
    return InMemorySessionManager(
        session_factory=SessionFactory(),
        agent_factory=create_chat_agent_factory(),
        clock=SystemSessionClock(),
        config=SessionConfigLoader().load(),
    )
