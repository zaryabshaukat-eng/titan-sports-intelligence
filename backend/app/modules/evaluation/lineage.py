import hashlib
import json

from app.modules.evaluation.models import BacktestLineage


def fingerprint(v: object) -> str:
    return hashlib.sha256(
        json.dumps(v, default=str, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build(run: object, probability_run: object) -> BacktestLineage:
    """Capture direct and indirect Probability lineage in immutable evidence."""
    artifact_ids = {
        "research_experiment_id": str(run.research_experiment_id),
        "probability_run_id": str(run.probability_run_id),
        "consensus_run_id": str(run.consensus_run_id),
        "risk_run_id": str(run.risk_run_id),
        "explainability_run_id": str(run.explainability_run_id),
        "dataset_snapshot_id": str(run.dataset_snapshot_id),
        "feature_set_version_id": str(run.feature_set_version_id),
        "probability_model_identifier": str(probability_run.model_identifier),
        "probability_model_version": str(probability_run.model_version),
    }
    if probability_run.calibration_version_id is not None:
        artifact_ids["calibration_version_id"] = str(probability_run.calibration_version_id)
    return BacktestLineage(
        backtest_run_id=run.id,
        parameters_checksum=fingerprint(run.parameters),
        artifact_ids=artifact_ids,
    )
