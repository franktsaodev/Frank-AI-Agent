from unittest.mock import patch

from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

from app.api.app import create_app
from tests.helpers.lifespan import empty_lifespan


def get_sample_value(
    metrics_text: str,
    *,
    name: str,
    labels: dict[str, str],
) -> float | None:
    for family in text_string_to_metric_families(metrics_text):
        for sample in family.samples:
            if sample.name == name and sample.labels == labels:
                return sample.value

    return None


def test_metrics_should_count_http_requests() -> None:
    app = create_app(lifespan=empty_lifespan)

    with TestClient(app) as client:
        first_response = client.get("/health")
        second_response = client.get("/health")
        metrics_response = client.get("/metrics")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert metrics_response.status_code == 200
    assert metrics_response.headers["content-type"].startswith("text/plain")

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_http_requests_total",
            labels={
                "method": "GET",
                "route": "/health",
                "status": "200",
            },
        )
        == 2.0
    )


def test_metrics_should_be_isolated_between_app_instances() -> None:
    first_app = create_app(lifespan=empty_lifespan)
    second_app = create_app(lifespan=empty_lifespan)

    with (
        TestClient(first_app) as first_client,
        TestClient(second_app) as second_client,
    ):
        health_response = first_client.get("/health")
        first_metrics = first_client.get("/metrics")
        second_metrics = second_client.get("/metrics")

    assert health_response.status_code == 200
    assert first_metrics.status_code == 200
    assert second_metrics.status_code == 200

    labels = {
        "method": "GET",
        "route": "/health",
        "status": "200",
    }

    assert (
        get_sample_value(
            first_metrics.text,
            name="frank_ai_agent_http_requests_total",
            labels=labels,
        )
        == 1.0
    )

    assert get_sample_value(
        second_metrics.text,
        name="frank_ai_agent_http_requests_total",
        labels=labels,
    ) in (None, 0.0)


def test_metrics_should_observe_response_start_duration_in_seconds() -> None:
    app = create_app(lifespan=empty_lifespan)

    with TestClient(app) as client:
        with patch(
            "app.api.app.perf_counter",
            side_effect=[10.0, 10.125],
        ):
            response = client.get("/health")

        metrics_response = client.get("/metrics")

    assert response.status_code == 200
    assert metrics_response.status_code == 200

    labels = {
        "method": "GET",
        "route": "/health",
        "status": "200",
    }
    metric_name = "frank_ai_agent_http_response_start_duration_seconds"

    assert (
        get_sample_value(
            metrics_response.text,
            name=f"{metric_name}_sum",
            labels=labels,
        )
        == 0.125
    )

    assert (
        get_sample_value(
            metrics_response.text,
            name=f"{metric_name}_count",
            labels=labels,
        )
        == 1.0
    )

    assert (
        get_sample_value(
            metrics_response.text,
            name=f"{metric_name}_bucket",
            labels={**labels, "le": "0.1"},
        )
        == 0.0
    )

    assert (
        get_sample_value(
            metrics_response.text,
            name=f"{metric_name}_bucket",
            labels={**labels, "le": "0.25"},
        )
        == 1.0
    )


def test_metrics_should_use_route_templates_without_private_values() -> None:
    app = create_app(lifespan=empty_lifespan)

    @app.get("/test-metrics/{session_id}")
    def get_test_session(session_id: str) -> dict[str, str]:
        return {"session_id": session_id}

    with TestClient(app) as client:
        first_response = client.get(
            "/test-metrics/private-session-alpha?secret=private-query",
        )
        second_response = client.get(
            "/test-metrics/private-session-beta",
        )
        metrics_response = client.get("/metrics")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert metrics_response.status_code == 200

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_http_requests_total",
            labels={
                "method": "GET",
                "route": "/test-metrics/{session_id}",
                "status": "200",
            },
        )
        == 2.0
    )

    for private_value in (
        "private-session-alpha",
        "private-session-beta",
        "private-query",
        first_response.headers["X-Request-ID"],
    ):
        assert private_value not in metrics_response.text


def test_metrics_should_group_missing_routes_under_unmatched() -> None:
    app = create_app(lifespan=empty_lifespan)

    with TestClient(app) as client:
        first_response = client.get("/private-missing-alpha")
        second_response = client.get(
            "/private-missing-beta?secret=private-query",
        )
        metrics_response = client.get("/metrics")

    assert first_response.status_code == 404
    assert second_response.status_code == 404
    assert metrics_response.status_code == 200

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_http_requests_total",
            labels={
                "method": "GET",
                "route": "unmatched",
                "status": "404",
            },
        )
        == 2.0
    )

    assert "private-missing-alpha" not in metrics_response.text
    assert "private-missing-beta" not in metrics_response.text
    assert "private-query" not in metrics_response.text


def test_metrics_should_count_sanitized_unhandled_errors() -> None:
    app = create_app(lifespan=empty_lifespan)

    @app.get("/test-metrics-error")
    def raise_unhandled_error() -> None:
        raise RuntimeError("Private internal failure detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-metrics-error")
        metrics_response = client.get("/metrics")

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert metrics_response.status_code == 200

    labels = {
        "method": "GET",
        "route": "/test-metrics-error",
        "status": "500",
    }

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_http_requests_total",
            labels=labels,
        )
        == 1.0
    )

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_http_response_start_duration_seconds_count",
            labels=labels,
        )
        == 1.0
    )

    assert "Private internal failure detail" not in metrics_response.text


def test_metrics_should_exclude_repeated_metrics_scrapes() -> None:
    app = create_app(lifespan=empty_lifespan)

    with TestClient(app) as client:
        health_response = client.get("/health")
        first_metrics = client.get("/metrics")
        second_metrics = client.get("/metrics")

    assert health_response.status_code == 200

    for response in (first_metrics, second_metrics):
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

        assert (
            get_sample_value(
                response.text,
                name="frank_ai_agent_http_requests_total",
                labels={
                    "method": "GET",
                    "route": "/health",
                    "status": "200",
                },
            )
            == 1.0
        )

        for family in text_string_to_metric_families(response.text):
            for sample in family.samples:
                assert sample.labels.get("route") != "/metrics"


def test_metrics_should_group_nonstandard_methods_under_other() -> None:
    app = create_app(lifespan=empty_lifespan)

    with TestClient(app) as client:
        first_response = client.request("CUSTOMALPHA", "/health")
        second_response = client.request("CUSTOMBETA", "/health")
        metrics_response = client.get("/metrics")

    assert first_response.status_code == 405
    assert second_response.status_code == 405
    assert metrics_response.status_code == 200

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_http_requests_total",
            labels={
                "method": "OTHER",
                "route": "/health",
                "status": "405",
            },
        )
        == 2.0
    )

    assert "CUSTOMALPHA" not in metrics_response.text
    assert "CUSTOMBETA" not in metrics_response.text
