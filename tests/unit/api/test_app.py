import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import patch
from uuid import UUID

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
    assert schema["info"]["version"] == "1.5.0"


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
    assert "/ready" in paths

    readiness_responses = paths["/ready"]["get"]["responses"]

    assert (
        readiness_responses["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ReadinessResponse"
    )
    assert (
        readiness_responses["503"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )
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
        "version": "1.5.0",
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


def test_responses_should_have_distinct_request_ids() -> None:
    app = create_app(
        lifespan=empty_lifespan,
    )

    with TestClient(app) as client:
        first_response = client.get("/health")
        second_response = client.get("/health")
        missing_response = client.get("/missing")

    request_ids = [
        response.headers["X-Request-ID"]
        for response in (first_response, second_response, missing_response)
    ]

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert missing_response.status_code == 404
    assert all(str(UUID(request_id)) == request_id for request_id in request_ids)
    assert len(set(request_ids)) == 3


def test_cors_should_expose_request_id_to_configured_origin(
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
                "Origin": "http://localhost:5173",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ("http://localhost:5173")
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()
    assert (
        str(UUID(response.headers["X-Request-ID"])) == response.headers["X-Request-ID"]
    )


def test_unhandled_error_should_include_request_id() -> None:
    app = create_app(
        lifespan=empty_lifespan,
    )

    @app.get("/test-unhandled-error")
    def raise_unhandled_error() -> None:
        raise RuntimeError("Sensitive internal detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-unhandled-error")

    assert response.status_code == 500
    assert "Sensitive internal detail" not in response.text

    request_id = response.headers["X-Request-ID"]
    assert str(UUID(request_id)) == request_id


def test_request_log_should_match_response_id_without_query_string(
    caplog,
) -> None:
    app = create_app(
        lifespan=empty_lifespan,
    )

    with (
        caplog.at_level(logging.INFO, logger="app.api.app"),
        TestClient(app) as client,
    ):
        response = client.get("/health?secret=private-value")

    request_id = response.headers["X-Request-ID"]
    request_logs = [
        record.getMessage()
        for record in caplog.records
        if record.name == "app.api.app"
        and "HTTP response started" in record.getMessage()
    ]

    assert len(request_logs) == 1
    assert f"request_id={request_id}" in request_logs[0]
    assert "method=GET" in request_logs[0]
    assert "status=200" in request_logs[0]
    assert "private-value" not in request_logs[0]


def test_request_log_should_include_response_start_duration(
    caplog,
) -> None:
    app = create_app(
        lifespan=empty_lifespan,
    )

    with (
        caplog.at_level(logging.INFO, logger="app.api.app"),
        patch(
            "app.api.app.perf_counter",
            side_effect=[10.0, 10.125],
        ),
        TestClient(app) as client,
    ):
        response = client.get("/health")

    request_logs = [
        record.getMessage()
        for record in caplog.records
        if record.name == "app.api.app"
        and "HTTP response started" in record.getMessage()
    ]

    assert response.status_code == 200
    assert len(request_logs) == 1
    assert f"request_id={response.headers['X-Request-ID']}" in request_logs[0]
    assert "duration_ms=125.000" in request_logs[0]


def test_unhandled_error_log_should_match_response_id(
    caplog,
) -> None:
    app = create_app(
        lifespan=empty_lifespan,
    )

    @app.get("/test-error-log")
    def raise_unhandled_error() -> None:
        raise RuntimeError("Sensitive internal detail")

    with (
        caplog.at_level(logging.ERROR, logger="app.api.app"),
        TestClient(app, raise_server_exceptions=False) as client,
    ):
        response = client.get("/test-error-log")

    request_id = response.headers["X-Request-ID"]
    error_logs = [
        record.getMessage()
        for record in caplog.records
        if record.name == "app.api.app"
        and "Unhandled HTTP request" in record.getMessage()
    ]

    assert response.status_code == 500
    assert len(error_logs) == 1
    assert f"request_id={request_id}" in error_logs[0]
    assert "method=GET" in error_logs[0]
    assert "Sensitive internal detail" not in error_logs[0]


def test_unhandled_error_should_expose_request_id_to_configured_origin(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173",
    )
    app = create_app(lifespan=empty_lifespan)

    @app.get("/test-cors-error")
    def raise_unhandled_error() -> None:
        raise RuntimeError("Sensitive internal detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/test-cors-error",
            headers={"Origin": "http://localhost:5173"},
        )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == ("http://localhost:5173")
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()
    assert (
        str(UUID(response.headers["X-Request-ID"])) == response.headers["X-Request-ID"]
    )
