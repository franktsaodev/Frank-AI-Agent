from app.api.session_dependencies import (
    get_session_manager,
)
from app.config_loaders.session_config_loader import (
    SessionConfigLoader,
)
from app.config_models.session_config import SessionConfig
from app.session.session_manager_protocol import (
    SessionManagerProtocol,
)


def get_lifespan_session_manager() -> SessionManagerProtocol:
    return get_session_manager()


def get_lifespan_session_config() -> SessionConfig:
    return SessionConfigLoader().load()
