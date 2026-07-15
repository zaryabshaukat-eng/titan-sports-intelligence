"""Explicit errors used by the fixture-ingestion bounded context."""

from __future__ import annotations

from typing import Any


class IngestionError(Exception):
    """Base error for expected ingestion failures that are safe to report and audit."""


class UnknownProviderError(IngestionError):
    """Raised when no registered adapter owns a requested provider name."""


class ProviderAlreadyRegisteredError(IngestionError):
    """Raised when application composition registers a duplicate provider adapter."""


class PayloadValidationError(IngestionError):
    """Normalized payload-validation errors retained with the immutable raw JSON."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__("Fixture payload validation failed.")
        self.errors = errors


class ImmutableFixtureConflictError(PayloadValidationError):
    """Raised when a known provider fixture attempts to change immutable identity fields."""
