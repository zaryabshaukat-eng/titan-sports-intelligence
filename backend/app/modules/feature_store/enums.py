"""Stable vocabularies owned by the Feature Store bounded context."""

from enum import StrEnum


class FeatureType(StrEnum):
    """Business classification used to describe a feature in its registry metadata."""

    TEMPORAL = "temporal"
    TEAM = "team"
    FIXTURE = "fixture"
    MARKET = "market"
    STATISTICAL = "statistical"
    PLAYER = "player"


class FeatureDataType(StrEnum):
    """Supported logical value types; values remain JSON for provider-neutral storage."""

    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    JSON = "json"


class MissingValuePolicy(StrEnum):
    """Explicit deterministic treatment when canonical dependencies have no observation."""

    REJECT = "reject"
    NULL = "null"
    ZERO = "zero"


class GenerationStatus(StrEnum):
    """Lifecycle for one deterministic offline generation request."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    """Outcome of a persisted feature validation rule."""

    PASSED = "passed"
    FAILED = "failed"
