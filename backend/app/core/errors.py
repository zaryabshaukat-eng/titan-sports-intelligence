"""Consistent, correlation-aware error responses for the public API."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger, request_id_context

logger = get_logger(__name__)


def _error_response(
    status_code: int, code: str, message: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    """Return the shared error envelope without exposing implementation details."""
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id_context.get(),
        }
    }
    return JSONResponse(status_code=status_code, content=payload, headers=headers)


def install_exception_handlers(app: FastAPI) -> None:
    """Register API-safe handlers for expected and unexpected failures."""

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        code = str(detail.get("code", "http_error"))
        message = str(
            detail.get("message", exc.detail if isinstance(exc.detail, str) else "Request failed.")
        )
        return _error_response(exc.status_code, code, message, dict(exc.headers or {}))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "The request could not be validated.",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "request.unhandled_exception",
            extra={"extra_fields": {"method": request.method, "path": request.url.path}},
        )
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_server_error",
            "An unexpected server error occurred.",
        )
