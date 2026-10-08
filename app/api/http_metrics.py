from collections.abc import Generator, Iterable
from typing import Literal

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

ChatStreamOutcome = Literal["completed", "failed", "incomplete"]


class HttpMetrics:
    def __init__(self) -> None:
        self._registry = CollectorRegistry()

        self._chat_streams_active = Gauge(
            "frank_ai_agent_chat_streams_active",
            "Chat stream serializer iterations currently in progress.",
            registry=self._registry,
        )

        self._requests = Counter(
            "frank_ai_agent_http_requests_total",
            "HTTP responses started, excluding the metrics endpoint.",
            labelnames=("method", "route", "status"),
            registry=self._registry,
        )

        self._response_start_duration = Histogram(
            "frank_ai_agent_http_response_start_duration_seconds",
            "Middleware duration until an HTTP response is available.",
            labelnames=("method", "route", "status"),
            registry=self._registry,
        )

        self._chat_streams = Counter(
            "frank_ai_agent_chat_streams_total",
            "Chat streams finished, grouped by outcome.",
            labelnames=("outcome",),
            registry=self._registry,
        )

        for outcome in ("completed", "failed", "incomplete"):
            self._chat_streams.labels(outcome=outcome)

        self._chat_stream_duration = Histogram(
            "frank_ai_agent_chat_stream_duration_seconds",
            "Duration from chat stream iteration start until termination.",
            labelnames=("outcome",),
            buckets=(
                0.1,
                0.25,
                0.5,
                1.0,
                2.5,
                5.0,
                10.0,
                30.0,
                60.0,
                120.0,
                300.0,
            ),
            registry=self._registry,
        )

        self._chat_stream_first_content_duration = Histogram(
            "frank_ai_agent_chat_stream_first_content_duration_seconds",
            "Duration from serializer iteration start until first content is serialized.",
            buckets=(
                0.1,
                0.25,
                0.5,
                1.0,
                2.5,
                5.0,
                10.0,
                30.0,
                60.0,
                120.0,
                300.0,
            ),
            registry=self._registry,
        )

    def observe_response(
        self,
        *,
        method: str,
        route: str,
        status: int,
        duration_seconds: float,
    ) -> None:
        known_methods = {
            "GET",
            "HEAD",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
            "TRACE",
            "CONNECT",
        }

        labels = {
            "method": method if method in known_methods else "OTHER",
            "route": route,
            "status": str(status),
        }

        self._requests.labels(**labels).inc()
        self._response_start_duration.labels(**labels).observe(
            duration_seconds,
        )

    def observe_chat_stream(
        self,
        *,
        outcome: ChatStreamOutcome,
        duration_seconds: float,
    ) -> None:
        self._chat_streams.labels(outcome=outcome).inc()
        self._chat_stream_duration.labels(outcome=outcome).observe(
            duration_seconds,
        )

    def observe_chat_stream_first_content(
        self,
        *,
        duration_seconds: float,
    ) -> None:
        self._chat_stream_first_content_duration.observe(
            duration_seconds,
        )

    def track_chat_stream(
        self,
        events: Iterable[str],
    ) -> Generator[str, None, None]:
        with self._chat_streams_active.track_inprogress():
            yield from events

    def render(self) -> bytes:
        return generate_latest(self._registry)
