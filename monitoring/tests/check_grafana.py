import base64
import json
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> None:
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

    if len(panels) != 6:
        raise RuntimeError("Expected six dashboard panels.")

    for panel in panels:
        if panel.get("datasource", {}).get("uid") != datasource_uid:
            raise RuntimeError("A panel references an unexpected data source.")

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
        "Prometheus data source and six dashboard panels."
    )


if __name__ == "__main__":
    main()
