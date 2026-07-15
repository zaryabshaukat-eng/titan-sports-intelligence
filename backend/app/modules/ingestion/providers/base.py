"""Stable adapter contract for provider-specific fixture payloads."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.modules.ingestion.schemas import NormalizedFixture


class FixtureProviderAdapter(ABC):
    """Translate one external provider's payload vocabulary into TITAN's canonical DTO."""

    provider_name: str

    @abstractmethod
    def normalize(self, payload: dict[str, Any]) -> NormalizedFixture:
        """Validate and normalize one provider fixture payload."""

    @abstractmethod
    def extract_fixture_id(self, payload: dict[str, Any]) -> str | None:
        """Best-effort external fixture ID extraction for invalid-payload audit records."""
