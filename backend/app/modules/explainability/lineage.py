import hashlib
import json

from app.modules.explainability.models import ExplainabilityLineage


def fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, default=str, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build(run: object, probability: object) -> ExplainabilityLineage:
    return ExplainabilityLineage(
        explainability_run_id=run.id,
        probability_run_id=run.probability_run_id,
        consensus_run_id=run.consensus_run_id,
        risk_run_id=run.risk_run_id,
        dataset_snapshot_id=run.dataset_snapshot_id,
        feature_set_version_id=run.feature_set_version_id,
        research_experiment_id=probability.research_experiment_id,
        parameters_checksum=fingerprint(run.parameters),
    )
