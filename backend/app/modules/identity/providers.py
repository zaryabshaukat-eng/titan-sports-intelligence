"""Pluggable identity-provider boundary and safe development provider."""

from __future__ import annotations

from hmac import compare_digest
from typing import TYPE_CHECKING, Protocol

from app.modules.identity.models import Principal, Role

if TYPE_CHECKING:
    from app.core.config import DevelopmentIdentityCredential, Settings


class IdentityAuthenticationError(Exception):
    """Raised when a supplied credential cannot establish a verified principal."""


class IdentityProvider(Protocol):
    """Future OAuth, SSO, service-account, or API-key providers implement this contract."""

    async def authenticate(self, credential: str) -> Principal:
        """Verify a bearer credential and return its normalized TITAN principal."""


class DevelopmentIdentityProvider:
    """Constant-time development credential provider; never permitted in production."""

    def __init__(self, credentials: dict[str, DevelopmentIdentityCredential]) -> None:
        self._credentials = credentials

    async def authenticate(self, credential: str) -> Principal:
        """Authenticate a configured development credential without logging its value."""
        for token, raw_identity in self._credentials.items():
            if not compare_digest(token, credential):
                continue
            try:
                return Principal(
                    subject=raw_identity.subject,
                    organization_id=raw_identity.organization_id,
                    roles=frozenset(Role(role) for role in raw_identity.roles),
                )
            except ValueError as exc:
                raise IdentityAuthenticationError(
                    "Development credential has an invalid role."
                ) from exc
        raise IdentityAuthenticationError("Bearer credential is invalid.")


def build_identity_provider(settings: Settings) -> IdentityProvider:
    """Build the configured provider; future provider modes extend only this composition point."""
    mode = settings.identity_provider
    if mode == "development":
        return DevelopmentIdentityProvider(settings.development_identity_credentials)
    raise RuntimeError(f"Identity provider '{mode}' is not installed.")
