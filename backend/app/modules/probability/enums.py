"""Stable Probability Engine vocabularies independent from inference implementations."""

from enum import StrEnum


class ProbabilityRunStatus(StrEnum):
    """Terminal state of an append-only probability computation."""

    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"


class CalibrationMethod(StrEnum):
    """Supported deterministic probability calibration methods."""

    PLATT = "platt"
    ISOTONIC = "isotonic"
    TEMPERATURE = "temperature"


class ProbabilityValidationStatus(StrEnum):
    """Outcome of one explicit probability run validation rule."""

    PASSED = "passed"
    FAILED = "failed"
