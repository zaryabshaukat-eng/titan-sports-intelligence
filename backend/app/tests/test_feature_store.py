"""Unit coverage for Feature Store metadata, validation, generators, and retrieval filters."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feature_store.enums import (
    FeatureDataType,
    FeatureType,
    MissingValuePolicy,
    ValidationStatus,
)
from app.modules.feature_store.feature_sets.market import MarketSummaryGenerator
from app.modules.feature_store.feature_sets.temporal import TemporalFeatureGenerator
from app.modules.feature_store.generator import (
    FeatureGenerationContext,
    FixtureContext,
    GeneratedFeature,
    SourceReference,
)
from app.modules.feature_store.metadata import feature_set_checksum, fingerprint
from app.modules.feature_store.models import (
    FeatureDefinition,
    FeatureGenerationRun,
    FeatureLineage,
    FeatureSet,
    FeatureSetVersion,
    FeatureValidationRecord,
    FeatureValue,
)
from app.modules.feature_store.registry import (
    FeatureGeneratorRegistry,
    FeatureSpec,
    build_default_registry,
)
from app.modules.feature_store.repositories import FeatureStoreRepository
from app.modules.feature_store.schemas import FeatureGenerationRequest, FeatureValueFilters
from app.modules.feature_store.service import FeatureGenerationService
from app.modules.feature_store.validation import validate_feature


class _SourceReader:
    def __init__(self, now: datetime) -> None:
        self._now = now

    async def previous_team_fixtures(
        self, *, team_id: object, as_of: datetime, home_only: bool | None = None, limit: int = 5
    ) -> list[object]:
        _ = team_id, as_of, home_only, limit
        return [SimpleNamespace(id=uuid4(), scheduled_start_at=self._now - timedelta(days=3))]

    async def latest_odds(self, *, fixture_id: object, as_of: datetime) -> list[object]:
        _ = fixture_id, as_of
        return [
            SimpleNamespace(
                id=uuid4(),
                observed_at=self._now,
                checksum="a" * 64,
                implied_probability=Decimal("0.4"),
            ),
            SimpleNamespace(
                id=uuid4(),
                observed_at=self._now,
                checksum="b" * 64,
                implied_probability=Decimal("0.6"),
            ),
        ]


def _context(now: datetime) -> FeatureGenerationContext:
    return FeatureGenerationContext(
        fixture=FixtureContext(
            fixture_id=uuid4(),
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            competition_id=uuid4(),
            season_id=uuid4(),
            scheduled_start_at=now,
        ),
        as_of=now,
        source_reader=_SourceReader(now),  # type: ignore[arg-type]
    )


def test_default_registry_has_versioned_canonical_generators() -> None:
    registry = build_default_registry()

    assert {generator.name for generator in registry.generators} == {
        "fixture_statistics",
        "market_summary",
        "temporal",
    }
    assert len({spec.feature_id for spec in registry.specs}) == len(registry.specs)
    assert {module for spec in registry.specs for module in spec.source_modules} <= {
        "sports",
        "statistics",
        "market_data",
    }


def test_feature_metadata_fingerprints_are_stable() -> None:
    specs = build_default_registry().specs

    assert fingerprint({"feature": "shots", "version": "1"}) == fingerprint(
        {"version": "1", "feature": "shots"}
    )
    assert feature_set_checksum(specs) == feature_set_checksum(specs)


def test_validation_rejects_undeclared_source_and_allows_declared_missing_values() -> None:
    spec = next(
        item for item in build_default_registry().specs if item.feature_id == "home_rest_days"
    )
    now = datetime(2026, 8, 1, tzinfo=UTC)
    missing = GeneratedFeature(
        feature_id=spec.feature_id,
        value=None,
        quality_score=Decimal("0"),
        sources=(),
        fixture_id=uuid4(),
    )
    assert all(
        finding.status is ValidationStatus.PASSED
        for finding in validate_feature(
            spec=spec, feature=missing, as_of=now, generator_version="1.0.0"
        )
    )
    invalid_source = GeneratedFeature(
        feature_id=spec.feature_id,
        value=Decimal("2"),
        quality_score=Decimal("1"),
        sources=(SourceReference("raw_provider", "payload", uuid4(), now),),
        fixture_id=uuid4(),
    )
    assert any(
        finding.rule_name == "dependency_provenance" and finding.status is ValidationStatus.FAILED
        for finding in validate_feature(
            spec=spec, feature=invalid_source, as_of=now, generator_version="1.0.0"
        )
    )


def test_temporal_and_market_generators_are_deterministic_for_historical_cutoff() -> None:
    async def run() -> None:
        now = datetime(2026, 8, 1, tzinfo=UTC)
        context = _context(now)
        temporal = await TemporalFeatureGenerator().generate(context)
        market = await MarketSummaryGenerator().generate(context)

        values = {item.feature_id: item.value for item in [*temporal, *market]}
        assert values["home_rest_days"] == Decimal("3")
        assert values["home_recent_home_fixture_count_5"] == 1
        assert values["market_implied_probability_mean"] == Decimal("0.5")
        assert values["market_implied_probability_volatility"] == Decimal("0.1")

    asyncio.run(run())


def test_retrieval_filters_compile_subject_and_feature_version_constraints() -> None:
    fixture_id = uuid4()
    filters = FeatureValueFilters(
        fixture_id=fixture_id,
        feature_set_code="core_fixture",
        feature_set_version="1.0.0",
        feature_id="fixture_shots_total",
    )

    statement = FeatureStoreRepository._apply_value_filters(select(FeatureValue), filters)
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "feature_store_feature_values.fixture_id" in compiled
    assert "feature_store_feature_sets.code" in compiled
    assert "feature_store_feature_set_versions.version" in compiled


def test_generation_service_reuses_identical_historical_inputs_with_lineage_and_validation() -> (
    None
):
    now = datetime(2026, 8, 1, tzinfo=UTC)
    source_id = uuid4()
    fixture = FixtureContext(uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), now)
    spec = FeatureSpec(
        "test_metric",
        "Test metric",
        "Test",
        "1.0.0",
        "test",
        ("sports",),
        ("sports_fixtures",),
        "constant",
        FeatureType.FIXTURE,
        FeatureDataType.NUMBER,
        MissingValuePolicy.REJECT,
    )

    class _Session:
        def __init__(self) -> None:
            self.added: list[
                FeatureGenerationRun | FeatureLineage | FeatureValidationRecord | FeatureValue
            ] = []

        def add(
            self,
            item: FeatureGenerationRun | FeatureLineage | FeatureValidationRecord | FeatureValue,
        ) -> None:
            self.added.append(item)

        def add_all(
            self,
            items: list[
                FeatureGenerationRun | FeatureLineage | FeatureValidationRecord | FeatureValue
            ],
        ) -> None:
            self.added.extend(items)

        async def flush(self) -> None:
            for item in self.added:
                if getattr(item, "id", None) is None:
                    item.id = uuid4()

    class _Repository:
        def __init__(self, session: _Session) -> None:
            self._session = session
            self._runs: dict[str, FeatureGenerationRun] = {}
            self._feature_set = FeatureSet(id=uuid4())
            self._set_version = FeatureSetVersion(id=uuid4())
            self._definitions = {"test_metric": FeatureDefinition(id=uuid4())}

        async def ensure_feature_set_version(
            self, **_: object
        ) -> tuple[FeatureSet, FeatureSetVersion, dict[str, FeatureDefinition]]:
            return (
                self._feature_set,
                self._set_version,
                self._definitions,
            )

        async def existing_run(self, idempotency_key: str) -> FeatureGenerationRun | None:
            return self._runs.get(idempotency_key)

        async def create_run(self, run: FeatureGenerationRun) -> FeatureGenerationRun:
            run.id = uuid4()
            self._runs[run.idempotency_key] = run
            return run

    class _Generator:
        name = "test"
        generator_version = "1.0.0"

        @property
        def specs(self) -> tuple[FeatureSpec, ...]:
            return (spec,)

        async def generate(self, context: FeatureGenerationContext) -> list[GeneratedFeature]:
            _ = context
            return [
                GeneratedFeature(
                    "test_metric",
                    Decimal("2.5"),
                    Decimal("1"),
                    (SourceReference("sports", "fixture", source_id, now),),
                    fixture_id=fixture.fixture_id,
                )
            ]

    class _Reader:
        def __init__(self, session: AsyncSession) -> None:
            _ = session

        async def fixture_context(self, fixture_id: object) -> FixtureContext:
            _ = fixture_id
            return fixture

    async def run() -> None:
        session = _Session()
        registry = FeatureGeneratorRegistry()
        registry.register(_Generator())
        service = FeatureGenerationService(cast(AsyncSession, session), registry)
        service._repository = cast(FeatureStoreRepository, _Repository(session))
        request = FeatureGenerationRequest(
            feature_set_code="core_fixture",
            feature_set_version="1.0.0",
            fixture_id=fixture.fixture_id,
            as_of=now,
        )
        with patch("app.modules.feature_store.service.CanonicalFeatureSourceReader", _Reader):
            first = await service.generate(request)
            second = await service.generate(request)

        assert first.status.value == "completed"
        assert first.generated_count == 1
        assert second.reused_existing_run is True
        assert any(item.__class__.__name__ == "FeatureValue" for item in session.added)
        assert any(item.__class__.__name__ == "FeatureLineage" for item in session.added)
        assert any(item.__class__.__name__ == "FeatureValidationRecord" for item in session.added)

    asyncio.run(run())
