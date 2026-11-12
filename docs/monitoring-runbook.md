# Monitoring alert runbook

This runbook covers the Prometheus alerts bundled with Frank AI Agent.

Run Docker Compose commands from the repository root. The HTTP diagnostic
commands below use PowerShell 7. Run PromQL queries in
[Prometheus](http://localhost:9090) or Grafana Explore.

| Alert                                    | Investigation                                             |
| ---------------------------------------- | --------------------------------------------------------- |
| `FrankAIAgentAPIScrapeFailed`            | [API metrics scrape failure](#api-metrics-scrape-failure) |
| `FrankAIAgentChatStreamFailures`         | [Chat stream failures](#chat-stream-failures)             |
| `FrankAIAgentChatStreamFirstContentSlow` | [Slow first content](#slow-first-content)                 |

Record the alert name, job, instance when present, incident time, recent
changes, and any available request IDs before investigating.

Alerts are evaluated in Prometheus. External notifications require a
configured Alertmanager.

## API metrics scrape failure

Alert: `FrankAIAgentAPIScrapeFailed`

The API target has reported `up=0` continuously for one minute.

This checks access to `/metrics`. Redis readiness is checked separately
through `/ready`. A target removed from the scrape configuration is not
detected by this rule.

### Check

Inspect service state and recent logs:

```powershell
docker compose --profile monitoring ps
docker compose logs --since 15m --tail 200 api
docker compose --profile monitoring logs --since 15m --tail 200 prometheus
```

Inspect the scrape target's error from Prometheus:

```powershell
$targets = Invoke-RestMethod `
    -Uri "http://127.0.0.1:9090/api/v1/targets?state=active" `
    -TimeoutSec 10 `
    -ErrorAction Stop

$targets.data.activeTargets |
    Where-Object { $_.labels.job -eq "frank-ai-agent" } |
    Select-Object scrapeUrl, health, lastError, lastScrape
```

Check host access to metrics and readiness separately:

```powershell
Invoke-WebRequest `
    -Uri "http://127.0.0.1:8000/metrics" `
    -SkipHttpErrorCheck `
    -TimeoutSec 10 `
    -ErrorAction Stop |
    Select-Object StatusCode

Invoke-WebRequest `
    -Uri "http://127.0.0.1:8000/ready" `
    -SkipHttpErrorCheck `
    -TimeoutSec 10 `
    -ErrorAction Stop |
    Select-Object StatusCode, Content
```

Successful host access does not prove that Prometheus can reach the API
through the Compose network. The configured container target is `api:8000`.

### Respond

- If the API is stopped or unhealthy, investigate its startup and runtime logs.
- If the API works from the host but scraping fails, use the target's
  `lastError` to investigate the scrape address and Compose networking.
- If `/ready` reports a storage problem, investigate Redis separately.
  A successful `/metrics` response does not confirm Redis readiness.
- Correct the identified service or configuration problem before restarting
  affected services.

### Confirm recovery

```promql
up{job="frank-ai-agent"}
```

The affected target should return `1`, its latest scrape error should be
empty, and the alert should become inactive. Confirm that the target still
exists; a missing series is not proof of recovery.

## Chat stream failures

Alert: `FrankAIAgentChatStreamFailures`

Prometheus observed a positive increase in the failed stream counter within
the last five minutes. This rule has no additional pending period.

Failures include stream processing and session persistence errors, including
session conflicts. An SSE response can start with HTTP `200` and fail later.

### Check

Inspect failed counter increases by instance:

```promql
increase(frank_ai_agent_chat_streams_total{job="frank-ai-agent",outcome="failed"}[5m])
```

Inspect API and Redis logs:

```powershell
docker compose logs --since 15m --tail 200 api redis
```

Look for `Chat stream finished` records with `outcome=failed`, then use their
fixed `error_code` and request ID to narrow the investigation.

If a request ID is available from the frontend diagnostics, search for it:

```powershell
$requestId = "replace-with-request-id"

docker compose logs --since 15m api |
    Select-String -SimpleMatch $requestId
```

Metrics intentionally omit request IDs and session IDs. Use request logs
for request-level correlation.

### Respond

- For provider or stream processing errors, investigate provider availability,
  connectivity, and the corresponding request logs.
- For persistence errors, investigate Redis availability and readiness.
- For repeated session conflicts, investigate concurrent writers to the same
  session before retrying.

### Confirm recovery

Confirm that new streams no longer add failed observations and that
scraping remains healthy.

The alert can remain firing after the underlying problem is fixed while
the observed increase remains in the rolling five-minute window. It should
become inactive after that increase leaves the window.

Failures before the first collected sample, or changes lost between scrapes
during a process restart, may not be detected.

## Slow first content

Alert: `FrankAIAgentChatStreamFirstContentSlow`

Both conditions must hold at every rule evaluation for five minutes:

- Job-wide first-content P95 is greater than 5 seconds.
- The estimated first-content observation increase over five minutes is
  at least 10.

The observation threshold uses Prometheus `increase()` and is an estimate.

This metric measures serializer iteration start until the first content
delta is successfully serialized. It excludes request processing before
iteration, network delivery, and browser rendering.

### Check

Inspect the job-wide P95 using the alert's fixed five-minute window:

```promql
histogram_quantile(
  0.95,
  sum by (job, le) (
    rate(frank_ai_agent_chat_stream_first_content_duration_seconds_bucket{job="frank-ai-agent"}[5m])
  )
)
```

Inspect the estimated observation increase:

```promql
sum by (job) (
  increase(frank_ai_agent_chat_stream_first_content_duration_seconds_count{job="frank-ai-agent"}[5m])
)
```

To investigate differences between instances:

```promql
histogram_quantile(
  0.95,
  sum by (job, instance, le) (
    rate(frank_ai_agent_chat_stream_first_content_duration_seconds_bucket{job="frank-ai-agent"}[5m])
  )
)
```

Compare latency with active serializer iterations:

```promql
sum(frank_ai_agent_chat_streams_active{job="frank-ai-agent"})
```

The active gauge reflects scrape snapshots and may miss short-lived
iterations.

Inspect resource usage and recent API logs:

```powershell
docker stats --no-stream
docker compose logs --since 15m --tail 200 api
```

### Respond

- Investigate resource pressure, provider latency, and work performed during
  iteration before the first content delta.
- Compare affected periods with traffic changes and recent deployments.
- Investigate slow instances individually even when the job-wide value
  recovers. High-volume normal traffic can mask a low-volume slow instance.
- Adjust thresholds in `monitoring/alerts.yml` only after reviewing expected
  traffic and latency.

### Confirm recovery

With representative traffic, confirm that the job-wide P95 falls below the
threshold and the alert becomes inactive.

An inactive alert can also result from insufficient observations or missing
metrics. Check observation volume and scrape health before declaring that
latency has recovered.

The rule handles counter resets per series before aggregation. A process
restart alone is not evidence that the latency problem is fixed.
