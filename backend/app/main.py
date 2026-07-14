"""FastAPI application factory and infrastructure lifecycle for TITAN Core."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.health import router as health_router
from app.api.v1.router import router as api_v1_router
from app.core.config import Settings, get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware, RequestLoggingMiddleware
from app.core.observability import create_metrics
from app.core.security import SecurityHeadersMiddleware
from app.shared.persistence.database import DatabaseSessionManager
from app.shared.redis import RedisClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create and dispose process-level clients without hiding dependency failures."""
    settings: Settings = app.state.settings
    app.state.database = DatabaseSessionManager(settings.database_url)
    app.state.redis = RedisClient(settings.redis_url)
    app.state.token_verifier = None

    try:
        yield
    finally:
        await app.state.redis.close()
        await app.state.database.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a configured TITAN Core application instance.

    Accepting settings enables isolated tests and makes deployment configuration
    explicit at the application composition boundary.
    """
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    app = FastAPI(
        title="TITAN Core API",
        summary="Backend foundation for the TITAN Sports Intelligence Operating System.",
        version="0.1.0",
        docs_url="/docs" if resolved_settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json",
        openapi_tags=[
            {
                "name": "System",
                "description": "Platform liveness and operational endpoints.",
            }
        ],
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.metrics = None

    if resolved_settings.metrics_enabled:
        metrics, metrics_app = create_metrics()
        app.state.metrics = metrics
        app.mount("/metrics", metrics_app)

    # Middleware is applied in reverse registration order. Request ID is added
    # last so correlation is available to all remaining middleware and handlers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=resolved_settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )
    if resolved_settings.trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=resolved_settings.trusted_hosts)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    install_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=resolved_settings.api_v1_prefix)
    return app


app = create_app()
