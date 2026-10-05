FROM grafana/grafana:13.2.3

COPY provisioning/datasources/prometheus.yml /etc/grafana/provisioning/datasources/prometheus.yml
COPY provisioning/dashboards/dashboards.yml /etc/grafana/provisioning/dashboards/dashboards.yml
COPY dashboards/frank-ai-agent.json /etc/grafana/dashboards/frank-ai-agent.json