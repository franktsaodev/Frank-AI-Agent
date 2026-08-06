from app.api.lifespan import create_lifespan
from app.api.lifespan_types import Lifespan
from app.api.session_dependencies import (
    get_session_manager,
)
from app.config_loaders.session_config_loader import (
    SessionConfigLoader,
)
from app.config_models.session_config import SessionConfig


def get_session_config() -> SessionConfig:
    return SessionConfigLoader().load()


application_lifespan: Lifespan = create_lifespan(
    get_session_manager=get_session_manager,
    get_session_config=get_session_config,
)
