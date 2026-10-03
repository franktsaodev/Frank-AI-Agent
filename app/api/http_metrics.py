from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)


class HttpMetrics:
    def __init__(self) -> None:
        self._registry = CollectorRegistry()

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

    def render(self) -> bytes:
        return generate_latest(self._registry)
