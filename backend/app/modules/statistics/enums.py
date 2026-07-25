"""Stable enumerations for the immutable Statistics bounded context."""

from enum import StrEnum


class StatisticScope(StrEnum):
    FIXTURE = "fixture"
    TEAM = "team"
    PLAYER = "player"


class StatisticsRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class RawStatisticPayloadStatus(StrEnum):
    RECEIVED = "received"
    VALID = "valid"
    INVALID = "invalid"
    APPLIED = "applied"


class StatisticsAuditOutcome(StrEnum):
    PROCESSED = "processed"
    UNCHANGED = "unchanged"
    VALIDATION_FAILED = "validation_failed"


class StatisticMappingEntityType(StrEnum):
    FIXTURE = "fixture"
    TEAM = "team"
    PLAYER = "player"
    CATEGORY = "category"


class StatisticsEventType(StrEnum):
    INGESTED = "StatisticsIngested"
    UPDATED = "StatisticsUpdated"
    VALIDATION_FAILED = "StatisticsValidationFailed"
