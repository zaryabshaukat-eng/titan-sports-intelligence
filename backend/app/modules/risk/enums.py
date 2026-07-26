from enum import StrEnum


class RiskRunStatus(StrEnum):
    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"


class RiskValidationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
