"""Unit coverage for immutable Research datasets, experiments, validation, and statistics."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.research.enums import AnalysisType, ExperimentStatus, ValidationStatus
from app.modules.research.exceptions import DatasetVersionConflictError
from app.modules.research.schemas import (
    AnalysisRequest,
    DatasetSelection,
    DatasetSnapshotCreate,
    ExperimentCreate,
)
from app.modules.research.service import ResearchService
from app.modules.research.statistics import (
    correlation,
    descriptive,
    distribution,
    welch_significance,
)
from app.modules.research.validation import validate_experiment


def test_statistical_primitives_are_deterministic_and_descriptive() -> None:
    """The initial framework is deterministic and does not invoke a predictive model."""
    summary = descriptive([1.0, 2.0, 3.0], feature_id="rest_days")
    histogram = distribution([1.0, 2.0, 3.0], feature_id="rest_days", bins=2)
    related = correlation(
        {"fixture:one": 1.0, "fixture:two": 2.0},
        {"fixture:one": 3.0, "fixture:two": 6.0},
        left_feature="rest_days",
        right_feature="shots",
    )
    significance = welch_significance(
        [1.0, 2.0, 3.0], [4.0, 5.0, 6.0], left_feature="home", right_feature="away"
    )

    assert summary.values["mean"] == 2.0
    assert sum(item["count"] for item in histogram.values["bins"]) == 3
    assert related.values["coefficient"] == 1.0
    assert significance.p_value is not None
    assert 0 <= significance.p_value <= 1


def test_analysis_contract_requires_related_feature_and_timezone_aware_window() -> None:
    """Invalid configurations fail before a dataset or experiment is persisted."""
    with pytest.raises(ValidationError):
        AnalysisRequest(analysis_type=AnalysisType.CORRELATION, feature_id="shots")
    with pytest.raises(ValidationError):
        DatasetSelection(
            feature_ids=["shots"],
            observed_after=datetime(2026, 8, 1),
        )


def test_experiment_validation_records_version_and_numeric_input_failures() -> None:
    """Validation is explicit, reproducible evidence rather than an implicit best effort."""
    findings = validate_experiment(
        dataset_feature_set_version_id=uuid4(),
        requested_feature_set_version_id=uuid4(),
        analysis=AnalysisRequest(analysis_type=AnalysisType.DESCRIPTIVE, feature_id="shots"),
        selected_feature_ids={"shots"},
        numeric_feature_counts={"shots": 0},
    )

    assert {finding.rule_name for finding in findings} == {
        "feature_set_version",
        "selected_features",
        "numeric_observations",
    }
    assert sum(item.status is ValidationStatus.FAILED for item in findings) == 2


def test_research_service_materializes_frozen_datasets_and_reuses_exact_retries() -> None:
    """A snapshot copies Feature Store rows once; later experiment runs use only those copies."""
    now = datetime(2026, 8, 1, tzinfo=UTC)
    feature_set_version_id = uuid4()
    fixture_id = uuid4()
    definition = SimpleNamespace(id=uuid4(), feature_id="fixture_shots_total")
    source_values = [
        SimpleNamespace(
            id=uuid4(),
            fixture_id=fixture_id,
            team_id=None,
            player_id=None,
            competition_id=None,
            season_id=None,
            value=Decimal("12"),
            numeric_value=Decimal("12"),
            observed_at=now,
            calculated_at=now,
        ),
        SimpleNamespace(
            id=uuid4(),
            fixture_id=uuid4(),
            team_id=None,
            player_id=None,
            competition_id=None,
            season_id=None,
            value=Decimal("8"),
            numeric_value=Decimal("8"),
            observed_at=now,
            calculated_at=now,
        ),
    ]

    class _Session:
        def __init__(self) -> None:
            self.added: list[object] = []

        def add(self, item: object) -> None:
            self.added.append(item)

        def add_all(self, items: list[object]) -> None:
            self.added.extend(items)

    class _Repository:
        def __init__(self, session: _Session) -> None:
            self._session = session
            self._datasets_by_key: dict[str, object] = {}
            self._datasets_by_id: dict[object, object] = {}
            self._datasets_by_version: dict[tuple[str, str], object] = {}
            self._experiments_by_key: dict[str, object] = {}
            self._experiments_by_code: dict[str, object] = {}

        async def feature_set_version(self, version_id: object) -> object | None:
            return (
                SimpleNamespace(id=feature_set_version_id, generator_version="1.0.0")
                if version_id == feature_set_version_id
                else None
            )

        async def feature_values(self, **_: object) -> list[tuple[object, object]]:
            return [(source_values[0], definition), (source_values[1], definition)]

        async def existing_dataset(self, key: str) -> object | None:
            return self._datasets_by_key.get(key)

        async def dataset_by_code_version(self, code: str, version: str) -> object | None:
            return self._datasets_by_version.get((code, version))

        async def create_dataset(self, dataset: object) -> object:
            dataset.id = uuid4()
            self._session.add(dataset)
            self._datasets_by_key[dataset.idempotency_key] = dataset
            self._datasets_by_id[dataset.id] = dataset
            self._datasets_by_version[(dataset.dataset_code, dataset.version)] = dataset
            return dataset

        async def dataset(self, dataset_id: object) -> object | None:
            return self._datasets_by_id.get(dataset_id)

        async def all_dataset_rows(self, dataset_id: object) -> list[object]:
            return [
                row
                for row in self._session.added
                if getattr(row, "dataset_snapshot_id", None) == dataset_id
            ]

        async def existing_experiment(self, key: str) -> object | None:
            return self._experiments_by_key.get(key)

        async def experiment_by_code(self, code: str) -> object | None:
            return self._experiments_by_code.get(code)

        async def create_experiment(self, experiment: object) -> object:
            experiment.id = uuid4()
            self._session.add(experiment)
            self._experiments_by_key[experiment.idempotency_key] = experiment
            self._experiments_by_code[experiment.experiment_code] = experiment
            return experiment

    async def run() -> None:
        session = _Session()
        service = ResearchService(session)  # type: ignore[arg-type]
        service._repository = _Repository(session)  # type: ignore[assignment]
        dataset_request = DatasetSnapshotCreate(
            dataset_code="fixture_shots",
            version="1.0.0",
            name="Fixture shots",
            description="Frozen shots data.",
            owner="research",
            feature_set_version_id=feature_set_version_id,
            selection=DatasetSelection(feature_ids=["fixture_shots_total"]),
        )

        first_dataset = await service.create_dataset(dataset_request)
        retried_dataset = await service.create_dataset(dataset_request)

        assert first_dataset.id == retried_dataset.id
        snapshot_rows = [
            row for row in session.added if row.__class__.__name__ == "DatasetSnapshotRow"
        ]
        assert len(snapshot_rows) == 2
        assert {row.source_feature_value_id for row in snapshot_rows} == {
            value.id for value in source_values
        }

        experiment_request = ExperimentCreate(
            experiment_code="fixture_shots_descriptive",
            name="Fixture shots descriptive",
            description="Summary over the frozen dataset.",
            owner="research",
            feature_set_version_id=feature_set_version_id,
            dataset_snapshot_id=first_dataset.id,
            random_seed=17,
            analysis=AnalysisRequest(
                analysis_type=AnalysisType.DESCRIPTIVE,
                feature_id="fixture_shots_total",
            ),
        )
        first_experiment = await service.create_experiment(experiment_request)
        retried_experiment = await service.create_experiment(experiment_request)

        assert first_experiment.id == retried_experiment.id
        assert first_experiment.status is ExperimentStatus.COMPLETED
        assert any(item.__class__.__name__ == "ExperimentLineage" for item in session.added)
        assert any(
            item.__class__.__name__ == "ExperimentValidationRecord" for item in session.added
        )
        assert any(item.__class__.__name__ == "ExperimentStatisticResult" for item in session.added)

        source_values[0].numeric_value = Decimal("99")
        with pytest.raises(DatasetVersionConflictError):
            await service.create_dataset(dataset_request)

    asyncio.run(run())
