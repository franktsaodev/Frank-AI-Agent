FROM prom/prometheus:v3.15.0

COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY alerts.yml /etc/prometheus/alerts.yml
COPY tests/alerts.test.yml /etc/prometheus/tests/alerts.test.yml