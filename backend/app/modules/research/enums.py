"""Stable Research Engine vocabularies independent from any analysis implementation."""

from enum import StrEnum


class ExperimentStatus(StrEnum):
    """Terminal status stored on immutable experiment artifacts."""

    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"


class AnalysisType(StrEnum):
    """Initial provider-neutral statistical analysis methods."""

    DESCRIPTIVE = "descriptive"
    CORRELATION = "correlation"
    DISTRIBUTION = "distribution"
    SIGNIFICANCE = "significance"


class HypothesisDecision(StrEnum):
    """Human-readable conclusion recorded against immutable experiment evidence."""

    SUPPORTED = "supported"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class ValidationStatus(StrEnum):
    """Research reproducibility and parameter-validation outcome."""

    PASSED = "passed"
    FAILED = "failed"
