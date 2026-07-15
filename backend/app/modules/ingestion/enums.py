"""Controlled vocabularies for ingestion workflow state and audit records."""

from enum import StrEnum


class IngestionRunStatus(StrEnum):
    """Lifecycle state of one provider ingestion batch."""

    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class RawPayloadStatus(StrEnum):
    """Validation and processing state of an immutable raw payload."""

    RECEIVED = "received"
    VALID = "valid"
    INVALID = "invalid"
    APPLIED = "applied"


class IngestionAuditOutcome(StrEnum):
    """Business result of processing one provider fixture payload."""

    INSERTED = "inserted"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    VALIDATION_FAILED = "validation_failed"


class ProviderEntityType(StrEnum):
    """Canonical entity types that can retain an external-provider identity link."""

    COUNTRY = "country"
    LEAGUE = "league"
    COMPETITION = "competition"
    SEASON = "season"
    TEAM = "team"
    VENUE = "venue"
    OFFICIAL = "official"
    TIMEZONE = "timezone"


class IngestionEventType(StrEnum):
    """Events emitted into the transactional outbox by fixture ingestion."""

    FIXTURE_INGESTED = "FixtureIngested"
    FIXTURE_UPDATED = "FixtureUpdated"
    FIXTURE_VALIDATION_FAILED = "FixtureValidationFailed"
