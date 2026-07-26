"""Deterministic Feature Store quality gates before any immutable value is written."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.modules.feature_store.enums import (
    FeatureDataType,
    MissingValuePolicy,
    ValidationStatus,
)
from app.modules.feature_store.generator import GeneratedFeature
from app.modules.feature_store.registry import FeatureSpec


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """One persisted quality-gate outcome."""

    rule_name: str
    status: ValidationStatus
    message: str


def validate_feature(
    *, spec: FeatureSpec, feature: GeneratedFeature, as_of: datetime, generator_version: str
) -> tuple[ValidationFinding, ...]:
    """Validate null policy, logical type, source dependency, and historical time boundaries."""
    findings: list[ValidationFinding] = []
    if feature.value is None:
        allowed = spec.missing_value_policy is MissingValuePolicy.NULL
        findings.append(
            ValidationFinding(
                "null_handling",
                ValidationStatus.PASSED if allowed else ValidationStatus.FAILED,
                "null accepted by declared missing-value policy"
                if allowed
                else "feature value is null but the feature policy does not allow it",
            )
        )
    elif spec.data_type is FeatureDataType.INTEGER:
        valid = isinstance(feature.value, int) and not isinstance(feature.value, bool)
        findings.append(
            ValidationFinding(
                "data_type",
                ValidationStatus.PASSED if valid else ValidationStatus.FAILED,
                "integer value matches declared type" if valid else "expected an integer value",
            )
        )
    elif spec.data_type is FeatureDataType.NUMBER:
        valid = isinstance(feature.value, (int, float, Decimal)) and not isinstance(
            feature.value, bool
        )
        findings.append(
            ValidationFinding(
                "data_type",
                ValidationStatus.PASSED if valid else ValidationStatus.FAILED,
                "numeric value matches declared type" if valid else "expected a numeric value",
            )
        )
    else:
        findings.append(
            ValidationFinding("data_type", ValidationStatus.PASSED, "value matches supported type")
        )

    valid_quality = Decimal("0") <= feature.quality_score <= Decimal("1")
    findings.append(
        ValidationFinding(
            "quality_range",
            ValidationStatus.PASSED if valid_quality else ValidationStatus.FAILED,
            "quality score is within [0, 1]"
            if valid_quality
            else "quality score is outside [0, 1]",
        )
    )
    invalid_source = any(
        source.source_module not in spec.source_modules for source in feature.sources
    )
    findings.append(
        ValidationFinding(
            "dependency_provenance",
            ValidationStatus.FAILED if invalid_source else ValidationStatus.PASSED,
            "all sources are declared canonical dependencies"
            if not invalid_source
            else "a source module is not declared by the feature specification",
        )
    )
    future_source = any(
        source.observed_at is not None and source.observed_at > as_of for source in feature.sources
    )
    findings.append(
        ValidationFinding(
            "temporal_boundary",
            ValidationStatus.FAILED if future_source else ValidationStatus.PASSED,
            "all source observations are at or before the historical cutoff"
            if not future_source
            else "a source observation is after the historical cutoff",
        )
    )
    findings.append(
        ValidationFinding(
            "generator_version",
            ValidationStatus.PASSED if generator_version else ValidationStatus.FAILED,
            "generator version is recorded"
            if generator_version
            else "generator version is missing",
        )
    )
    findings.append(
        ValidationFinding(
            "feature_version",
            ValidationStatus.PASSED if spec.version else ValidationStatus.FAILED,
            "feature version is recorded" if spec.version else "feature version is missing",
        )
    )
    return tuple(findings)
