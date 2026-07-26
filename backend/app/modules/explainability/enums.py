from enum import StrEnum


class ExplainabilityRunStatus(StrEnum):
    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"


class ExplainabilityValidationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
