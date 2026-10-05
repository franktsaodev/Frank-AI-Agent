from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

from app.api.app import create_app
from app.api.http_metrics import HttpMetrics
from app.api.session_dependencies import get_session_manager
from app.models.chat_stream_event import (
    ChatContentDelta,
    ChatStreamCompleted,
    ChatStreamEvent,
)
from app.session.session_conflict_error import SessionConflictError
from app.session.session_id import SessionId
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


def get_active_chat_streams(
    metrics: HttpMetrics,
) -> float | None:
    return get_sample_value(
        metrics.render().decode("utf-8"),
        name="frank_ai_agent_chat_streams_active",
        labels={},
    )


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


@pytest.mark.parametrize(
    "outcome",
    ["completed", "failed", "incomplete"],
)
def test_metrics_should_expose_zero_chat_stream_counters_before_any_stream(
    outcome: str,
) -> None:
    app = create_app(lifespan=empty_lifespan)

    with TestClient(app) as client:
        response = client.get("/metrics")

    assert response.status_code == 200

    labels = {"outcome": outcome}

    assert (
        get_sample_value(
            response.text,
            name="frank_ai_agent_chat_streams_total",
            labels=labels,
        )
        == 0.0
    )

    assert (
        get_sample_value(
            response.text,
            name="frank_ai_agent_chat_stream_duration_seconds_count",
            labels=labels,
        )
        is None
    )


@pytest.mark.parametrize(
    "outcome",
    ["completed", "incomplete"],
)
def test_metrics_should_record_chat_stream_outcome_and_duration(
    outcome: str,
) -> None:
    app = create_app(lifespan=empty_lifespan)
    manager = MagicMock()

    app.dependency_overrides[get_session_manager] = lambda: manager

    events: list[ChatStreamEvent] = [
        ChatContentDelta(content="Private response"),
    ]

    if outcome == "completed":
        events.append(
            ChatStreamCompleted(response="Private response"),
        )

    manager.get.return_value.agent.stream_chat.return_value = iter(events)

    with TestClient(app) as client:
        with patch(
            "app.api.v1.session_routes.perf_counter",
            side_effect=[20.0, 20.5],
        ):
            response = client.post(
                "/api/v1/sessions/private-session/chat/stream",
                json={"message": "Private prompt"},
            )

        metrics_response = client.get("/metrics")

    assert response.status_code == 200
    assert metrics_response.status_code == 200
    assert ("event: completed\n" in response.text) == (outcome == "completed")
    assert manager.save.call_count == (1 if outcome == "completed" else 0)

    labels = {"outcome": outcome}

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_streams_total",
            labels=labels,
        )
        == 1.0
    )

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_stream_duration_seconds_count",
            labels=labels,
        )
        == 1.0
    )

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_stream_duration_seconds_sum",
            labels=labels,
        )
        == 0.5
    )

    for private_value in (
        "Private prompt",
        "Private response",
        "private-session",
        response.headers["X-Request-ID"],
    ):
        assert private_value not in metrics_response.text


@pytest.mark.parametrize(
    "failure_stage",
    ["iteration", "persistence", "conflict"],
)
def test_metrics_should_record_failed_chat_streams(
    failure_stage: str,
) -> None:
    app = create_app(lifespan=empty_lifespan)
    manager = MagicMock()

    app.dependency_overrides[get_session_manager] = lambda: manager

    def failing_events() -> Iterator[ChatStreamEvent]:
        yield ChatContentDelta(content="Private response")
        raise RuntimeError("Private failure detail")

    if failure_stage == "iteration":
        events = failing_events()
    else:
        events = iter(
            [
                ChatContentDelta(content="Private response"),
                ChatStreamCompleted(response="Private response"),
            ]
        )
        if failure_stage == "conflict":
            manager.save.side_effect = SessionConflictError(
                session_id=SessionId(value="private-session"),
            )
        else:
            manager.save.side_effect = RuntimeError("Private failure detail")

    manager.get.return_value.agent.stream_chat.return_value = events

    with TestClient(app) as client:
        with patch(
            "app.api.v1.session_routes.perf_counter",
            side_effect=[30.0, 30.25],
        ):
            response = client.post(
                "/api/v1/sessions/private-session/chat/stream",
                json={"message": "Private prompt"},
            )

        metrics_response = client.get("/metrics")

    assert response.status_code == 200
    assert "event: error\n" in response.text
    assert "event: completed\n" not in response.text
    if failure_stage == "conflict":
        assert '"error":"session_conflict"' in response.text
    assert "Private failure detail" not in response.text
    assert manager.save.call_count == (0 if failure_stage == "iteration" else 1)
    assert metrics_response.status_code == 200

    labels = {"outcome": "failed"}

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_streams_total",
            labels=labels,
        )
        == 1.0
    )

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_stream_duration_seconds_count",
            labels=labels,
        )
        == 1.0
    )

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_stream_duration_seconds_sum",
            labels=labels,
        )
        == 0.25
    )

    for outcome in ("completed", "incomplete"):
        assert get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_streams_total",
            labels={"outcome": outcome},
        ) in (None, 0.0)

    for private_value in (
        "Private prompt",
        "Private response",
        "Private failure detail",
        "private-session",
        response.headers["X-Request-ID"],
    ):
        assert private_value not in metrics_response.text


