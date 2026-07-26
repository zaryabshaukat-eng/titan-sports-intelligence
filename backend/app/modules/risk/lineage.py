import hashlib
import json
from uuid import UUID

from app.modules.consensus.models import ConsensusRun
from app.modules.risk.models import RiskLineage


def fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, default=str, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build(
    *,
    risk_run_id: UUID,
    consensus: ConsensusRun,
    probability_run_ids: list[str],
    parameters: dict[str, object],
    seed: int,
) -> RiskLineage:
    return RiskLineage(
        risk_run_id=risk_run_id,
        consensus_run_id=consensus.id,
        probability_run_ids=probability_run_ids,
        dataset_snapshot_id=consensus.dataset_snapshot_id,
        feature_set_version_id=consensus.feature_set_version_id,
        parameters_checksum=fingerprint(parameters),
        random_seed=seed,
    )
