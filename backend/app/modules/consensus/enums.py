"""Stable Consensus Engine vocabularies."""

from enum import StrEnum


class ConsensusRunStatus(StrEnum):
    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"


class ConsensusStrategy(StrEnum):
    WEIGHTED_AVERAGE = "weighted_average"
    MEDIAN = "median"
    TRIMMED_MEAN = "trimmed_mean"
    MAJORITY_VOTING = "majority_voting"
    BAYESIAN_POOLING = "bayesian_pooling"


class ConsensusValidationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
