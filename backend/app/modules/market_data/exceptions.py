"""Expected, audit-safe errors raised by Market Data processing."""

from __future__ import annotations

from typing import Any


class MarketDataError(Exception):
    """Base error for handled Market Data bounded-context failures."""


class UnknownOddsProviderError(MarketDataError):
    """Raised when the requested odds provider has not been registered."""


class OddsProviderAlreadyRegisteredError(MarketDataError):
    """Raised when startup composition attempts to register one provider name twice."""


class OddsPayloadValidationError(MarketDataError):
    """Structured validation failures stored with immutable raw provider JSON."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__("Odds payload validation failed.")
        self.errors = errors
