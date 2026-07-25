"""Unauthenticated liveness and dependency-readiness endpoints."""

from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

router = APIRouter(tags=["System"])


class HealthResponse(BaseModel):
    """Stable liveness response contract."""

    status: str


class ReadinessResponse(BaseModel):
    """Dependency readiness result safe for container orchestrators and monitoring."""

    status: Literal["ready", "not_ready"]
    checks: dict[str, Literal["ready", "not_ready"]]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Confirm that the API process is able to receive requests.

    This is deliberately a liveness endpoint. Dependency readiness is monitored
    separately so an infrastructure outage does not prevent diagnostics.
    """
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(request: Request, response: Response) -> ReadinessResponse:
    """Verify PostgreSQL and Redis connectivity without exposing error internals."""
    timeout_seconds = request.app.state.settings.readiness_timeout_seconds

    async def check(name: str, operation: object) -> tuple[str, bool, float]:
        started = perf_counter()
        try:
            await asyncio.wait_for(operation, timeout=timeout_seconds)  # type: ignore[arg-type]
            return name, True, perf_counter() - started
        except Exception:
            return name, False, perf_counter() - started

    database = request.app.state.database
    redis = request.app.state.redis
    results = await asyncio.gather(check("database", database.ping()), check("redis", redis.ping()))
    metrics = getattr(request.app.state, "metrics", None)
    checks: dict[str, Literal["ready", "not_ready"]] = {}
    for name, healthy, duration in results:
        checks[name] = "ready" if healthy else "not_ready"
        if metrics is not None:
            metrics.observe_readiness(name, healthy, duration)
    is_ready = all(value == "ready" for value in checks.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="ready" if is_ready else "not_ready", checks=checks)
