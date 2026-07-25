"""Provider-neutral authentication contracts and local Development/JWT implementations."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from datetime import UTC, datetime
from hmac import compare_digest
from typing import TYPE_CHECKING, Any, Protocol

from app.modules.identity.models import Principal, Role

if TYPE_CHECKING:
    from app.core.config import DevelopmentIdentityCredential, Settings


class IdentityAuthenticationError(Exception):
    """Raised when a supplied credential cannot establish a verified principal."""


class IdentityProvider(Protocol):
    """Business modules rely exclusively on this provider-neutral boundary."""

    async def authenticate(self, credential: str) -> Principal: ...

    async def validate_token(self, credential: str) -> dict[str, Any]: ...

    async def get_user(self, principal: Principal) -> Principal: ...

    async def get_roles(self, principal: Principal) -> frozenset[Role]: ...

    async def get_permissions(self, principal: Principal): ...

    async def health(self) -> bool: ...


class DevelopmentIdentityProvider:
    """Constant-time development credential provider; never permitted in production."""

    def __init__(self, credentials: dict[str, DevelopmentIdentityCredential]) -> None:
        self._credentials = credentials

    async def authenticate(self, credential: str) -> Principal:
        claims = await self.validate_token(credential)
        try:
            return Principal(
                subject=str(claims["sub"]),
                organization_id=claims.get("organization_id"),
                roles=frozenset(Role(role) for role in claims["roles"]),
                provider="development",
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IdentityAuthenticationError("Development credential has invalid claims.") from exc

    async def validate_token(self, credential: str) -> dict[str, Any]:
        """Resolve configured development token claims without logging the credential."""
        for token, raw_identity in self._credentials.items():
            if compare_digest(token, credential):
                return {
                    "sub": raw_identity.subject,
                    "organization_id": raw_identity.organization_id,
                    "roles": raw_identity.roles,
                }
        raise IdentityAuthenticationError("Bearer credential is invalid.")

    async def get_user(self, principal: Principal) -> Principal:
        return principal

    async def get_roles(self, principal: Principal) -> frozenset[Role]:
        return principal.roles

    async def get_permissions(self, principal: Principal):
        return principal.permissions

    async def health(self) -> bool:
        return True


class JwtIdentityProvider:
    """Strict local HS256 JWT validator for future OIDC/JWT integrations."""

    def __init__(
        self, *, issuer: str, audience: str, secret: str, clock_skew_seconds: int
    ) -> None:
        self._issuer = issuer
        self._audience = audience
        self._secret = secret.encode("utf-8")
        self._clock_skew_seconds = clock_skew_seconds

    async def authenticate(self, credential: str) -> Principal:
        claims = await self.validate_token(credential)
        roles = claims.get("roles", [])
        if not isinstance(roles, list):
            raise IdentityAuthenticationError("JWT roles claim must be an array.")
        try:
            return Principal(
                subject=str(claims["sub"]),
                organization_id=claims.get("organization_id"),
                roles=frozenset(Role(role) for role in roles),
                provider="jwt",
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IdentityAuthenticationError("JWT claims cannot form a TITAN principal.") from exc

    async def validate_token(self, credential: str) -> dict[str, Any]:
        """Verify signature, issuer, audience, expiration, and optional not-before claim."""
        header, claims, signature, signing_input = self._decode(credential)
        if header.get("alg") != "HS256" or header.get("typ") not in (None, "JWT"):
            raise IdentityAuthenticationError("JWT algorithm is not permitted.")
        expected = hmac.new(self._secret, signing_input, hashlib.sha256).digest()
        if not compare_digest(expected, signature):
            raise IdentityAuthenticationError("JWT signature is invalid.")
        if claims.get("iss") != self._issuer:
            raise IdentityAuthenticationError("JWT issuer is invalid.")
        audience = claims.get("aud")
        audiences = audience if isinstance(audience, list) else [audience]
        if self._audience not in audiences:
            raise IdentityAuthenticationError("JWT audience is invalid.")
        now = datetime.now(UTC).timestamp()
        skew = self._clock_skew_seconds
        if not isinstance(claims.get("exp"), (int, float)) or claims["exp"] + skew < now:
            raise IdentityAuthenticationError("JWT has expired.")
        if isinstance(claims.get("nbf"), (int, float)) and claims["nbf"] - skew > now:
            raise IdentityAuthenticationError("JWT is not active yet.")
        return claims

    @staticmethod
    def _decode(credential: str) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
        parts = credential.split(".")
        if len(parts) != 3:
            raise IdentityAuthenticationError("JWT must contain three segments.")
        try:
            header = json.loads(JwtIdentityProvider._b64decode(parts[0]))
            claims = json.loads(JwtIdentityProvider._b64decode(parts[1]))
            signature = JwtIdentityProvider._b64decode(parts[2])
        except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise IdentityAuthenticationError("JWT encoding is invalid.") from exc
        if not isinstance(header, dict) or not isinstance(claims, dict):
            raise IdentityAuthenticationError("JWT header and claims must be objects.")
        return header, claims, signature, f"{parts[0]}.{parts[1]}".encode("ascii")

    @staticmethod
    def _b64decode(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    async def get_user(self, principal: Principal) -> Principal:
        return principal

    async def get_roles(self, principal: Principal) -> frozenset[Role]:
        return principal.roles

    async def get_permissions(self, principal: Principal):
        return principal.permissions

    async def health(self) -> bool:
        return True


class IdentityProviderRegistry:
    """Composition-root registry allowing new providers without business-module changes."""

    def build(self, settings: Settings) -> IdentityProvider:
        if settings.identity_provider == "development":
            return DevelopmentIdentityProvider(settings.development_identity_credentials)
        if settings.identity_provider == "jwt":
            if (
                not settings.jwt_issuer
                or not settings.jwt_audience
                or settings.jwt_hs256_secret is None
            ):
                raise RuntimeError(
                    "JWT provider requires issuer, audience, and HS256 secret settings."
                )
            return JwtIdentityProvider(
                issuer=settings.jwt_issuer,
                audience=settings.jwt_audience,
                secret=settings.jwt_hs256_secret.get_secret_value(),
                clock_skew_seconds=settings.jwt_clock_skew_seconds,
            )
        raise RuntimeError(f"Identity provider '{settings.identity_provider}' is not installed.")


def build_identity_provider(settings: Settings) -> IdentityProvider:
    """Build the configured provider at the application composition boundary."""
    return IdentityProviderRegistry().build(settings)
