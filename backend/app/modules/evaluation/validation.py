from dataclasses import dataclass
from uuid import UUID

from app.modules.consensus.models import ConsensusRun
from app.modules.evaluation.enums import BacktestValidationStatus, ScenarioType
from app.modules.explainability.models import ExplainabilityRun
from app.modules.probability.models import ProbabilityRun
from app.modules.risk.models import RiskRun


@dataclass(frozen=True, slots=True)
class Finding:
    rule_name: str
    status: BacktestValidationStatus
    message: str


def validate_scenario_parameters(scenario: ScenarioType, parameters: dict[str, object]) -> None:
    """Reject parameter values that would make a replay ambiguous or empty."""
    if scenario is ScenarioType.ROLLING_WINDOW:
        window_size = parameters.get("window_size")
        if not isinstance(window_size, int) or isinstance(window_size, bool) or window_size < 1:
            raise ValueError("rolling_window requires an integer window_size of at least one")
    if scenario is ScenarioType.TIME_SPLIT:
        test_fraction = parameters.get("test_fraction")
        if not isinstance(test_fraction, (int, float)) or isinstance(test_fraction, bool):
            raise ValueError("time_split requires numeric test_fraction")
        if not 0 < float(test_fraction) <= 1:
            raise ValueError("time_split test_fraction must be greater than zero and at most one")


def validate(
    prob: ProbabilityRun,
    consensus: ConsensusRun,
    risk: RiskRun,
    explain: ExplainabilityRun,
    requested_research_experiment_id: UUID,
    leakage: bool,
) -> tuple[Finding, ...]:
    same = (
        prob.dataset_snapshot_id
        == consensus.dataset_snapshot_id
        == risk.dataset_snapshot_id
        == explain.dataset_snapshot_id
        and prob.feature_set_version_id
        == consensus.feature_set_version_id
        == risk.feature_set_version_id
        == explain.feature_set_version_id
    )
    return (
        Finding(
            "lineage",
            BacktestValidationStatus.PASSED if same else BacktestValidationStatus.FAILED,
            "artifacts share immutable dataset/version lineage"
            if same
            else "mixed dataset or Feature Set versions",
        ),
        Finding(
            "research_lineage",
            BacktestValidationStatus.PASSED
            if prob.research_experiment_id == requested_research_experiment_id
            else BacktestValidationStatus.FAILED,
            "requested research experiment matches the probability artifact"
            if prob.research_experiment_id == requested_research_experiment_id
            else "requested research experiment conflicts with the probability artifact",
        ),
        Finding(
            "future_leakage",
            BacktestValidationStatus.PASSED if not leakage else BacktestValidationStatus.FAILED,
            "all predictions precede fixture kickoff"
            if not leakage
            else "prediction timestamp is after fixture kickoff",
        ),
    )
