import argparse
import base64
import json
from math import isclose, isfinite
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

Sample = tuple[dict[str, str], float]


def query_grafana(
    headers: dict[str, str],
    expression: str,
    *,
    instant: bool = True,
) -> list[Sample]:
    payload = {
        "from": "now-2m",
        "to": "now",
        "queries": [
            {
                "refId": "A",
                "datasource": {
                    "type": "prometheus",
                    "uid": "frank-ai-agent-prometheus",
                },
                "expr": expression,
                "format": "time_series",
                "instant": instant,
                "range": not instant,
                "intervalMs": 15000,
                "maxDataPoints": 20,
            }
        ],
    }

    request = Request(
        "http://127.0.0.1:13000/api/ds/query",
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            result = json.load(response)["results"]["A"]
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Grafana query failed: {detail}") from error

    if result.get("error"):
        raise RuntimeError(f"Grafana query failed: {result['error']}")

    samples: list[Sample] = []

    for frame in result.get("frames", []):
        fields = frame["schema"]["fields"]
        columns = frame["data"]["values"]

        for field, values in zip(fields, columns, strict=True):
            if field["type"] != "number" or not values or values[-1] is None:
                continue

            value = values[-1]

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
            ):
                raise RuntimeError("Grafana returned a non-finite or invalid value.")

            samples.append((field.get("labels", {}), float(value)))

    return samples


def group_values(
    samples: list[Sample],
    *,
    label: str,
    expected: set[str],
) -> dict[str, float]:
    grouped: dict[str, float] = {}

    for labels, value in samples:
        key = labels.get(label)

        if key is None or key in grouped or value <= 0:
            raise RuntimeError(f"Unexpected sample for label {label}: {labels}={value}")

        grouped[key] = value

    if set(grouped) != expected:
        raise RuntimeError(f"Unexpected {label} series: {grouped}")

    return grouped


