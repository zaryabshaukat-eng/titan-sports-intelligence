from enum import StrEnum


class MonitoringStatus(StrEnum):
    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"


class ValidationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
