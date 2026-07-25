"""Readiness, trace propagation, and bounded Prometheus metric coverage."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from fastapi import Response
from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from app.api.health import readiness_check
from app.core.config import AppEnvironment, Settings
from app.core.observability import create_metrics
from app.main import create_app


class _ReadyDependency:
    async def ping(self) -> bool:
        return True

    async def outbox_backlog(self) -> dict[str, int]:
        return {"fixture_ingestion": 2, "market_data": 0, "statistics": 1}


class _FailedDependency:
    async def ping(self) -> bool:
        raise ConnectionError("unavailable")


class _ReadyIdentity:
    async def health(self) -> bool:
        return True


def test_readiness_reports_each_dependency_without_exposing_errors() -> None:
    async def run() -> None:
        metrics, _ = create_metrics()
        request = SimpleNamespace(
            app=SimpleNamespace(
                state=SimpleNamespace(
                    database=_ReadyDependency(),
                    redis=_FailedDependency(),
                    identity_provider=_ReadyIdentity(),
                    metrics=metrics,
                    settings=SimpleNamespace(readiness_timeout_seconds=0.1),
                )
            )
        )
        response = Response()

        result = await readiness_check(request, response)

        assert response.status_code == 503
        assert result.status == "not_ready"
        assert result.checks == {
            "database": "ready",
            "redis": "not_ready",
            "identity": "ready",
            "outbox": "ready",
        }
        assert result.outbox_backlog["fixture_ingestion"] == 2

    asyncio.run(run())


def test_request_trace_headers_propagate_valid_w3c_trace_id() -> None:
    trace_id = "a" * 32
    with TestClient(create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING))) as client:
        response = client.get("/health", headers={"traceparent": f"00-{trace_id}-{'b' * 16}-01"})

    assert response.status_code == 200
    assert response.headers["X-Trace-ID"] == trace_id
    assert response.headers["traceparent"].startswith(f"00-{trace_id}-")


def test_ingestion_metrics_capture_provider_success_and_validation_failures() -> None:
    metrics, _ = create_metrics()

    metrics.observe_ingestion("statistics", "provider-a", received=3, failed=1)
    exported = generate_latest(metrics.registry).decode()

    assert (
        "titan_ingestion_records_total{"
        'context="statistics",outcome="received",provider="provider-a"} 3.0' in exported
    )
    assert (
        'titan_ingestion_validation_failures_total{context="statistics",provider="provider-a"} 1.0'
        in exported
    )
    assert (
        'titan_provider_last_success_unixtime{context="statistics",provider="provider-a"}'
        in exported
    )


def test_operational_metrics_capture_authentication_and_outbox_signals() -> None:
    metrics, _ = create_metrics()

    metrics.observe_authentication_failure("development")
    metrics.observe_authorization_failure("fixtures:ingest")
    metrics.observe_outbox_backlog("statistics", 4)
    metrics.observe_slow_request("/health")
    exported = generate_latest(metrics.registry).decode()

    assert 'titan_authentication_failures_total{provider="development"} 1.0' in exported
    assert 'titan_authorization_failures_total{permission="fixtures:ingest"} 1.0' in exported
    assert 'titan_outbox_backlog{context="statistics"} 4.0' in exported
    assert 'titan_slow_requests_total{path="/health"} 1.0' in exported
