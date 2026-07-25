"""Expected, audit-safe errors for Statistics ingestion."""

from __future__ import annotations

from typing import Any


class StatisticsError(Exception):
    """Base class for expected Statistics bounded-context failures."""


class StatisticsPayloadValidationError(StatisticsError):
    """A source payload cannot be normalized into the canonical contract."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__("Statistics payload validation failed.")
        self.errors = errors


class StatisticsResolutionError(StatisticsError):
    """A provider reference cannot safely resolve to a canonical entity."""


class StatisticsPersistenceError(StatisticsError):
    """An expected persistence conflict prevented canonical observation storage."""
