from dataclasses import dataclass

from app.modules.consensus.enums import ConsensusRunStatus
from app.modules.risk.enums import RiskValidationStatus


@dataclass(frozen=True, slots=True)
class Finding:
    rule_name: str
    status: RiskValidationStatus
    message: str


def validate(
    consensus: object, outputs: list[object], lineage: object | None
) -> tuple[Finding, ...]:
    return (
        Finding(
            "consensus_compatibility",
            RiskValidationStatus.PASSED
            if consensus.status is ConsensusRunStatus.COMPLETED
            else RiskValidationStatus.FAILED,
            "consensus run completed"
            if consensus.status is ConsensusRunStatus.COMPLETED
            else "consensus run did not complete",
        ),
        Finding(
            "feature_completeness",
            RiskValidationStatus.PASSED if outputs else RiskValidationStatus.FAILED,
            "consensus has output evidence" if outputs else "consensus has no output evidence",
        ),
        Finding(
            "lineage",
            RiskValidationStatus.PASSED if lineage else RiskValidationStatus.FAILED,
            "consensus lineage is present" if lineage else "consensus lineage is missing",
        ),
    )
