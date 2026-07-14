"""Authentication extension points and HTTP security middleware."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Protocol

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


@dataclass(frozen=True, slots=True)
class Principal:
    """Verified caller identity exposed to protected future endpoints."""

    subject: str
    organization_id: str | None
    roles: frozenset[str]


class TokenVerifier(Protocol):
    """Contract implemented by a future identity-provider adapter."""

    async def verify(self, token: str) -> Principal:
        """Validate a bearer token and return a verified principal."""


bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


async def require_authenticated_principal(
    request: Request,
    credentials: BearerCredentials,
) -> Principal:
    """Fail closed until a real identity provider is configured.

    This is intentionally an extension point, not login or token-validation logic.
    Future protected routes depend on this function instead of inspecting raw headers.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "authentication_required",
                "message": "Bearer authentication is required.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    verifier: TokenVerifier | None = getattr(request.app.state, "token_verifier", None)
    if verifier is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "authentication_not_configured",
                "message": "Authentication is unavailable.",
            },
        )

    return await verifier.verify(credentials.credentials)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply baseline browser security headers to every HTTP response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Add headers after the downstream application has prepared its response."""
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response
