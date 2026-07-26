"""Application-local Prometheus metrics used by request middleware."""

from __future__ import annotations

from dataclasses import dataclass
from time import time

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, make_asgi_app
from starlette.types import ASGIApp


@dataclass(slots=True)
class ApplicationMetrics:
    """Per-application metric collectors, avoiding global registry collisions in tests."""

    registry: CollectorRegistry
    request_count: Counter
    request_duration_seconds: Histogram
    readiness_checks: Counter
    readiness_duration_seconds: Histogram
    ingestion_batches: Counter
    ingestion_records: Counter
    validation_failures: Counter
    provider_last_success_unixtime: Gauge
    authentication_failures: Counter
    authorization_failures: Counter
    outbox_backlog: Gauge
    slow_requests: Counter
    infrastructure_events: Counter

    def observe_request(
        self, method: str, path: str, status_code: int, duration_seconds: float
    ) -> None:
        """Record a completed HTTP request."""
        labels = {"method": method, "path": path, "status_code": str(status_code)}
        self.request_count.labels(**labels).inc()
        self.request_duration_seconds.labels(**labels).observe(duration_seconds)

    def observe_readiness(self, dependency: str, healthy: bool, duration_seconds: float) -> None:
        """Record a bounded database or Redis readiness result."""
        state = "ready" if healthy else "not_ready"
        self.readiness_checks.labels(dependency=dependency, state=state).inc()
        self.readiness_duration_seconds.labels(dependency=dependency).observe(duration_seconds)

    def observe_ingestion(self, context: str, provider: str, received: int, failed: int) -> None:
        """Record batch/record outcomes and successful provider-contact time."""
        outcome = "completed_with_errors" if failed else "completed"
        self.ingestion_batches.labels(context=context, provider=provider, outcome=outcome).inc()
        self.ingestion_records.labels(context=context, provider=provider, outcome="received").inc(
            received
        )
        if failed:
            self.ingestion_records.labels(
                context=context, provider=provider, outcome="validation_failed"
            ).inc(failed)
            self.validation_failures.labels(context=context, provider=provider).inc(failed)
        if received > failed:
            self.provider_last_success_unixtime.labels(context=context, provider=provider).set(
                time()
            )

    def observe_authentication_failure(self, provider: str) -> None:
        self.authentication_failures.labels(provider=provider).inc()

    def observe_authorization_failure(self, permission: str) -> None:
        self.authorization_failures.labels(permission=permission).inc()

    def observe_outbox_backlog(self, context: str, count: int) -> None:
        self.outbox_backlog.labels(context=context).set(count)

    def observe_slow_request(self, path: str) -> None:
        self.slow_requests.labels(path=path).inc()

    def observe_infrastructure(self, event: str, amount: int = 1) -> None:
        self.infrastructure_events.labels(event=event).inc(amount)


def create_metrics() -> tuple[ApplicationMetrics, ASGIApp]:
    """Create isolated collectors and the matching ASGI metrics endpoint."""
    registry = CollectorRegistry(auto_describe=True)
    metrics = ApplicationMetrics(
        registry=registry,
        request_count=Counter(
            "titan_http_requests_total",
            "Completed TITAN Core HTTP requests.",
            labelnames=("method", "path", "status_code"),
            registry=registry,
        ),
        request_duration_seconds=Histogram(
            "titan_http_request_duration_seconds",
            "TITAN Core HTTP request duration in seconds.",
            labelnames=("method", "path", "status_code"),
            registry=registry,
        ),
        readiness_checks=Counter(
            "titan_readiness_checks_total",
            "Readiness dependency checks by result.",
            labelnames=("dependency", "state"),
            registry=registry,
        ),
        readiness_duration_seconds=Histogram(
            "titan_readiness_check_duration_seconds",
            "Readiness dependency check duration.",
            labelnames=("dependency",),
            registry=registry,
        ),
        ingestion_batches=Counter(
            "titan_ingestion_batches_total",
            "Completed provider ingestion batches.",
            labelnames=("context", "provider", "outcome"),
            registry=registry,
        ),
        ingestion_records=Counter(
            "titan_ingestion_records_total",
            "Provider ingestion records by outcome.",
            labelnames=("context", "provider", "outcome"),
            registry=registry,
        ),
        validation_failures=Counter(
            "titan_ingestion_validation_failures_total",
            "Provider records rejected by validation or safe resolution.",
            labelnames=("context", "provider"),
            registry=registry,
        ),
        provider_last_success_unixtime=Gauge(
            "titan_provider_last_success_unixtime",
            "Unix time of the latest ingestion batch with at least one accepted record.",
            labelnames=("context", "provider"),
            registry=registry,
        ),
        authentication_failures=Counter(
            "titan_authentication_failures_total",
            "Rejected authentication attempts.",
            labelnames=("provider",),
            registry=registry,
        ),
        authorization_failures=Counter(
            "titan_authorization_failures_total",
            "Permission-denied authorization attempts.",
            labelnames=("permission",),
            registry=registry,
        ),
        outbox_backlog=Gauge(
            "titan_outbox_backlog",
            "Unpublished, non-dead-lettered outbox events.",
            labelnames=("context",),
            registry=registry,
        ),
        slow_requests=Counter(
            "titan_slow_requests_total",
            "HTTP requests exceeding the configured slow-request threshold.",
            labelnames=("path",),
            registry=registry,
        ),
        infrastructure_events=Counter(
            "titan_infrastructure_events_total",
            "Infrastructure cache, lock, queue, worker, scheduler, and throttle events.",
            labelnames=("event",),
            registry=registry,
        ),
    )
    return metrics, make_asgi_app(registry=registry)
