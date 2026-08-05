from fastapi.testclient import TestClient

from app.api.app import create_app


def test_openapi_should_describe_application() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/openapi.json",
        )

    assert response.status_code == 200

    schema = response.json()

    assert schema["info"]["title"] == ("Frank AI Agent API")
    assert schema["info"]["version"] == "0.1.0"


def test_openapi_should_include_health_and_chat_routes() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/openapi.json",
        )

    schema = response.json()

    assert "/health" in schema["paths"]
    assert "/api/v1/chat" in schema["paths"]


def test_health_should_return_ok() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/health",
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Frank AI Agent",
        "version": "0.1.0",
    }
