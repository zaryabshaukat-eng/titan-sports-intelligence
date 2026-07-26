"""Backward-compatible opt-in v1 response envelopes for SDK consumers."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class ApiEnvelopeMiddleware(BaseHTTPMiddleware):
    """Wrap JSON success bodies only when callers explicitly opt in.

    Existing v1 callers receive their historical response shape unchanged.
    Clients sending ``X-TITAN-Response-Envelope: v1`` receive a stable SDK
    contract containing data, request metadata, request ID, and timestamp.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if (
            not request.url.path.startswith("/api/v1/")
            or request.headers.get("X-TITAN-Response-Envelope") != "v1"
            or response.status_code >= 300
            or "application/json" not in response.headers.get("content-type", "")
        ):
            return response
        body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return response
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return JSONResponse(
            {
                "data": data,
                "metadata": {},
                "request_id": getattr(request.state, "request_id", None),
                "api_version": "v1",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            status_code=response.status_code,
            headers=headers,
        )
