"""Identity-provider, role, permission, and authentication-middleware coverage."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.core.config import AppEnvironment, DevelopmentIdentityCredential, Settings
from app.main import create_app
from app.modules.identity.models import Permission, Role
from app.modules.identity.providers import (
    DevelopmentIdentityProvider,
    IdentityAuthenticationError,
)


def test_development_provider_normalizes_roles_and_permissions() -> None:
    async def run() -> None:
        provider = DevelopmentIdentityProvider(
            {
                "analyst-token": DevelopmentIdentityCredential(
                    subject="analyst-1", organization_id="titan", roles=[Role.ANALYST]
                )
            }
        )
        principal = await provider.authenticate("analyst-token")

        assert principal.subject == "analyst-1"
        assert principal.permits(Permission.DATA_READ)
        assert not principal.permits(Permission.FIXTURE_INGEST)

    asyncio.run(run())


def test_development_provider_rejects_unknown_credentials() -> None:
    async def run() -> None:
        provider = DevelopmentIdentityProvider({})
        try:
            await provider.authenticate("unknown")
        except IdentityAuthenticationError:
            return
        raise AssertionError("Unknown credentials must be rejected.")

    asyncio.run(run())


def test_authentication_middleware_rejects_invalid_bearer_before_route_execution() -> None:
    settings = Settings(_env_file=None, app_env=AppEnvironment.TESTING)
    with TestClient(create_app(settings)) as client:
        response = client.get("/health", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "authentication_invalid"


def test_development_credentials_are_configurable_from_settings() -> None:
    settings = Settings(
        _env_file=None,
        development_identity_credentials={
            "custom-token": {"subject": "custom", "roles": [Role.DATA_INGESTOR]}
        },
    )
    credential = settings.development_identity_credentials["custom-token"]

    assert credential.subject == "custom"
    assert credential.roles == [Role.DATA_INGESTOR]
