from enum import StrEnum


class BacktestRunStatus(StrEnum):
    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"


class ScenarioType(StrEnum):
    HISTORICAL_REPLAY = "historical_replay"
    ROLLING_WINDOW = "rolling_window"
    EXPANDING_WINDOW = "expanding_window"
    WALK_FORWARD = "walk_forward"
    TIME_SPLIT = "time_split"


class BacktestValidationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
