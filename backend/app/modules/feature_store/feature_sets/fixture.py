"""Fixture statistics generators using canonical immutable statistic snapshots only."""

from __future__ import annotations

from decimal import Decimal

from app.modules.feature_store.enums import FeatureDataType, FeatureType, MissingValuePolicy
from app.modules.feature_store.generator import (
    FeatureGenerationContext,
    GeneratedFeature,
    SourceReference,
)
from app.modules.feature_store.metadata import fingerprint
from app.modules.feature_store.registry import FeatureSpec


def _number(value: object) -> Decimal | None:
    """Accept only finite scalar numeric observations from canonical statistic JSON."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        candidate = Decimal(str(value))
        return candidate if candidate.is_finite() else None
    return None


def _metric(snapshot: object, *keys: str) -> Decimal | None:
    values = getattr(snapshot, "values", {})
    if not isinstance(values, dict):
        return None
    for key in keys:
        number = _number(values.get(key))
        if number is not None:
            return number
    return None


class FixtureStatisticsGenerator:
    """Produce a small explainable set of snapshot counts, trends, and statistic aggregates."""

    name = "fixture_statistics"
    generator_version = "1.0.0"

    @property
    def specs(self) -> tuple[FeatureSpec, ...]:
        return (
            FeatureSpec(
                "fixture_statistic_snapshot_count",
                "Fixture statistic snapshot count",
                "Number of canonical statistic snapshots available at the generation cutoff.",
                "1.0.0",
                "sports-intelligence",
                ("sports", "statistics"),
                ("statistics_snapshots.fixture_id", "statistics_snapshots.observed_at"),
                "count all immutable snapshots for the fixture through as_of",
                FeatureType.STATISTICAL,
                FeatureDataType.INTEGER,
                MissingValuePolicy.ZERO,
            ),
            FeatureSpec(
                "fixture_possession_total",
                "Fixture possession total",
                "Sum of latest available canonical possession observations "
                "across statistic series.",
                "1.0.0",
                "sports-intelligence",
                ("sports", "statistics"),
                ("statistics_snapshots.values.possession",),
                "sum latest series values named possession or possession_pct",
                FeatureType.FIXTURE,
                FeatureDataType.NUMBER,
                MissingValuePolicy.NULL,
            ),
            FeatureSpec(
                "fixture_shots_total",
                "Fixture shots total",
                "Sum of latest available canonical shot observations across statistic series.",
                "1.0.0",
                "sports-intelligence",
                ("sports", "statistics"),
                ("statistics_snapshots.values.shots",),
                "sum latest series values named shots or total_shots",
                FeatureType.FIXTURE,
                FeatureDataType.NUMBER,
                MissingValuePolicy.NULL,
            ),
            FeatureSpec(
                "fixture_discipline_cards_total",
                "Fixture discipline cards total",
                "Sum of latest yellow and red card observations across statistic series.",
                "1.0.0",
                "sports-intelligence",
                ("sports", "statistics"),
                (
                    "statistics_snapshots.values.yellow_cards",
                    "statistics_snapshots.values.red_cards",
                ),
                "sum latest yellow_cards and red_cards values",
                FeatureType.FIXTURE,
                FeatureDataType.INTEGER,
                MissingValuePolicy.ZERO,
            ),
            FeatureSpec(
                "fixture_shots_momentum_delta",
                "Fixture shots momentum delta",
                "Difference between the newest and preceding available canonical "
                "shots observation.",
                "1.0.0",
                "sports-intelligence",
                ("sports", "statistics"),
                ("statistics_snapshots.values.shots", "statistics_snapshots.observed_at"),
                "newest fixture shots total minus preceding fixture shots total",
                FeatureType.STATISTICAL,
                FeatureDataType.NUMBER,
                MissingValuePolicy.NULL,
            ),
        )

    async def generate(self, context: object) -> list[object]:
        assert isinstance(context, FeatureGenerationContext)
        snapshots = await context.source_reader.statistic_history(
            fixture_id=context.fixture.fixture_id, as_of=context.as_of
        )
        latest_by_series: dict[object, object] = {}
        for snapshot in snapshots:
            latest_by_series.setdefault(snapshot.series_id, snapshot)
        latest = list(latest_by_series.values())

        def sources(rows: list[object]) -> tuple[SourceReference, ...]:
            return tuple(
                SourceReference(
                    "statistics",
                    "statistic_snapshot",
                    row.id,
                    row.observed_at,
                    fingerprint(
                        {
                            "id": row.id,
                            "series_id": row.series_id,
                            "observed_at": row.observed_at,
                            "checksum": row.checksum,
                        }
                    ),
                )
                for row in rows
            )

        def total(*keys: str) -> Decimal | None:
            values = [value for row in latest if (value := _metric(row, *keys)) is not None]
            return sum(values, Decimal("0")) if values else None

        possession = total("possession", "possession_pct")
        shots = total("shots", "total_shots")
        discipline_values = [
            value
            for row in latest
            for value in (_metric(row, "yellow_cards"), _metric(row, "red_cards"))
            if value is not None
        ]
        shot_history = [
            total_value
            for row in snapshots
            if (total_value := _metric(row, "shots", "total_shots")) is not None
        ]
        momentum = shot_history[0] - shot_history[1] if len(shot_history) > 1 else None
        fixture = context.fixture
        shared = {
            "fixture_id": fixture.fixture_id,
            "competition_id": fixture.competition_id,
            "season_id": fixture.season_id,
        }
        return [
            GeneratedFeature(
                "fixture_statistic_snapshot_count",
                len(snapshots),
                Decimal("1"),
                sources(snapshots),
                **shared,
            ),
            GeneratedFeature(
                "fixture_possession_total",
                possession,
                Decimal("1") if possession is not None else Decimal("0"),
                sources(latest),
                **shared,
            ),
            GeneratedFeature(
                "fixture_shots_total",
                shots,
                Decimal("1") if shots is not None else Decimal("0"),
                sources(latest),
                **shared,
            ),
            GeneratedFeature(
                "fixture_discipline_cards_total",
                sum(discipline_values, Decimal("0")),
                Decimal("1") if discipline_values else Decimal("0"),
                sources(latest),
                **shared,
            ),
            GeneratedFeature(
                "fixture_shots_momentum_delta",
                momentum,
                Decimal("1") if momentum is not None else Decimal("0"),
                sources(snapshots[:2]),
                **shared,
            ),
        ]
