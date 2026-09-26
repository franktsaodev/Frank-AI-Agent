from collections.abc import Iterator
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.agent.chat_agent import ChatAgent
from app.api.app import create_app
from app.api.session_dependencies import (
    get_session_manager,
)
from app.exceptions.client_exceptions import (
    AIClientError,
    ClientAuthenticationError,
    ClientConnectionError,
    ClientRateLimitError,
    ClientTimeoutError,
)
from app.models.chat_stream_event import (
    ChatContentDelta,
    ChatStreamCompleted,
    ChatStreamEvent,
)
from app.models.message import Message
from app.models.message_role import MessageRole
from app.session.agent_session import AgentSession
from app.session.session_conflict_error import SessionConflictError
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
    fake_session_manager: FakeSessionManager,
    session: AgentSession,
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

    assert fake_session_manager.saved_sessions == [
        session,
    ]


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
    fake_session_manager: FakeSessionManager,
    session: AgentSession,
) -> None:
    response = client.delete(
        "/api/v1/sessions/session-123/history",
    )

    assert response.status_code == 200
    assert response.json() == {
        "cleared": True,
    }

    mock_agent.clear_history.assert_called_once_with()

    assert fake_session_manager.saved_sessions == [
        session,
    ]


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


def test_stream_chat_with_session_should_return_sse_events(
    client: TestClient,
    mock_agent: MagicMock,
    fake_session_manager: FakeSessionManager,
    session: AgentSession,
) -> None:
    mock_agent.stream_chat.return_value = iter(
        [
            ChatContentDelta(
                content="Hello Frank!",
            ),
            ChatStreamCompleted(
                response="Hello Frank!",
            ),
        ]
    )

    response = client.post(
        "/api/v1/sessions/session-123/chat/stream",
        json={
            "message": "Hello",
            "metadata": {
                "request_id": "request-123",
                "source": "untrusted",
                "session_id": "untrusted-session",
            },
        },
    )

    assert response.status_code == 200

    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"

    assert response.text == (
        "event: content_delta\n"
        'data: {"content":"Hello Frank!"}\n\n'
        "event: completed\n"
        'data: {"response":"Hello Frank!"}\n\n'
    )

    mock_agent.stream_chat.assert_called_once_with(
        "Hello",
        metadata={
            "request_id": "request-123",
            "source": "api",
            "session_id": "session-123",
        },
    )

    assert fake_session_manager.saved_sessions == [
        session,
    ]


def test_stream_chat_should_emit_error_when_session_save_fails(
    client: TestClient,
    mock_agent: MagicMock,
    fake_session_manager: FakeSessionManager,
    session: AgentSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_agent.stream_chat.return_value = iter(
        [
            ChatContentDelta(
                content="Hello Frank!",
            ),
            ChatStreamCompleted(
                response="Hello Frank!",
            ),
        ]
    )

    save = MagicMock(
        side_effect=RuntimeError(
            "Redis unavailable",
        ),
    )
    monkeypatch.setattr(
        fake_session_manager,
        "save",
        save,
    )

    response = client.post(
        "/api/v1/sessions/session-123/chat/stream",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 200
    assert response.text == (
        "event: content_delta\n"
        'data: {"content":"Hello Frank!"}\n\n'
        "event: error\n"
        'data: {"error":"stream_error",'
        '"message":"The chat stream failed unexpectedly."}\n\n'
    )

    assert "event: completed\n" not in response.text

    save.assert_called_once_with(
        session,
    )


def test_stream_chat_should_emit_conflict_when_session_save_fails(
    client: TestClient,
    mock_agent: MagicMock,
    fake_session_manager: FakeSessionManager,
) -> None:
    mock_agent.stream_chat.return_value = iter(
        [
            ChatContentDelta(content="Hello Frank!"),
            ChatStreamCompleted(response="Hello Frank!"),
        ]
    )

    with patch.object(
        fake_session_manager,
        "save",
        side_effect=SessionConflictError(
            session_id=SessionId(value="session-123"),
        ),
    ):
        response = client.post(
            "/api/v1/sessions/session-123/chat/stream",
            json={"message": "Hello"},
        )

    assert response.status_code == 200
    assert response.text == (
        "event: content_delta\n"
        'data: {"content":"Hello Frank!"}\n\n'
        "event: error\n"
        'data: {"error":"session_conflict",'
        '"message":"Session was updated by another request. Please retry."}\n\n'
    )
    assert "event: completed" not in response.text


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
def test_stream_chat_with_session_should_reject_blank_message(
    client: TestClient,
    mock_agent: MagicMock,
    message: str,
) -> None:
    response = client.post(
        "/api/v1/sessions/session-123/chat/stream",
        json={
            "message": message,
        },
    )

    assert response.status_code == 422
    mock_agent.stream_chat.assert_not_called()


def test_stream_chat_with_session_should_return_not_found_for_unknown_session(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    response = client.post(
        "/api/v1/sessions/unknown-session/chat/stream",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "session_not_found",
        "message": "Session not found.",
    }

    mock_agent.stream_chat.assert_not_called()


def test_stream_chat_with_session_should_hide_unexpected_error(
    client: TestClient,
    mock_agent: MagicMock,
    fake_session_manager: FakeSessionManager,
) -> None:
    def failing_stream() -> Iterator[ChatStreamEvent]:
        yield from ()

        raise RuntimeError(
            "Sensitive internal implementation detail",
        )

    mock_agent.stream_chat.return_value = failing_stream()

    response = client.post(
        "/api/v1/sessions/session-123/chat/stream",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    assert response.text == (
        "event: error\n"
        'data: {"error":"stream_error",'
        '"message":"The chat stream failed unexpectedly."}\n\n'
    )

    assert "Sensitive internal implementation detail" not in response.text

    assert fake_session_manager.saved_sessions == []


@pytest.mark.parametrize(
    (
        "error",
        "expected_error",
        "expected_message",
    ),
    [
        (
            ClientAuthenticationError(
                "invalid credentials",
            ),
            "client_authentication_error",
            "The AI service authentication failed.",
        ),
        (
            ClientTimeoutError(
                "request timed out",
            ),
            "client_timeout",
            "The AI service took too long to respond.",
        ),
        (
            ClientConnectionError(
                "connection failed",
            ),
            "client_connection_error",
            "Unable to connect to the AI service.",
        ),
        (
            ClientRateLimitError(
                "AI service rate limit exceeded",
            ),
            "client_rate_limit",
            ("The AI service is temporarily rate limited. Please try again later."),
        ),
        (
            AIClientError(
                "upstream failure",
            ),
            "ai_client_error",
            "The AI service returned an error.",
        ),
    ],
)
def test_stream_chat_with_session_should_emit_client_error_event(
    client: TestClient,
    mock_agent: MagicMock,
    fake_session_manager: FakeSessionManager,
    error: Exception,
    expected_error: str,
    expected_message: str,
) -> None:
    def failing_stream() -> Iterator[ChatStreamEvent]:
        yield from ()

        raise error

    mock_agent.stream_chat.return_value = failing_stream()

    response = client.post(
        "/api/v1/sessions/session-123/chat/stream",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    assert response.text == (
        "event: error\n"
        f'data: {{"error":"{expected_error}",'
        f'"message":"{expected_message}"}}\n\n'
    )

    assert fake_session_manager.saved_sessions == []
