from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.app import create_app
from tests.helpers.lifespan import empty_lifespan


def test_openapi_should_describe_application() -> None:
    app = create_app(
        lifespan=empty_lifespan,
    )

    with TestClient(app) as client:
        response = client.get(
            "/openapi.json",
        )

    assert response.status_code == 200

    schema = response.json()

    assert schema["info"]["title"] == ("Frank AI Agent API")
    assert schema["info"]["version"] == "1.2.0"


def test_openapi_should_include_health_and_session_routes() -> None:
    app = create_app(
        lifespan=empty_lifespan,
    )

    with TestClient(app) as client:
        response = client.get(
            "/openapi.json",
        )

    assert response.status_code == 200

    schema = response.json()
    paths = schema["paths"]

    assert "/health" in paths
    assert "/api/v1/sessions" in paths
    assert "/api/v1/sessions/{session_id}/chat" in paths
    assert "/api/v1/sessions/{session_id}" in paths
    assert "/api/v1/sessions/{session_id}/history" in paths

    history_path = paths["/api/v1/sessions/{session_id}/history"]

    assert "get" in history_path
    assert "delete" in history_path


def test_health_should_return_ok() -> None:
    app = create_app(
        lifespan=empty_lifespan,
    )

    with TestClient(app) as client:
        response = client.get(
            "/health",
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Frank AI Agent",
        "version": "1.2.0",
    }


def test_create_app_should_use_injected_lifespan() -> None:
    state = {
        "started": False,
        "stopped": False,
    }

    @asynccontextmanager
    async def test_lifespan(
        app: FastAPI,
    ) -> AsyncGenerator[None]:
        del app

        state["started"] = True

        try:
            yield
        finally:
            state["stopped"] = True

    app = create_app(
        lifespan=test_lifespan,
    )

    assert state == {
        "started": False,
        "stopped": False,
    }

    with TestClient(app):
        assert state == {
            "started": True,
            "stopped": False,
        }

    assert state == {
        "started": True,
        "stopped": True,
    }


def test_cors_should_allow_configured_origin(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173",
    )

    app = create_app(
        lifespan=empty_lifespan,
    )

    with TestClient(app) as client:
        response = client.options(
            "/api/v1/sessions",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ("http://localhost:5173")


def test_cors_should_not_allow_unconfigured_origin(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173",
    )

    app = create_app(
        lifespan=empty_lifespan,
    )

    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={
                "Origin": "https://untrusted.example.com",
            },
        )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
