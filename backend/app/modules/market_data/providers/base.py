"""Stable provider-adapter contract for source-specific odds payloads."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.modules.market_data.schemas import NormalizedOddsPayload


class OddsProviderAdapter(ABC):
    """Translate one external provider's odds vocabulary into canonical normalized DTOs."""

    provider_name: str

    @abstractmethod
    def normalize(self, payload: dict[str, Any]) -> NormalizedOddsPayload:
        """Validate and normalize one complete source-provider odds payload."""

    @abstractmethod
    def extract_fixture_reference(self, payload: dict[str, Any]) -> tuple[str | None, str | None]:
        """Best-effort fixture provider and ID extraction for invalid-payload audit records."""
