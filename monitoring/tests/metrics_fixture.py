from http.server import BaseHTTPRequestHandler, HTTPServer
from os import environ
from time import monotonic


def histogram_samples(
    *,
    name: str,
    labels: str,
    count: int,
    duration: float,
    buckets: tuple[float, ...] = (0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
) -> list[str]:
    samples: list[str] = []
    bucket_prefix = f"{labels}," if labels else ""
    label_suffix = f"{{{labels}}}" if labels else ""

    for boundary in buckets:
        bucket_count = count if duration <= boundary else 0
        samples.append(
            f'{name}_bucket{{{bucket_prefix}le="{boundary}"}} {bucket_count}'
        )

    samples.extend(
        [
            f'{name}_bucket{{{bucket_prefix}le="+Inf"}} {count}',
            f"{name}_count{label_suffix} {count}",
            f"{name}_sum{label_suffix} {count * duration}",
        ]
    )

    return samples


def render_metrics(
    batch: int,
    *,
    active_streams: float | None,
    first_content_observed: bool,
) -> bytes:
    http_counter = "frank_ai_agent_http_requests_total"
    http_duration = "frank_ai_agent_http_response_start_duration_seconds"
    stream_counter = "frank_ai_agent_chat_streams_total"
    stream_duration = "frank_ai_agent_chat_stream_duration_seconds"
    stream_active = "frank_ai_agent_chat_streams_active"
    first_content_duration = "frank_ai_agent_chat_stream_first_content_duration_seconds"

    samples = [
        f"# HELP {http_counter} Synthetic HTTP response counters.",
        f"# TYPE {http_counter} counter",
        f'{http_counter}{{method="GET",route="/health",status="200"}} {10 * batch}',
        f'{http_counter}{{method="GET",route="/health",status="500"}} {2 * batch}',
        f"# HELP {http_duration} Synthetic HTTP response-start durations.",
        f"# TYPE {http_duration} histogram",
    ]

    for status_code, count, duration in (
        ("200", 10 * batch, 0.05),
        ("500", 2 * batch, 0.2),
    ):
        samples.extend(
            histogram_samples(
                name=http_duration,
                labels=f'method="GET",route="/health",status="{status_code}"',
                count=count,
                duration=duration,
            )
        )

    samples.extend(
        [
            f"# HELP {stream_counter} Synthetic chat stream counters.",
            f"# TYPE {stream_counter} counter",
        ]
    )

    outcomes = (
        ("completed", 3 * batch, 0.5),
        ("failed", batch, 1.0),
        ("incomplete", batch, 0.25),
    )

    for outcome, count, _ in outcomes:
        samples.append(f'{stream_counter}{{outcome="{outcome}"}} {count}')

    samples.extend(
        [
            f"# HELP {stream_duration} Synthetic chat stream durations.",
            f"# TYPE {stream_duration} histogram",
        ]
    )

    for outcome, count, duration in outcomes:
        samples.extend(
            histogram_samples(
                name=stream_duration,
                labels=f'outcome="{outcome}"',
                count=count,
                duration=duration,
            )
        )

    samples.extend(
        [
            f"# HELP {first_content_duration} Synthetic first-content durations.",
            f"# TYPE {first_content_duration} histogram",
        ]
    )
    samples.extend(
        histogram_samples(
            name=first_content_duration,
            labels="",
            count=5 * batch if first_content_observed else 0,
            duration=0.2,
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
        )
    )

    if active_streams is not None:
        samples.extend(
            [
                f"# HELP {stream_active} Synthetic active chat stream iterations.",
                f"# TYPE {stream_active} gauge",
                f"{stream_active} {active_streams}",
            ]
        )

    return ("\n".join(samples) + "\n").encode("utf-8")


class MetricsHandler(BaseHTTPRequestHandler):
    started_at = monotonic()
    active_streams: float | None = 2.0
    first_content_observed = True

    def do_GET(self) -> None:
        if self.path == "/health":
            body = b"ok\n"
            content_type = "text/plain; charset=utf-8"
        elif self.path == "/metrics":
            batch = int((monotonic() - self.started_at) / 5) + 1
            body = render_metrics(
                batch,
                active_streams=self.active_streams,
                first_content_observed=self.first_content_observed,
            )
            content_type = "text/plain; version=0.0.4; charset=utf-8"
        else:
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string: str, *args: object) -> None:
        pass


def main() -> None:
    active_stream_state = environ.get(
        "MONITORING_FIXTURE_ACTIVE_STREAM_STATE",
        "active",
    )
    active_values: dict[str, float | None] = {
        "active": 2.0,
        "idle": 0.0,
        "missing": None,
    }

    if active_stream_state not in active_values:
        raise ValueError(
            f"Invalid monitoring fixture active stream state: {active_stream_state}"
        )

    MetricsHandler.active_streams = active_values[active_stream_state]

    first_content_state = environ.get(
        "MONITORING_FIXTURE_FIRST_CONTENT_STATE",
        "observed",
    )

    if first_content_state not in {"observed", "unobserved"}:
        raise ValueError(
            f"Invalid monitoring fixture first-content state: {first_content_state}"
        )

    MetricsHandler.first_content_observed = first_content_state == "observed"

    with HTTPServer(("0.0.0.0", 8000), MetricsHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
