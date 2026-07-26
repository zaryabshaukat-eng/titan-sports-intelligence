"""Immutable consensus lineage and stable input fingerprinting."""

import hashlib
import json
from collections.abc import Sequence
from uuid import UUID

from app.modules.consensus.models import ConsensusLineage
from app.modules.probability.models import ProbabilityRun


def fingerprint(value: object) -> str:
    payload = json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_lineage(
    *,
    run_id: UUID,
    feature_set_version_id: UUID,
    dataset_snapshot_id: UUID,
    inputs: Sequence[ProbabilityRun],
    parameters: dict[str, object],
    random_seed: int,
) -> ConsensusLineage:
    return ConsensusLineage(
        consensus_run_id=run_id,
        feature_set_version_id=feature_set_version_id,
        dataset_snapshot_id=dataset_snapshot_id,
        probability_run_ids=[str(item.id) for item in inputs],
        model_versions=[
            {"identifier": item.model_identifier, "version": item.model_version} for item in inputs
        ],
        calibration_versions=[
            item.calibration_version_id and str(item.calibration_version_id)
            for item in inputs
            if item.calibration_version_id
        ],
        research_experiment_ids=[str(item.research_experiment_id) for item in inputs],
        parameters_checksum=fingerprint(parameters),
        random_seed=random_seed,
    )