def test_chat_stream_metrics_should_be_isolated_between_app_instances() -> None:
    first_app = create_app(lifespan=empty_lifespan)
    second_app = create_app(lifespan=empty_lifespan)
    manager = MagicMock()

    first_app.dependency_overrides[get_session_manager] = lambda: manager
    manager.get.return_value.agent.stream_chat.return_value = iter(
        [
            ChatStreamCompleted(response="Done"),
        ]
    )

    with (
        TestClient(first_app) as first_client,
        TestClient(second_app) as second_client,
    ):
        response = first_client.post(
            "/api/v1/sessions/session-123/chat/stream",
            json={"message": "Hello"},
        )
        first_metrics = first_client.get("/metrics")
        second_metrics = second_client.get("/metrics")

    assert response.status_code == 200
    assert "event: completed\n" in response.text
    assert first_metrics.status_code == 200
    assert second_metrics.status_code == 200

    labels = {"outcome": "completed"}

    for metric_name in (
        "frank_ai_agent_chat_streams_total",
        "frank_ai_agent_chat_stream_duration_seconds_count",
    ):
        assert (
            get_sample_value(
                first_metrics.text,
                name=metric_name,
                labels=labels,
            )
            == 1.0
        )

        assert get_sample_value(
            second_metrics.text,
            name=metric_name,
            labels=labels,
        ) in (None, 0.0)


def test_metrics_should_expose_zero_active_chat_streams() -> None:
    app = create_app(lifespan=empty_lifespan)

    with TestClient(app) as client:
        response = client.get("/metrics")

    assert response.status_code == 200

    assert (
        get_sample_value(
            response.text,
            name="frank_ai_agent_chat_streams_active",
            labels={},
        )
        == 0.0
    )


@pytest.mark.parametrize(
    "outcome",
    ["completed", "failed", "incomplete"],
)
def test_metrics_should_track_active_chat_stream_iteration(
    outcome: str,
) -> None:
    app = create_app(lifespan=empty_lifespan)
    manager = MagicMock()

    app.dependency_overrides[get_session_manager] = lambda: manager

    active_values: list[float | None] = []

    def record_active_value() -> None:
        metrics_text = app.state.http_metrics.render().decode("utf-8")

        active_values.append(
            get_sample_value(
                metrics_text,
                name="frank_ai_agent_chat_streams_active",
                labels={},
            ),
        )

    def stream_events() -> Iterator[ChatStreamEvent]:
        record_active_value()

        yield ChatContentDelta(content="Private response")

        record_active_value()

        if outcome == "completed":
            yield ChatStreamCompleted(response="Private response")
        elif outcome == "failed":
            raise RuntimeError("Private stream failure detail")

    manager.get.return_value.agent.stream_chat.return_value = stream_events()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/sessions/private-session/chat/stream",
            json={"message": "Private prompt"},
        )

        metrics_response = client.get("/metrics")

    assert response.status_code == 200
    assert metrics_response.status_code == 200
    assert active_values == [1.0, 1.0]

    assert ("event: completed\n" in response.text) == (outcome == "completed")
    assert ("event: error\n" in response.text) == (outcome == "failed")
    assert manager.save.call_count == (1 if outcome == "completed" else 0)
    assert "Private stream failure detail" not in response.text

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_streams_active",
            labels={},
        )
        == 0.0
    )

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_streams_total",
            labels={"outcome": outcome},
        )
        == 1.0
    )


