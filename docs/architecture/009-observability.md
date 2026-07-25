# Observability

## Endpoints

- `GET /health` is liveness only: the process can receive HTTP requests.
- `GET /ready` performs bounded PostgreSQL and Redis pings. It returns `200` only when both are ready and `503` with dependency states otherwise. Error internals are never returned.
- `/metrics` exposes application Prometheus metrics when `TITAN_METRICS_ENABLED=true`.

## Correlation and trace propagation

Every request receives a validated UUID `X-Request-ID`. TITAN accepts a valid W3C `traceparent`; otherwise it creates a trace ID. Responses include `X-Request-ID`, `X-Trace-ID`, and a child `traceparent`. Structured JSON logs automatically include both identifiers.

## Metric catalogue

| Metric | Labels | Meaning |
|---|---|---|
| `titan_http_requests_total` | method, path, status_code | Completed HTTP requests. |
| `titan_http_request_duration_seconds` | method, path, status_code | HTTP latency histogram. |
| `titan_readiness_checks_total` | dependency, state | Database/Redis readiness results. |
| `titan_readiness_check_duration_seconds` | dependency | Dependency ping latency. |
| `titan_ingestion_batches_total` | context, provider, outcome | Completed provider batches. |
| `titan_ingestion_records_total` | context, provider, outcome | Received and validation-failed records. |
| `titan_ingestion_validation_failures_total` | context, provider | Rejected records. |
| `titan_provider_last_success_unixtime` | context, provider | Timestamp of latest batch with an accepted record; freshness is `time() - value`. |
| `titan_outbox_claimed_total` | context | Events leased by the worker. |
| `titan_outbox_delivered_total` | context | Events acknowledged by the worker. |
| `titan_outbox_retried_total` | context | Events scheduled for another delivery attempt. |
| `titan_outbox_dead_lettered_total` | context | Events that exhausted retries. |
| `titan_outbox_lease_conflicts_total` | context | Stale-worker acknowledgement/failure attempts. |
| `titan_outbox_pending` | context | Rows claimed during the latest poll. |

Labels are intentionally bounded. Provider names originate from registered adapters; API paths use route templates rather than raw URLs; no payload, credential, subject, or fixture identifiers are metric labels.
