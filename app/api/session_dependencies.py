from functools import lru_cache

from app.api.redis_dependencies import (
    get_session_repository,
)
from app.bootstrap import create_chat_agent_factory
from app.config_loaders.session_config_loader import (
    SessionConfigLoader,
)
from app.session.persistent_session_manager import (
    PersistentSessionManager,
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
    return PersistentSessionManager(
        session_factory=SessionFactory(),
        agent_factory=create_chat_agent_factory(),
        repository=get_session_repository(),
        clock=SystemSessionClock(),
        config=SessionConfigLoader().load(),
    )