def test_metrics_should_release_overlapping_chat_streams_when_closed() -> None:
    metrics = HttpMetrics()
    finalized: list[str] = []

    def stream_events(name: str) -> Iterator[str]:
        try:
            yield name
        finally:
            finalized.append(name)

    first_stream = metrics.track_chat_stream(stream_events("first"))
    second_stream = metrics.track_chat_stream(stream_events("second"))

    try:
        assert get_active_chat_streams(metrics) == 0.0

        assert next(first_stream) == "first"
        assert get_active_chat_streams(metrics) == 1.0

        assert next(second_stream) == "second"
        assert get_active_chat_streams(metrics) == 2.0

        first_stream.close()
        assert get_active_chat_streams(metrics) == 1.0
        assert finalized == ["first"]

        first_stream.close()
        assert get_active_chat_streams(metrics) == 1.0
        assert finalized == ["first"]

        second_stream.close()
        assert get_active_chat_streams(metrics) == 0.0
        assert finalized == ["first", "second"]

        second_stream.close()
        assert get_active_chat_streams(metrics) == 0.0
        assert finalized == ["first", "second"]
    finally:
        first_stream.close()
        second_stream.close()


def test_metrics_should_not_count_a_chat_stream_closed_before_iteration() -> None:
    metrics = HttpMetrics()
    started = MagicMock()

    def stream_events() -> Iterator[str]:
        started()
        yield "Private response"

    stream = metrics.track_chat_stream(stream_events())

    assert get_active_chat_streams(metrics) == 0.0

    stream.close()
    stream.close()

    started.assert_not_called()
    assert get_active_chat_streams(metrics) == 0.0


def test_active_chat_stream_metrics_should_be_isolated_between_apps() -> None:
    first_app = create_app(lifespan=empty_lifespan)
    second_app = create_app(lifespan=empty_lifespan)

    first_metrics: HttpMetrics = first_app.state.http_metrics
    second_metrics: HttpMetrics = second_app.state.http_metrics

    first_stream = first_metrics.track_chat_stream(iter(["first"]))
    second_stream = second_metrics.track_chat_stream(iter(["second"]))

    try:
        assert next(first_stream) == "first"
        assert get_active_chat_streams(first_metrics) == 1.0
        assert get_active_chat_streams(second_metrics) == 0.0

        assert next(second_stream) == "second"
        assert get_active_chat_streams(first_metrics) == 1.0
        assert get_active_chat_streams(second_metrics) == 1.0

        first_stream.close()
        assert get_active_chat_streams(first_metrics) == 0.0
        assert get_active_chat_streams(second_metrics) == 1.0

        second_stream.close()
        assert get_active_chat_streams(first_metrics) == 0.0
        assert get_active_chat_streams(second_metrics) == 0.0
    finally:
        first_stream.close()
        second_stream.close()


@pytest.mark.parametrize(
    "save_error",
    [
        RuntimeError("Private persistence failure"),
        SessionConflictError(
            session_id=SessionId(value="private-session"),
        ),
    ],
    ids=["unexpected-error", "session-conflict"],
)
def test_metrics_should_release_active_chat_stream_after_save_failure(
    save_error: Exception,
) -> None:
    app = create_app(lifespan=empty_lifespan)
    metrics: HttpMetrics = app.state.http_metrics
    manager = MagicMock()

    app.dependency_overrides[get_session_manager] = lambda: manager

    manager.get.return_value.agent.stream_chat.return_value = iter(
        [
            ChatStreamCompleted(response="Private response"),
        ],
    )

    active_during_save: list[float | None] = []

    def fail_save(session: object) -> None:
        active_during_save.append(get_active_chat_streams(metrics))
        raise save_error

    manager.save.side_effect = fail_save

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/sessions/private-session/chat/stream",
            json={"message": "Private prompt"},
        )

        metrics_response = client.get("/metrics")

    assert response.status_code == 200
    assert metrics_response.status_code == 200
    assert active_during_save == [1.0]
    manager.save.assert_called_once()

    assert "event: error\n" in response.text
    assert "event: completed\n" not in response.text
    assert "Private persistence failure" not in response.text

    assert get_active_chat_streams(metrics) == 0.0

    assert (
        get_sample_value(
            metrics_response.text,
            name="frank_ai_agent_chat_streams_total",
            labels={"outcome": "failed"},
        )
        == 1.0
    )
