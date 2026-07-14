"""Request correlation and structured request logging middleware."""

from __future__ import annotations

from time import perf_counter
from uuid import UUID, uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.logging import get_logger, request_id_context

logger = get_logger(__name__)


def _request_id_from_header(value: str | None) -> str:
    """Accept only UUID request IDs to avoid reflecting arbitrary user input."""
    if value:
        try:
            return str(UUID(value))
        except ValueError:
            pass
    return str(uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a validated request ID to context, logs, and the response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Set the correlation context for the complete request lifecycle."""
        request_id = _request_id_from_header(request.headers.get("X-Request-ID"))
        token = request_id_context.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_context.reset(token)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log and measure completed requests without recording query or body data."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Capture duration, status, and low-cardinality route information."""
        started_at = perf_counter()
        response = await call_next(request)
        duration_seconds = perf_counter() - started_at
        path = request.scope.get("route")
        route_path = getattr(path, "path", request.url.path)

        metrics = getattr(request.app.state, "metrics", None)
        if metrics is not None:
            metrics.observe_request(
                request.method, route_path, response.status_code, duration_seconds
            )

        logger.info(
            "request.completed",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": route_path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_seconds * 1000, 2),
                }
            },
        )
        return response
