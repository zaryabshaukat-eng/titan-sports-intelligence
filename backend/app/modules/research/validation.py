"""Deterministic validation for immutable dataset and experiment configurations."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.research.enums import AnalysisType, ValidationStatus
from app.modules.research.schemas import AnalysisRequest


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    rule_name: str
    status: ValidationStatus
    message: str


def validate_experiment(
    *,
    dataset_feature_set_version_id: UUID,
    requested_feature_set_version_id: UUID,
    analysis: AnalysisRequest,
    selected_feature_ids: set[str],
    numeric_feature_counts: dict[str, int],
) -> tuple[ValidationFinding, ...]:
    """Validate version consistency and input sufficiency before persisting an experiment."""
    requested = {analysis.feature_id}
    if analysis.related_feature_id:
        requested.add(analysis.related_feature_id)
    findings = [
        ValidationFinding(
            "feature_set_version",
            ValidationStatus.PASSED
            if dataset_feature_set_version_id == requested_feature_set_version_id
            else ValidationStatus.FAILED,
            "dataset and experiment reference the same Feature Set version"
            if dataset_feature_set_version_id == requested_feature_set_version_id
            else "dataset snapshot and experiment reference different Feature Set versions",
        ),
        ValidationFinding(
            "selected_features",
            ValidationStatus.PASSED
            if requested.issubset(selected_feature_ids)
            else ValidationStatus.FAILED,
            "all requested features exist in the immutable dataset snapshot"
            if requested.issubset(selected_feature_ids)
            else "one or more requested features do not exist in the dataset snapshot",
        ),
    ]
    minimum = (
        2 if analysis.analysis_type in {AnalysisType.CORRELATION, AnalysisType.SIGNIFICANCE} else 1
    )
    enough_numeric = all(
        numeric_feature_counts.get(feature_id, 0) >= minimum for feature_id in requested
    )
    findings.append(
        ValidationFinding(
            "numeric_observations",
            ValidationStatus.PASSED if enough_numeric else ValidationStatus.FAILED,
            "the dataset contains sufficient numeric observations for the requested analysis"
            if enough_numeric
            else "the dataset lacks sufficient numeric observations for the requested analysis",
        )
    )
    return tuple(findings)
