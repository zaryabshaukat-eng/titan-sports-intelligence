"""Application-local Prometheus metrics used by request middleware."""

from __future__ import annotations

from dataclasses import dataclass

from prometheus_client import CollectorRegistry, Counter, Histogram, make_asgi_app
from starlette.types import ASGIApp


@dataclass(slots=True)
class ApplicationMetrics:
    """Per-application metric collectors, avoiding global registry collisions in tests."""

    request_count: Counter
    request_duration_seconds: Histogram

    def observe_request(
        self, method: str, path: str, status_code: int, duration_seconds: float
    ) -> None:
        """Record a completed HTTP request."""
        labels = {"method": method, "path": path, "status_code": str(status_code)}
        self.request_count.labels(**labels).inc()
        self.request_duration_seconds.labels(**labels).observe(duration_seconds)


def create_metrics() -> tuple[ApplicationMetrics, ASGIApp]:
    """Create isolated collectors and the matching ASGI metrics endpoint."""
    registry = CollectorRegistry(auto_describe=True)
    metrics = ApplicationMetrics(
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
    )
    return metrics, make_asgi_app(registry=registry)
