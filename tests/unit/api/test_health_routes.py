from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from redis import Redis
from redis.exceptions import RedisError

from app.api.app import create_app
from app.api.redis_dependencies import get_redis_client
from app.api.runtime import RuntimeInfo
from app.api.runtime_provider import get_runtime_info
from tests.helpers.lifespan import empty_lifespan


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
        "version": "1.4.0",
    }


def test_health_should_use_runtime_dependency() -> None:
    app = create_app(
        lifespan=empty_lifespan,
    )

    app.dependency_overrides[get_runtime_info] = lambda: RuntimeInfo(
        service_name="Test Agent",
        version="9.9.9",
    )

    try:
        with TestClient(app) as client:
            response = client.get(
                "/health",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Test Agent",
        "version": "9.9.9",
    }


def test_readiness_should_return_ready_when_redis_is_available() -> None:
    redis_client = MagicMock(
        spec=Redis,
    )
    redis_client.ping.return_value = True

    app = create_app(
        lifespan=empty_lifespan,
    )

    app.dependency_overrides[get_redis_client] = lambda: redis_client

    try:
        with TestClient(app) as client:
            response = client.get(
                "/ready",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "redis": "ok",
    }

    redis_client.ping.assert_called_once_with()


def test_readiness_should_return_service_unavailable_when_redis_fails() -> None:
    redis_client = MagicMock(
        spec=Redis,
    )
    redis_client.ping.side_effect = RedisError(
        "Sensitive Redis connection detail",
    )

    app = create_app(
        lifespan=empty_lifespan,
    )

    app.dependency_overrides[get_redis_client] = lambda: redis_client

    try:
        with TestClient(
            app,
            raise_server_exceptions=False,
        ) as client:
            response = client.get(
                "/ready",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "error": "service_unavailable",
        "message": "The service is not ready.",
    }

    assert "Sensitive Redis connection detail" not in response.text

    redis_client.ping.assert_called_once_with()


def test_readiness_should_return_service_unavailable_when_ping_returns_false() -> None:
    redis_client = MagicMock(
        spec=Redis,
    )
    redis_client.ping.return_value = False

    app = create_app(
        lifespan=empty_lifespan,
    )

    app.dependency_overrides[get_redis_client] = lambda: redis_client

    try:
        with TestClient(app) as client:
            response = client.get(
                "/ready",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "error": "service_unavailable",
        "message": "The service is not ready.",
    }

    redis_client.ping.assert_called_once_with()
