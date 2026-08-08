from fastapi.testclient import TestClient

from app.api.app import create_app
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
        "version": "1.0.0",
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
