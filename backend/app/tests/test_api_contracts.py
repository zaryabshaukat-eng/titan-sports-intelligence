"""Cross-cutting public v1 API contract assertions for the Phase 2.14 boundary."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_public_v1_operations_publish_common_openapi_contracts() -> None:
    """Every public operation documents its endpoint purpose and standard errors."""
    app = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING))
    schema = app.openapi()

    for path, path_item in schema["paths"].items():
        if not path.startswith("/api/v1/"):
            continue
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            assert operation["summary"]
            assert operation["description"]
            assert operation["x-titan-response-envelope"] == "opt-in-v1"
            assert operation["x-titan-authentication"] in {"anonymous", "bearer-required"}
            assert "required_permissions" in operation["x-titan-authorization"]
            for status_code in ("401", "403", "422", "429", "500"):
                assert status_code in operation["responses"]


def test_rate_limit_is_applied_by_authenticated_role() -> None:
    """A role-specific budget is centrally enforced before a protected handler runs."""
    settings = Settings(
        _env_file=None,
        app_env=AppEnvironment.TESTING,
        api_rate_limit_viewer_per_minute=1,
        development_identity_credentials={
            "viewer-token": {"subject": "viewer", "roles": ["viewer"]}
        },
    )
    with TestClient(create_app(settings)) as client:
        first = client.get(
            "/api/v1/infrastructure/health", headers={"Authorization": "Bearer viewer-token"}
        )
        second = client.get(
            "/api/v1/infrastructure/health", headers={"Authorization": "Bearer viewer-token"}
        )

    assert first.status_code in {200, 503}
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limit_exceeded"
    assert second.headers["Retry-After"] == "60"


def test_openapi_declares_exact_permission_requirements_for_protected_routes() -> None:
    """Authorization documentation comes from existing guards, not duplicate route policy."""
    schema = create_app(Settings(_env_file=None, app_env=AppEnvironment.TESTING)).openapi()

    ingestion = schema["paths"]["/api/v1/ingestion/fixtures/{provider_name}"]["post"]
    sports = schema["paths"]["/api/v1/sports/countries"]["get"]

    assert ingestion["x-titan-authentication"] == "bearer-required"
    assert ingestion["x-titan-authorization"] == {"required_permissions": ["fixtures:ingest"]}
    assert sports["x-titan-authentication"] == "anonymous"
    assert sports["x-titan-authorization"] == {"required_permissions": []}
