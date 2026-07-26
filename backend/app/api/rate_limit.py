"""Central, role-aware HTTP throttling built on TITAN's existing limiter primitive."""

from __future__ import annotations

from collections.abc import Mapping

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import Settings
from app.core.logging import get_logger
from app.modules.infrastructure.throttling import LocalRateLimiter

logger = get_logger(__name__)


class ApiRateLimitMiddleware(BaseHTTPMiddleware):
    """Apply the configured per-role request budget to all public v1 API routes.

    The limiter intentionally uses the existing local infrastructure primitive.
    It provides deterministic in-process protection and preserves the current
    deployment behaviour; a shared distributed policy remains a deployment
    concern for a future Redis-backed limiter implementation.
    """

    def __init__(self, app: object, *, settings: Settings) -> None:
        super().__init__(app)
        self._api_prefix = settings.api_v1_prefix.rstrip("/")
        self._limits = settings.api_rate_limits_per_minute
        self._limiters = {
            role: LocalRateLimiter(limit=limit) for role, limit in self._limits.items()
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Reject an over-budget request before it reaches a public route handler."""
        if request.method == "OPTIONS" or not request.url.path.startswith(f"{self._api_prefix}/"):
            return await call_next(request)

        role, subject = self._request_identity(request)
        limiter = self._limiters[role]
        if limiter.allow(f"{role}:{subject}"):
            return await call_next(request)

        metrics = getattr(request.app.state, "metrics", None)
        if metrics is not None:
            metrics.observe_infrastructure("api_rate_limited")
        logger.warning(
            "api.rate_limit_exceeded",
            extra={
                "extra_fields": {
                    "path": request.url.path,
                    "role": role,
                    "subject": subject,
                    "request_id": getattr(request.state, "request_id", None),
                    "result": "rate_limited",
                }
            },
        )
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "rate_limit_exceeded",
                    "message": "The request rate limit has been exceeded.",
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
            headers={"Retry-After": "60"},
        )

    def _request_identity(self, request: Request) -> tuple[str, str]:
        """Choose the most permissive assigned role without changing authorization rules."""
        principal = getattr(request.state, "principal", None)
        if principal is None:
            return "anonymous", request.client.host if request.client else "unknown"

        assigned_roles = [role.value for role in principal.roles if role.value in self._limits]
        role = max(assigned_roles, key=self._limits.__getitem__, default="anonymous")
        return role, principal.subject


def role_rate_limit_documentation(limits: Mapping[str, int]) -> str:
    """Build a low-maintenance OpenAPI description of the active role policy."""
    limits_text = ", ".join(f"{role}: {limit}/min" for role, limit in sorted(limits.items()))
    return f"Role-aware rate limits are centrally enforced ({limits_text})."
