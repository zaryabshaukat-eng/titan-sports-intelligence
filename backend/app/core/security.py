"""Authentication middleware, provider-neutral principal resolution, and authorization guards."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.logging import get_logger
from app.modules.identity.models import Permission, Principal
from app.modules.identity.providers import IdentityAuthenticationError, IdentityProvider

bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
logger = get_logger(__name__)


def _authentication_error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authenticate supplied bearer credentials once per request and store the principal."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        header = request.headers.get("Authorization")
        if header is None:
            return await call_next(request)
        scheme, _, credential = header.partition(" ")
        if scheme.lower() != "bearer" or not credential:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": {
                        "code": "authentication_invalid",
                        "message": "Invalid bearer credential.",
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        provider: IdentityProvider | None = getattr(request.app.state, "identity_provider", None)
        if provider is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": {
                        "code": "authentication_not_configured",
                        "message": "Authentication is unavailable.",
                    }
                },
            )
        try:
            request.state.principal = await provider.authenticate(credential)
        except IdentityAuthenticationError:
            metrics = getattr(request.app.state, "metrics", None)
            if metrics is not None:
                metrics.observe_authentication_failure(request.app.state.settings.identity_provider)
            logger.warning(
                "identity.authentication_failed",
                extra={
                    "extra_fields": {
                        "provider": request.app.state.settings.identity_provider,
                        "endpoint": request.url.path,
                        "outcome": "invalid",
                    }
                },
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": {
                        "code": "authentication_invalid",
                        "message": "Invalid bearer credential.",
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        principal: Principal = request.state.principal
        logger.info(
            "identity.authentication_succeeded",
            extra={
                "extra_fields": {
                    "subject": principal.subject,
                    "provider": principal.provider,
                    "roles": sorted(role.value for role in principal.roles),
                    "permissions": sorted(permission.value for permission in principal.permissions),
                    "endpoint": request.url.path,
                    "outcome": "authenticated",
                }
            },
        )
        return await call_next(request)


async def require_authenticated_principal(
    request: Request,
    credentials: BearerCredentials,
) -> Principal:
    """Require the middleware-verified principal while preserving OpenAPI bearer security."""
    if credentials is None:
        raise _authentication_error(
            "authentication_required",
            "Bearer authentication is required.",
            status.HTTP_401_UNAUTHORIZED,
        )
    principal: Principal | None = getattr(request.state, "principal", None)
    if principal is not None:
        return principal
    provider: IdentityProvider | None = getattr(request.app.state, "identity_provider", None)
    if provider is None:
        raise _authentication_error(
            "authentication_not_configured",
            "Authentication is unavailable.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    try:
        return await provider.authenticate(credentials.credentials)
    except IdentityAuthenticationError as exc:
        raise _authentication_error(
            "authentication_invalid", "Invalid bearer credential.", status.HTTP_401_UNAUTHORIZED
        ) from exc


def require_permissions(*permissions: Permission):
    """Build a dependency requiring all named permissions for an internal operation."""

    async def authorize(
        request: Request,
        principal: Annotated[Principal, Depends(require_authenticated_principal)],
    ) -> Principal:
        if not principal.permits(*permissions):
            metrics = getattr(request.app.state, "metrics", None)
            if metrics is not None:
                for permission in permissions:
                    metrics.observe_authorization_failure(permission.value)
            logger.warning(
                "identity.authorization_denied",
                extra={
                    "extra_fields": {
                        "subject": principal.subject,
                        "provider": principal.provider,
                        "roles": sorted(role.value for role in principal.roles),
                        "required_permissions": [permission.value for permission in permissions],
                        "outcome": "forbidden",
                    }
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "authorization_denied",
                    "message": "The authenticated principal lacks the required permission.",
                    "required_permissions": [permission.value for permission in permissions],
                },
            )
        return principal

    return authorize


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply baseline browser security headers to every HTTP response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response
