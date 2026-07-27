"""Identity-provider, role, permission, and authentication-middleware coverage."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.config import AppEnvironment, DevelopmentIdentityCredential, Settings
from app.main import create_app
from app.modules.identity.models import Permission, Role
from app.modules.identity.providers import (
    DevelopmentIdentityProvider,
    IdentityAuthenticationError,
    IdentityProviderRegistry,
    JwtIdentityProvider,
)


def _jwt(secret: str, claims: dict[str, object]) -> str:
    """Create a test-only HS256 token without adding a JWT runtime dependency."""

    def encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    header = encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8"))
    payload = encode(json.dumps(claims).encode("utf-8"))
    signature = hmac.new(
        secret.encode("utf-8"), f"{header}.{payload}".encode("ascii"), hashlib.sha256
    ).digest()
    return f"{header}.{payload}.{encode(signature)}"


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


def test_security_headers_are_applied_to_public_responses() -> None:
    """Baseline browser protections apply independently of route authentication."""
    settings = Settings(_env_file=None, app_env=AppEnvironment.TESTING)
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == "geolocation=(), microphone=(), camera=()"


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


def test_jwt_provider_validates_signature_claims_and_normalizes_roles() -> None:
    async def run() -> None:
        now = datetime.now(UTC)
        provider = JwtIdentityProvider(
            issuer="https://identity.example.test",
            audience="titan-core",
            secret="test-secret",
            clock_skew_seconds=0,
        )
        token = _jwt(
            "test-secret",
            {
                "sub": "researcher-1",
                "iss": "https://identity.example.test",
                "aud": "titan-core",
                "exp": (now + timedelta(minutes=5)).timestamp(),
                "roles": ["researcher"],
            },
        )

        principal = await provider.authenticate(token)

        assert principal.provider == "jwt"
        assert principal.roles == frozenset({Role.RESEARCHER})
        assert principal.permits(Permission.RESEARCH_EXECUTE)
        assert await provider.health() is True

    asyncio.run(run())


def test_jwt_provider_rejects_an_invalid_signature() -> None:
    async def run() -> None:
        provider = JwtIdentityProvider(
            issuer="issuer", audience="audience", secret="trusted", clock_skew_seconds=0
        )
        token = _jwt(
            "untrusted",
            {
                "sub": "attacker",
                "iss": "issuer",
                "aud": "audience",
                "exp": (datetime.now(UTC) + timedelta(minutes=5)).timestamp(),
                "roles": ["viewer"],
            },
        )
        try:
            await provider.authenticate(token)
        except IdentityAuthenticationError:
            return
        raise AssertionError("Invalid JWT signatures must be rejected.")

    asyncio.run(run())


def test_provider_registry_builds_jwt_from_environment_backed_settings() -> None:
    settings = Settings(
        _env_file=None,
        identity_provider="jwt",
        jwt_issuer="issuer",
        jwt_audience="audience",
        jwt_hs256_secret="test-secret",
    )

    assert isinstance(IdentityProviderRegistry().build(settings), JwtIdentityProvider)
