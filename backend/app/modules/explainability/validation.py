from dataclasses import dataclass

from app.modules.explainability.enums import ExplainabilityValidationStatus


@dataclass(frozen=True, slots=True)
class Finding:
    rule_name: str
    status: ExplainabilityValidationStatus
    message: str


def validate(prob: object, consensus: object, risk: object) -> tuple[Finding, ...]:
    same = (
        prob.dataset_snapshot_id == consensus.dataset_snapshot_id == risk.dataset_snapshot_id
        and prob.feature_set_version_id
        == consensus.feature_set_version_id
        == risk.feature_set_version_id
    )
    return (
        Finding(
            "output_compatibility",
            ExplainabilityValidationStatus.PASSED
            if same
            else ExplainabilityValidationStatus.FAILED,
            "all outputs share dataset and Feature Set versions"
            if same
            else "outputs have incompatible dataset or Feature Set lineage",
        ),
    )
