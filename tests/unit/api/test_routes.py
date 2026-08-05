from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agent.chat_agent import ChatAgent
from app.api.app import create_app
from app.api.dependencies import get_chat_agent
from app.api.runtime import RuntimeInfo
from app.api.runtime_provider import get_runtime_info


@pytest.fixture
def mock_agent() -> MagicMock:
    agent = MagicMock(
        spec=ChatAgent,
    )

    agent.chat.return_value = "Hello Frank!"

    return agent


@pytest.fixture
def client(
    mock_agent: MagicMock,
) -> Iterator[TestClient]:
    app = create_app()

    app.dependency_overrides[get_chat_agent] = lambda: mock_agent

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health_should_return_ok(
    client: TestClient,
) -> None:
    response = client.get(
        "/health",
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Frank AI Agent",
        "version": "0.1.0",
    }


def test_chat_should_return_agent_response(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "Hello Frank!",
    }

    mock_agent.chat.assert_called_once_with(
        "Hello",
        metadata={
            "source": "api",
        },
    )


def test_chat_should_pass_request_metadata_to_agent(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    response = client.post(
        "/api/v1/chat",
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
        },
    )


def test_chat_should_override_metadata_source(
    client: TestClient,
    mock_agent: MagicMock,
) -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
            "metadata": {
                "source": "fake-source",
            },
        },
    )

    assert response.status_code == 200

    mock_agent.chat.assert_called_once_with(
        "Hello",
        metadata={
            "source": "api",
        },
    )


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
def test_chat_should_reject_blank_message(
    client: TestClient,
    mock_agent: MagicMock,
    message: str,
) -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "message": message,
        },
    )

    assert response.status_code == 422
    mock_agent.chat.assert_not_called()


def test_health_should_use_runtime_dependency() -> None:
    app = create_app()

    app.dependency_overrides[get_runtime_info] = lambda: RuntimeInfo(
        service_name="Test Agent",
        version="9.9.9",
    )

    with TestClient(app) as client:
        response = client.get(
            "/health",
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Test Agent",
        "version": "9.9.9",
    }
