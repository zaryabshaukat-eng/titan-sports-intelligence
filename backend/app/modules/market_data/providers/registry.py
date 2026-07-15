"""Explicit Market Data provider registration with no provider conditionals in core services."""

from __future__ import annotations

from app.modules.market_data.exceptions import (
    OddsProviderAlreadyRegisteredError,
    UnknownOddsProviderError,
)
from app.modules.market_data.providers.base import OddsProviderAdapter


class OddsProviderRegistry:
    """Application-composed map of odds-provider names to source-specific adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, OddsProviderAdapter] = {}

    def register(self, adapter: OddsProviderAdapter) -> None:
        """Register one provider name once; duplicate registration is a startup configuration error."""
        if adapter.provider_name in self._adapters:
            raise OddsProviderAlreadyRegisteredError(
                f"An odds adapter is already registered for '{adapter.provider_name}'."
            )
        self._adapters[adapter.provider_name] = adapter

    def get(self, provider_name: str) -> OddsProviderAdapter:
        """Return one configured adapter or fail with a safe explicit error."""
        try:
            return self._adapters[provider_name]
        except KeyError as exc:
            raise UnknownOddsProviderError(f"Unknown odds provider '{provider_name}'.") from exc

    @property
    def provider_names(self) -> tuple[str, ...]:
        """Expose configured providers for diagnostics and tests."""
        return tuple(sorted(self._adapters))


def build_default_registry() -> OddsProviderRegistry:
    """Compose the reference provider adapters intentionally enabled in this deployment."""
    from app.modules.market_data.providers.odds_feed_v1 import OddsFeedV1Adapter

    registry = OddsProviderRegistry()
    registry.register(OddsFeedV1Adapter())
    return registry
