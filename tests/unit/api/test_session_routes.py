from collections.abc import Iterator
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agent.chat_agent import ChatAgent
from app.api.app import create_app
from app.api.session_dependencies import (
    get_session_manager,
)
from app.models.message import Message
from app.models.message_role import MessageRole
from app.session.agent_session import AgentSession
from app.session.session_id import SessionId
from tests.fakes.fake_session_manager import (
    FakeSessionManager,
)
from tests.helpers.lifespan import empty_lifespan


@pytest.fixture
def mock_agent() -> MagicMock:
    agent = MagicMock(
        spec=ChatAgent,
    )

    agent.chat.return_value = "Hello Frank!"

    return agent


@pytest.fixture
def session(
    mock_agent: MagicMock,
    session_timestamp: datetime,
) -> AgentSession:
    return AgentSession(
        session_id=SessionId(
            value="session-123",
        ),
        agent=mock_agent,
        created_at=session_timestamp,
        last_activity_at=session_timestamp,
    )


@pytest.fixture
def fake_session_manager(
    session: AgentSession,
) -> FakeSessionManager:
    return FakeSessionManager(
        sessions=[
            session,
        ],
    )


@pytest.fixture
def client(
    fake_session_manager: FakeSessionManager,
) -> Iterator[TestClient]:
    app = create_app(
        lifespan=empty_lifespan,
    )

    app.dependency_overrides[get_session_manager] = lambda: fake_session_manager

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_create_session_should_return_session_id(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/sessions",
    )

    assert response.status_code == 201
    assert response.json() == {
        "session_id": "session-123",
    }


def test_chat_with_session_should_use_session_agent(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    response = client.post(
        "/api/v1/sessions/session-123/chat",
        json={
            "message": "Hello",
            "metadata": {
                "request_id": "request-123",
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "Hello Frank!",
    }

    mock_agent.chat.assert_called_once_with(
        "Hello",
        metadata={
            "request_id": "request-123",
            "source": "api",
            "session_id": "session-123",
        },
    )


def test_chat_with_session_should_return_not_found_for_unknown_session(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    response = client.post(
        "/api/v1/sessions/unknown-session/chat",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "session_not_found",
        "message": "Session not found.",
    }

    mock_agent.chat.assert_not_called()


def test_delete_session_should_remove_session(
    client: TestClient,
    fake_session_manager: FakeSessionManager,
) -> None:
    response = client.delete(
        "/api/v1/sessions/session-123",
    )

    assert response.status_code == 200
    assert response.json() == {
        "deleted": True,
    }

    assert (
        fake_session_manager.contains(
            SessionId(
                value="session-123",
            )
        )
        is False
    )


def test_delete_session_should_return_not_found_for_unknown_session(
    client: TestClient,
) -> None:
    response = client.delete(
        "/api/v1/sessions/unknown-session",
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "session_not_found",
        "message": "Session not found.",
    }


def test_chat_with_session_should_pass_metadata_to_agent(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    response = client.post(
        "/api/v1/sessions/session-123/chat",
        json={
            "message": "Hello",
            "metadata": {
                "request_id": "request-123",
                "user_id": "frank",
            },
        },
    )

    assert response.status_code == 200

    mock_agent.chat.assert_called_once_with(
        "Hello",
        metadata={
            "request_id": "request-123",
            "user_id": "frank",
            "source": "api",
            "session_id": "session-123",
        },
    )


def test_chat_with_session_should_override_protected_metadata(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    response = client.post(
        "/api/v1/sessions/session-123/chat",
        json={
            "message": "Hello",
            "metadata": {
                "source": "fake-source",
                "session_id": "fake-session",
            },
        },
    )

    assert response.status_code == 200

    mock_agent.chat.assert_called_once_with(
        "Hello",
        metadata={
            "source": "api",
            "session_id": "session-123",
        },
    )


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
def test_chat_with_session_should_reject_blank_message(
    client: TestClient,
    mock_agent: MagicMock,
    message: str,
) -> None:
    response = client.post(
        "/api/v1/sessions/session-123/chat",
        json={
            "message": message,
        },
    )

    assert response.status_code == 422
    mock_agent.chat.assert_not_called()


def test_get_session_history_should_return_agent_history(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    mock_agent.get_history.return_value = (
        Message(
            role=MessageRole.USER,
            content="Hello",
        ),
        Message(
            role=MessageRole.ASSISTANT,
            content="Hi Frank!",
        ),
    )

    response = client.get(
        "/api/v1/sessions/session-123/history",
    )

    assert response.status_code == 200
    assert response.json() == {
        "session_id": "session-123",
        "messages": [
            {
                "role": "user",
                "content": "Hello",
            },
            {
                "role": "assistant",
                "content": "Hi Frank!",
            },
        ],
    }

    mock_agent.get_history.assert_called_once_with()


def test_get_session_history_should_return_empty_messages(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    mock_agent.get_history.return_value = ()

    response = client.get(
        "/api/v1/sessions/session-123/history",
    )

    assert response.status_code == 200
    assert response.json() == {
        "session_id": "session-123",
        "messages": [],
    }


def test_clear_session_history_should_clear_agent_history(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    response = client.delete(
        "/api/v1/sessions/session-123/history",
    )

    assert response.status_code == 200
    assert response.json() == {
        "cleared": True,
    }

    mock_agent.clear_history.assert_called_once_with()


def test_get_session_history_should_return_not_found_for_unknown_session(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/sessions/unknown-session/history",
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "session_not_found",
        "message": "Session not found.",
    }


def test_clear_session_history_should_return_not_found_for_unknown_session(
    client: TestClient,
) -> None:
    response = client.delete(
        "/api/v1/sessions/unknown-session/history",
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "session_not_found",
        "message": "Session not found.",
    }


def test_get_session_detail_should_return_session_information(
    client: TestClient,
    mock_agent: MagicMock,
    session_timestamp: datetime,
) -> None:
    mock_agent.get_history.return_value = (
        Message(
            role=MessageRole.USER,
            content="Hello",
        ),
        Message(
            role=MessageRole.ASSISTANT,
            content="Hi!",
        ),
    )

    response = client.get(
        "/api/v1/sessions/session-123",
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["session_id"] == "session-123"
    assert response_data["message_count"] == 2

    assert (
        datetime.fromisoformat(
            response_data["created_at"].replace(
                "Z",
                "+00:00",
            )
        )
        == session_timestamp
    )

    assert (
        datetime.fromisoformat(
            response_data["last_activity_at"].replace(
                "Z",
                "+00:00",
            )
        )
        == session_timestamp
    )

    mock_agent.get_history.assert_called_once_with()


def test_get_session_detail_should_return_not_found_for_unknown_session(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/sessions/unknown-session",
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "session_not_found",
        "message": "Session not found.",
    }
