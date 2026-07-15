"""Controlled vocabularies owned by the Market Data bounded context."""

from enum import StrEnum


class OddsIngestionRunStatus(StrEnum):
    """Lifecycle state of one odds-provider batch."""

    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class RawOddsPayloadStatus(StrEnum):
    """Validation and application state for an immutable raw odds payload."""

    RECEIVED = "received"
    VALID = "valid"
    INVALID = "invalid"
    APPLIED = "applied"


class OddsAuditOutcome(StrEnum):
    """Business outcome for one raw odds payload."""

    PROCESSED = "processed"
    UNCHANGED = "unchanged"
    VALIDATION_FAILED = "validation_failed"


class MarketProviderEntityType(StrEnum):
    """Canonical entity categories that may have an external provider identity."""

    FIXTURE = "fixture"
    BOOKMAKER = "bookmaker"
    MARKET = "market"
    SELECTION = "selection"


class OddsMovementType(StrEnum):
    """Durable movement taxonomy for price and market-structure changes."""

    OPENING = "opening"
    CLOSING = "closing"
    PRICE_INCREASED = "price_increased"
    PRICE_DECREASED = "price_decreased"
    MARKET_SUSPENDED = "market_suspended"
    MARKET_REOPENED = "market_reopened"
    SELECTION_ADDED = "selection_added"
    SELECTION_REMOVED = "selection_removed"


class MarketDataEventType(StrEnum):
    """Domain events persisted in the Market Data transactional outbox."""

    ODDS_SNAPSHOT_CREATED = "OddsSnapshotCreated"
    ODDS_CHANGED = "OddsChanged"
    MARKET_SUSPENDED = "MarketSuspended"
    MARKET_REOPENED = "MarketReopened"
    ODDS_VALIDATION_FAILED = "OddsValidationFailed"
