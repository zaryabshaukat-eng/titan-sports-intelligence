"""Explicit provider registration, avoiding service-level provider conditionals."""

from __future__ import annotations

from app.modules.ingestion.exceptions import ProviderAlreadyRegisteredError, UnknownProviderError
from app.modules.ingestion.providers.base import FixtureProviderAdapter


class FixtureProviderRegistry:
    """Application-composed map of stable provider names to fixture adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, FixtureProviderAdapter] = {}

    def register(self, adapter: FixtureProviderAdapter) -> None:
        """Register one adapter once; duplicate names are a startup configuration error."""
        if adapter.provider_name in self._adapters:
            raise ProviderAlreadyRegisteredError(
                f"A fixture adapter is already registered for '{adapter.provider_name}'."
            )
        self._adapters[adapter.provider_name] = adapter

    def get(self, provider_name: str) -> FixtureProviderAdapter:
        """Return a registered adapter or raise an explicit, safe unknown-provider error."""
        try:
            return self._adapters[provider_name]
        except KeyError as exc:
            raise UnknownProviderError(f"Unknown fixture provider '{provider_name}'.") from exc

    @property
    def provider_names(self) -> tuple[str, ...]:
        """Expose registered names for operational diagnostics and tests."""
        return tuple(sorted(self._adapters))


def build_default_registry() -> FixtureProviderRegistry:
    """Compose the adapters intentionally supported by this deployment."""
    from app.modules.ingestion.providers.fixture_feed_v1 import FixtureFeedV1Adapter

    registry = FixtureProviderRegistry()
    registry.register(FixtureFeedV1Adapter())
    return registry
