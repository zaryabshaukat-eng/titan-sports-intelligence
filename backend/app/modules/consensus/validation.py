"""Compatibility validation for immutable consensus inputs."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.modules.consensus.enums import ConsensusValidationStatus
from app.modules.probability.enums import ProbabilityRunStatus
from app.modules.probability.models import ProbabilityRun


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    rule_name: str
    status: ConsensusValidationStatus
    message: str


def validate(
    *, inputs: Sequence[ProbabilityRun], expected_count: int, strategy_valid: bool
) -> tuple[ValidationFinding, ...]:
    same_dataset = bool(inputs) and len({item.dataset_snapshot_id for item in inputs}) == 1
    same_features = bool(inputs) and len({item.feature_set_version_id for item in inputs}) == 1
    completed = len(inputs) == expected_count and all(
        item.status is ProbabilityRunStatus.COMPLETED for item in inputs
    )
    return (
        _item(
            "probability_runs",
            completed,
            "all requested Probability runs are present and completed",
            "one or more Probability runs are missing or incomplete",
        ),
        _item(
            "dataset_compatibility",
            same_dataset,
            "all inputs use one dataset snapshot",
            "inputs use incompatible dataset snapshots",
        ),
        _item(
            "feature_set_compatibility",
            same_features,
            "all inputs use one Feature Set version",
            "inputs use incompatible Feature Set versions",
        ),
        _item(
            "strategy_parameters",
            strategy_valid,
            "strategy parameters are valid",
            "strategy parameters are invalid",
        ),
    )


def _item(rule: str, passed: bool, ok: str, failed: str) -> ValidationFinding:
    return ValidationFinding(
        rule,
        ConsensusValidationStatus.PASSED if passed else ConsensusValidationStatus.FAILED,
        ok if passed else failed,
    )
