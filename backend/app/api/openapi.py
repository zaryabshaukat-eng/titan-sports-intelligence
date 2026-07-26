"""Central OpenAPI contract normalization for backward-compatible v1 endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from app.api.rate_limit import role_rate_limit_documentation
from app.core.config import Settings

_STANDARD_ERROR_CODES = {
    "401": "AuthenticationError",
    "403": "AuthorizationError",
    "422": "ValidationError",
    "429": "RateLimitError",
    "500": "InternalError",
}


def install_openapi_contracts(app: FastAPI, settings: Settings) -> None:
    """Document shared v1 guarantees without altering runtime request or response shapes."""

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            summary=app.summary,
            description=(
                "TITAN OS version 1 public API. Legacy response shapes remain the default; "
                "clients may opt in to the documented response envelope with "
                "`X-TITAN-Response-Envelope: v1`. "
                + role_rate_limit_documentation(settings.api_rate_limits_per_minute)
            ),
            routes=app.routes,
            tags=app.openapi_tags,
        )
        components = schema.setdefault("components", {})
        components.setdefault("schemas", {})["ApiError"] = {
            "type": "object",
            "required": ["error"],
            "properties": {
                "error": {
                    "type": "object",
                    "required": ["code", "message", "request_id"],
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "request_id": {"type": "string", "nullable": True},
                    },
                }
            },
        }
        responses = components.setdefault("responses", {})
        for _status_code, name in _STANDARD_ERROR_CODES.items():
            responses.setdefault(
                name,
                {
                    "description": "Standard TITAN API error response.",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/ApiError"}}
                    },
                },
            )

        permission_map = _route_permission_map(app)
        for path, path_item in schema.get("paths", {}).items():
            if not path.startswith(f"{settings.api_v1_prefix}/"):
                continue
            for method, operation in path_item.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                operation.setdefault("summary", f"{method.upper()} {path}")
                operation.setdefault(
                    "description",
                    "Versioned public TITAN API operation with centralized authentication, "
                    "authorization, validation, and error handling.",
                )
                permissions = permission_map.get((path, method), ())
                if permissions:
                    operation["x-titan-authentication"] = "bearer-required"
                    operation["x-titan-authorization"] = {"required_permissions": list(permissions)}
                else:
                    operation["x-titan-authentication"] = "anonymous"
                    operation["x-titan-authorization"] = {"required_permissions": []}
                operation.setdefault("x-titan-response-envelope", "opt-in-v1")
                operation_responses = operation.setdefault("responses", {})
                for status_code, name in _STANDARD_ERROR_CODES.items():
                    operation_responses.setdefault(
                        status_code, {"$ref": f"#/components/responses/{name}"}
                    )
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi


def _route_permission_map(app: FastAPI) -> dict[tuple[str, str], tuple[str, ...]]:
    """Extract permission metadata from existing guards without changing authorization behavior."""
    result: dict[tuple[str, str], tuple[str, ...]] = {}
    for route in app.routes:
        if isinstance(route, APIRoute):
            _add_route_permissions(result, route.path, route.methods, route.dependant)
            continue
        # FastAPI 0.115+ retains nested routers as lazy included-router nodes.
        # Its public schema is already flattened; inspect the matching effective
        # contexts so permission metadata uses the same fully prefixed paths.
        contexts = getattr(route, "effective_route_contexts", None)
        if contexts is None:
            continue
        for context in contexts():
            if context.dependant is not None:
                _add_route_permissions(
                    result, context.path_format, context.methods, context.dependant
                )
    return result


def _add_route_permissions(
    target: dict[tuple[str, str], tuple[str, ...]],
    path: str,
    methods: set[str] | None,
    dependant: Dependant,
) -> None:
    """Record one effective route's inherited guard requirements."""
    permissions = tuple(sorted(_permissions_for_dependant(dependant)))
    for method in methods or set():
        target[(path, method.lower())] = permissions


def _permissions_for_dependant(dependant: Dependant) -> set[str]:
    """Traverse FastAPI dependencies to find metadata attached by permission guards."""
    permissions: set[str] = set()
    required = getattr(dependant.call, "required_permissions", ())
    permissions.update(permission.value for permission in required)
    for dependency in dependant.dependencies:
        permissions.update(_permissions_for_dependant(dependency))
    return permissions