def verify_panel_queries(
    queries: dict[int, tuple[str, bool]],
    headers: dict[str, str],
    *,
    active_stream_state: str,
    first_content_state: str,
) -> None:
    if set(queries) != {1, 2, 3, 4, 5, 6, 7, 8}:
        raise RuntimeError("Expected dashboard panel IDs 1 through 8.")

    if not queries[7][1]:
        raise RuntimeError("The active chat stream panel must use an instant query.")

    readiness_query = (
        "min(count_over_time("
        'frank_ai_agent_http_requests_total{job="frank-ai-agent"}[1m]))'
    )

    for _ in range(40):
        samples = query_grafana(headers, readiness_query)

        if len(samples) == 1 and samples[0][1] >= 3:
            break

        sleep(2)
    else:
        raise RuntimeError("Prometheus did not collect three fixture samples in time.")

    results = {
        panel_id: query_grafana(
            headers,
            expression.replace("$__rate_interval", "1m"),
            instant=instant,
        )
        for panel_id, (expression, instant) in queries.items()
    }

    scrape = results[1]

    if (
        len(scrape) != 1
        or scrape[0][0].get("instance") != "api:8000"
        or scrape[0][1] != 1.0
    ):
        raise RuntimeError(f"Unexpected scrape status: {scrape}")

    outcomes = {"completed", "failed", "incomplete"}

    for panel_id in (2, 5):
        counts = group_values(
            results[panel_id],
            label="outcome",
            expected=outcomes,
        )

        if not (
            isclose(
                counts["completed"],
                3 * counts["failed"],
                rel_tol=1e-6,
            )
            and isclose(
                counts["incomplete"],
                counts["failed"],
                rel_tol=1e-6,
            )
        ):
            raise RuntimeError(
                f"Panel {panel_id} has unexpected outcome ratios: {counts}"
            )

    rates = group_values(
        results[3],
        label="status",
        expected={"200", "500"},
    )

    if not isclose(rates["200"], 5 * rates["500"], rel_tol=1e-6):
        raise RuntimeError(f"Unexpected HTTP rate ratio: {rates}")

    percentile = results[4]

    if (
        len(percentile) != 1
        or percentile[0][0].get("method") != "GET"
        or percentile[0][0].get("route") != "/health"
        or not isclose(percentile[0][1], 0.205, rel_tol=1e-6)
    ):
        raise RuntimeError(f"Unexpected HTTP response-start P95: {percentile}")

    durations = group_values(
        results[6],
        label="outcome",
        expected=outcomes,
    )

    expected_durations = {
        "completed": 0.5,
        "failed": 1.0,
        "incomplete": 0.25,
    }

    for outcome, expected in expected_durations.items():
        if not isclose(durations[outcome], expected, rel_tol=1e-6):
            raise RuntimeError(
                f"Unexpected average duration for {outcome}: {durations}"
            )

    active_streams = results[7]
    expected_active_values: dict[str, float | None] = {
        "active": 2.0,
        "idle": 0.0,
        "missing": None,
    }
    expected_active_value = expected_active_values[active_stream_state]

    if expected_active_value is None:
        if active_streams:
            raise RuntimeError(
                "Unexpected active chat stream count for "
                f"{active_stream_state}: {active_streams}"
            )
    elif (
        len(active_streams) != 1
        or active_streams[0][0] != {}
        or active_streams[0][1] != expected_active_value
    ):
        raise RuntimeError(
            "Unexpected active chat stream count for "
            f"{active_stream_state}: {active_streams}"
        )

    first_content_percentile = results[8]

    if first_content_state == "unobserved":
        first_content_counts = query_grafana(
            headers,
            "sum("
            "frank_ai_agent_chat_stream_first_content_duration_seconds_count"
            '{job="frank-ai-agent"})',
        )

        if (
            len(first_content_counts) != 1
            or first_content_counts[0][0] != {}
            or first_content_counts[0][1] != 0.0
        ):
            raise RuntimeError(
                "Expected an existing first-content histogram with zero observations: "
                f"{first_content_counts}"
            )

        if first_content_percentile:
            raise RuntimeError(
                "Expected no first-content P95 without observations: "
                f"{first_content_percentile}"
            )
    elif (
        len(first_content_percentile) != 1
        or first_content_percentile[0][0] != {}
        or not isclose(
            first_content_percentile[0][1],
            0.2425,
            rel_tol=1e-6,
        )
    ):
        raise RuntimeError(
            f"Unexpected chat stream first-content P95: {first_content_percentile}"
        )

    print(f"First-content state verified: {first_content_state}.")

    print(f"Active stream state verified: {active_stream_state}.")

    for panel_id in sorted(results):
        print(f"Panel {panel_id} query verified: {len(results[panel_id])} series.")

    print("Monitoring integration verified through Grafana's Prometheus data source.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify Grafana provisioning and optional fixture queries.",
    )

    parser.add_argument(
        "--queries",
        action="store_true",
        help="Verify dashboard queries against the monitoring fixture stack.",
    )

    parser.add_argument(
        "--active-stream-state",
        choices=("active", "idle", "missing"),
        default="active",
        help="Expected active stream gauge state in the monitoring fixture.",
    )

    parser.add_argument(
        "--first-content-state",
        choices=("observed", "unobserved"),
        default="observed",
        help="Expected first-content histogram state in the monitoring fixture.",
    )

    args = parser.parse_args()

    base_url = "http://127.0.0.1:13000"
    datasource_uid = "frank-ai-agent-prometheus"
    dashboard_uid = "frank-ai-agent-overview"

    # Credentials belong to a fresh, disposable verification container.
    credentials = base64.b64encode(b"admin:admin").decode("ascii")
    headers = {
        "Authorization": f"Basic {credentials}",
    }

    dashboard_request = Request(
        f"{base_url}/apis/dashboard.grafana.app/v1/"
        f"namespaces/default/dashboards/{dashboard_uid}",
        headers=headers,
    )

    dashboard_response = None

    for _ in range(30):
        try:
            with urlopen(dashboard_request, timeout=3) as response:
                dashboard_response = json.load(response)
            break
        except HTTPError as error:
            if error.code != 404:
                raise
        except (URLError, TimeoutError, ConnectionError):
            pass

        sleep(2)

    if dashboard_response is None:
        raise RuntimeError("Grafana did not load the dashboard in time.")

    if dashboard_response["metadata"]["name"] != dashboard_uid:
        raise RuntimeError("Unexpected dashboard UID.")

    dashboard = dashboard_response["spec"]

    if dashboard["title"] != "Frank AI Agent Overview":
        raise RuntimeError("Unexpected dashboard title.")

    panels = dashboard["panels"]

    if len(panels) != 8:
        raise RuntimeError("Expected eight dashboard panels.")

    for panel in panels:
        if panel.get("datasource", {}).get("uid") != datasource_uid:
            raise RuntimeError("A panel references an unexpected data source.")

    active_panels = [panel for panel in panels if panel.get("id") == 7]

    if len(active_panels) != 1:
        raise RuntimeError("Expected exactly one active chat stream panel.")

    active_panel = active_panels[0]
    active_targets = active_panel.get("targets", [])

    if (
        active_panel.get("title") != "Active chat stream iterations"
        or active_panel.get("type") != "stat"
        or active_panel.get("fieldConfig", {}).get("defaults", {}).get("noValue")
        != "No data"
    ):
        raise RuntimeError("Unexpected active chat stream panel configuration.")

    if (
        len(active_targets) != 1
        or active_targets[0].get("instant") is not True
        or active_targets[0].get("range") is not False
    ):
        raise RuntimeError(
            "The active chat stream panel must use only an instant query."
        )

    first_content_panels = [panel for panel in panels if panel.get("id") == 8]

    if len(first_content_panels) != 1:
        raise RuntimeError("Expected exactly one first-content duration panel.")

    first_content_panel = first_content_panels[0]
    first_content_targets = first_content_panel.get("targets", [])
    first_content_defaults = first_content_panel.get("fieldConfig", {}).get(
        "defaults", {}
    )

    if (
        first_content_panel.get("title") != "Chat stream first-content duration P95"
        or first_content_panel.get("type") != "timeseries"
        or first_content_defaults.get("unit") != "s"
        or first_content_defaults.get("noValue") != "No data"
    ):
        raise RuntimeError("Unexpected first-content duration panel configuration.")

    if (
        len(first_content_targets) != 1
        or first_content_targets[0].get("instant") is not False
        or first_content_targets[0].get("range") is not True
    ):
        raise RuntimeError(
            "The first-content duration panel must use only a range query."
        )

    datasource_request = Request(
        f"{base_url}/api/datasources/uid/{datasource_uid}",
        headers=headers,
    )

    with urlopen(datasource_request, timeout=10) as response:
        datasource = json.load(response)

    if (
        datasource["uid"] != datasource_uid
        or datasource["type"] != "prometheus"
        or datasource["url"] != "http://prometheus:9090"
        or not datasource["isDefault"]
    ):
        raise RuntimeError("Unexpected Prometheus data source configuration.")

    print(
        "Grafana provisioning verified: "
        "Prometheus data source and eight dashboard panels."
    )

    if args.queries:
        panel_queries: dict[int, tuple[str, bool]] = {}

        for panel in panels:
            targets = panel["targets"]

            if len(targets) != 1 or targets[0].get("refId") != "A":
                raise RuntimeError("Expected one query with refId A in each panel.")

            expression = targets[0].get("expr")

            if not isinstance(expression, str) or not expression:
                raise RuntimeError("A panel has no valid PromQL expression.")

            panel_queries[panel["id"]] = (
                expression,
                bool(targets[0].get("instant", False)),
            )

        verify_panel_queries(
            panel_queries,
            headers,
            active_stream_state=args.active_stream_state,
            first_content_state=args.first_content_state,
        )


if __name__ == "__main__":
    main()
