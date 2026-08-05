from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agent.chat_agent import ChatAgent
from app.api.app import create_app
from app.api.dependencies import get_chat_agent
from app.exceptions.client_exceptions import (
    AIClientError,
    ClientAuthenticationError,
    ClientConnectionError,
    ClientTimeoutError,
)


@pytest.fixture
def mock_agent() -> MagicMock:
    return MagicMock(
        spec=ChatAgent,
    )


@pytest.fixture
def client(
    mock_agent: MagicMock,
) -> Iterator[TestClient]:
    app = create_app()

    app.dependency_overrides[get_chat_agent] = lambda: mock_agent

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_chat_should_return_gateway_timeout_when_client_times_out(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    mock_agent.chat.side_effect = ClientTimeoutError(
        "request timed out",
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 504
    assert response.json() == {
        "error": "client_timeout",
        "message": ("The AI service took too long to respond."),
    }


def test_chat_should_return_service_unavailable_when_connection_fails(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    mock_agent.chat.side_effect = ClientConnectionError(
        "connection failed",
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "error": "client_connection_error",
        "message": ("Unable to connect to the AI service."),
    }


def test_chat_should_return_bad_gateway_when_authentication_fails(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    mock_agent.chat.side_effect = ClientAuthenticationError(
        "invalid credentials",
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": "client_authentication_error",
        "message": ("The AI service authentication failed."),
    }


def test_chat_should_return_bad_gateway_for_ai_client_error(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    mock_agent.chat.side_effect = AIClientError(
        "upstream failure",
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": "ai_client_error",
        "message": ("The AI service returned an error."),
    }
