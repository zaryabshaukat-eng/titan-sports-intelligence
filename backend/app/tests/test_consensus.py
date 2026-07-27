"""Unit coverage for deterministic Consensus calculations and immutable run evidence."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consensus.confidence import metrics as confidence_metrics
from app.modules.consensus.disagreement import metrics as disagreement_metrics
from app.modules.consensus.engines import ConsensusEstimate
from app.modules.consensus.enums import ConsensusRunStatus, ConsensusStrategy
from app.modules.consensus.registry import ConsensusStrategyRegistry
from app.modules.consensus.repositories import ConsensusRepository
from app.modules.consensus.schemas import ConsensusRunCreate
from app.modules.consensus.service import ConsensusService
from app.modules.consensus.voting import majority_vote
from app.modules.consensus.weighting import weighted_average
from app.modules.probability.enums import ProbabilityRunStatus


def test_strategies_disagreement_and_confidence_are_deterministic() -> None:
    first, second = uuid4(), uuid4()
    estimates = [ConsensusEstimate(first, 0.2), ConsensusEstimate(second, 0.8)]
    assert weighted_average(estimates, {str(first): 1, str(second): 3}) == pytest.approx(0.65)
    assert majority_vote(estimates, 0.5) == 0.5
    assert ConsensusStrategyRegistry().resolve("median").combine(estimates, {}) == 0.5
    disagreement = disagreement_metrics([item.probability for item in estimates])
    score, detail, level = confidence_metrics(
        disagreement=disagreement, calibration_quality=0.8, completeness=1
    )
    assert disagreement["max_min_spread"] == 0.6000000000000001
    assert (
        0 <= score <= 1 and detail["input_completeness"] == 1 and level in {"low", "medium", "high"}
    )


def test_consensus_service_reuses_exact_run_and_persists_lineage_and_output() -> None:
    feature_set, dataset, experiment, fixture = uuid4(), uuid4(), uuid4(), uuid4()
    run_ids = [uuid4(), uuid4()]

    class Session:
        def __init__(self) -> None:
            self.added: list[Any] = []

        def add(self, item: Any) -> None:
            if getattr(item, "id", None) is None:
                item.id = uuid4()
            self.added.append(item)

        def add_all(self, items: list[Any]) -> None:
            for item in items:
                self.add(item)

    class Repository:
        def __init__(self, session: Session) -> None:
            self.session, self.runs = session, cast(dict[str, Any], {})
            self.inputs = [
                SimpleNamespace(
                    id=run_ids[0],
                    feature_set_version_id=feature_set,
                    dataset_snapshot_id=dataset,
                    research_experiment_id=experiment,
                    model_identifier="logistic_baseline",
                    model_version="1.0.0",
                    calibration_version_id=None,
                    input_checksum="a",
                    status=ProbabilityRunStatus.COMPLETED,
                ),
                SimpleNamespace(
                    id=run_ids[1],
                    feature_set_version_id=feature_set,
                    dataset_snapshot_id=dataset,
                    research_experiment_id=experiment,
                    model_identifier="poisson_baseline",
                    model_version="1.0.0",
                    calibration_version_id=None,
                    input_checksum="b",
                    status=ProbabilityRunStatus.COMPLETED,
                ),
            ]
            self.source_outputs = [
                SimpleNamespace(
                    probability_run_id=run_ids[0],
                    fixture_id=fixture,
                    market_type="match_result",
                    outcome="home_win",
                    estimated_probability=Decimal("0.6"),
                ),
                SimpleNamespace(
                    probability_run_id=run_ids[1],
                    fixture_id=fixture,
                    market_type="match_result",
                    outcome="home_win",
                    estimated_probability=Decimal("0.8"),
                ),
            ]

        async def probability_runs(self, _: object) -> list[Any]:
            return self.inputs

        async def existing_run(self, key: str) -> object | None:
            return self.runs.get(key)

        async def run_by_code(self, code: str) -> object | None:
            return next((item for item in self.runs.values() if item.run_code == code), None)

        async def create_run(self, run: Any) -> Any:
            run.id = uuid4()
            self.session.add(run)
            self.runs[run.idempotency_key] = run
            return run

        async def probability_outputs(self, _: object) -> list[Any]:
            return self.source_outputs

        async def latest_evaluations(self, _: object) -> list[Any]:
            return []

    async def run() -> None:
        session = Session()
        service = ConsensusService(cast(AsyncSession, session))
        service._repository = cast(ConsensusRepository, Repository(session))
        request = ConsensusRunCreate(
            run_code="two_models_v1",
            probability_run_ids=run_ids,
            strategy=ConsensusStrategy.WEIGHTED_AVERAGE,
            parameters={"weights": {str(run_ids[0]): 1, str(run_ids[1]): 3}},
            random_seed=7,
        )
        first = await service.create_run(request)
        retried = await service.create_run(request)
        assert first.id == retried.id and first.status is ConsensusRunStatus.COMPLETED
        output = next(
            item for item in session.added if item.__class__.__name__ == "ConsensusOutput"
        )
        assert output.consensus_probability == Decimal("0.75") and output.contributor_count == 2
        assert any(item.__class__.__name__ == "ConsensusLineage" for item in session.added)
        assert any(item.__class__.__name__ == "ConsensusValidationRecord" for item in session.added)

    asyncio.run(run())
