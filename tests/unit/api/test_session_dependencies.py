from unittest.mock import MagicMock, patch

from app.api.session_dependencies import get_session_manager
from app.config_models.session_config import SessionConfig
from app.session.persistent_session_manager import (
    PersistentSessionManager,
)
from app.session.session_repository_protocol import (
    SessionRepositoryProtocol,
)


@patch(
    "app.api.session_dependencies.PersistentSessionManager",
)
@patch(
    "app.api.session_dependencies.SessionFactory",
)
@patch(
    "app.api.session_dependencies.create_chat_agent_factory",
)
@patch(
    "app.api.session_dependencies.get_session_repository",
)
@patch(
    "app.api.session_dependencies.SystemSessionClock",
)
@patch(
    "app.api.session_dependencies.SessionConfigLoader",
)
def test_get_session_manager_should_create_and_cache_persistent_manager(
    mock_config_loader_class: MagicMock,
    mock_clock_class: MagicMock,
    mock_get_session_repository: MagicMock,
    mock_create_agent_factory: MagicMock,
    mock_session_factory_class: MagicMock,
    mock_manager_class: MagicMock,
) -> None:
    config = SessionConfig(
        ttl_seconds=3600,
        cleanup_interval_seconds=300,
    )
    session_factory = MagicMock()
    agent_factory = MagicMock()
    repository = MagicMock(
        spec=SessionRepositoryProtocol,
    )
    clock = MagicMock()
    expected_manager = MagicMock(
        spec=PersistentSessionManager,
    )

    mock_config_loader_class.return_value.load.return_value = config
    mock_session_factory_class.return_value = session_factory
    mock_create_agent_factory.return_value = agent_factory
    mock_get_session_repository.return_value = repository
    mock_clock_class.return_value = clock
    mock_manager_class.return_value = expected_manager

    get_session_manager.cache_clear()

    try:
        first_result = get_session_manager()
        second_result = get_session_manager()
    finally:
        get_session_manager.cache_clear()

    assert first_result is expected_manager
    assert second_result is expected_manager

    mock_session_factory_class.assert_called_once_with()
    mock_create_agent_factory.assert_called_once_with()
    mock_get_session_repository.assert_called_once_with()
    mock_clock_class.assert_called_once_with()
    mock_config_loader_class.return_value.load.assert_called_once_with()

    mock_manager_class.assert_called_once_with(
        session_factory=session_factory,
        agent_factory=agent_factory,
        repository=repository,
        clock=clock,
        config=config,
    )
