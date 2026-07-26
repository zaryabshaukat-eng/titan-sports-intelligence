"""Temporal and team-context generators based exclusively on canonical fixtures."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from app.modules.feature_store.enums import FeatureDataType, FeatureType, MissingValuePolicy
from app.modules.feature_store.generator import (
    FeatureGenerationContext,
    GeneratedFeature,
    SourceReference,
)
from app.modules.feature_store.metadata import fingerprint
from app.modules.feature_store.registry import FeatureSpec
from app.modules.sports.models import Fixture


class TemporalFeatureGenerator:
    """Produce deterministic rest-day and home/away recent-fixture context features."""

    name = "temporal"
    generator_version = "1.0.0"

    @property
    def specs(self) -> tuple[FeatureSpec, ...]:
        return (
            FeatureSpec(
                "home_rest_days",
                "Home rest days",
                "Calendar days between kickoff and the home team's latest prior canonical fixture.",
                "1.0.0",
                "sports-intelligence",
                ("sports",),
                ("sports_fixtures.scheduled_start_at",),
                "as_of fixture kickoff minus the latest prior fixture kickoff for the home team",
                FeatureType.TEMPORAL,
                FeatureDataType.NUMBER,
                MissingValuePolicy.NULL,
            ),
            FeatureSpec(
                "away_rest_days",
                "Away rest days",
                "Calendar days between kickoff and the away team's latest prior canonical fixture.",
                "1.0.0",
                "sports-intelligence",
                ("sports",),
                ("sports_fixtures.scheduled_start_at",),
                "as_of fixture kickoff minus the latest prior fixture kickoff for the away team",
                FeatureType.TEMPORAL,
                FeatureDataType.NUMBER,
                MissingValuePolicy.NULL,
            ),
            FeatureSpec(
                "home_recent_home_fixture_count_5",
                "Home recent home-fixture count",
                "Count of the home team's five most recent canonical home fixtures "
                "before the cutoff.",
                "1.0.0",
                "sports-intelligence",
                ("sports",),
                ("sports_fixtures.home_team_id", "sports_fixtures.scheduled_start_at"),
                "count of up to five prior home fixtures",
                FeatureType.TEAM,
                FeatureDataType.INTEGER,
                MissingValuePolicy.ZERO,
            ),
            FeatureSpec(
                "away_recent_away_fixture_count_5",
                "Away recent away-fixture count",
                "Count of the away team's five most recent canonical away fixtures "
                "before the cutoff.",
                "1.0.0",
                "sports-intelligence",
                ("sports",),
                ("sports_fixtures.away_team_id", "sports_fixtures.scheduled_start_at"),
                "count of up to five prior away fixtures",
                FeatureType.TEAM,
                FeatureDataType.INTEGER,
                MissingValuePolicy.ZERO,
            ),
        )

    async def generate(self, context: FeatureGenerationContext) -> list[GeneratedFeature]:
        fixture = context.fixture
        home_any = await context.source_reader.previous_team_fixtures(
            team_id=fixture.home_team_id, as_of=context.as_of, limit=1
        )
        away_any = await context.source_reader.previous_team_fixtures(
            team_id=fixture.away_team_id, as_of=context.as_of, limit=1
        )
        home_split = await context.source_reader.previous_team_fixtures(
            team_id=fixture.home_team_id, as_of=context.as_of, home_only=True, limit=5
        )
        away_split = await context.source_reader.previous_team_fixtures(
            team_id=fixture.away_team_id, as_of=context.as_of, home_only=False, limit=5
        )

        def refs(rows: Sequence[Fixture]) -> tuple[SourceReference, ...]:
            return tuple(
                SourceReference(
                    "sports",
                    "fixture",
                    row.id,
                    row.scheduled_start_at,
                    fingerprint({"id": row.id, "scheduled_start_at": row.scheduled_start_at}),
                )
                for row in rows
            )

        def rest(rows: Sequence[Fixture]) -> Decimal | None:
            if not rows:
                return None
            return Decimal(
                str((fixture.scheduled_start_at - rows[0].scheduled_start_at).total_seconds())
            ) / Decimal("86400")

        shared = {
            "fixture_id": fixture.fixture_id,
            "competition_id": fixture.competition_id,
            "season_id": fixture.season_id,
        }
        return [
            GeneratedFeature(
                "home_rest_days",
                rest(home_any),
                Decimal("1") if home_any else Decimal("0"),
                refs(home_any),
                team_id=fixture.home_team_id,
                **shared,
            ),
            GeneratedFeature(
                "away_rest_days",
                rest(away_any),
                Decimal("1") if away_any else Decimal("0"),
                refs(away_any),
                team_id=fixture.away_team_id,
                **shared,
            ),
            GeneratedFeature(
                "home_recent_home_fixture_count_5",
                len(home_split),
                Decimal("1"),
                refs(home_split),
                team_id=fixture.home_team_id,
                **shared,
            ),
            GeneratedFeature(
                "away_recent_away_fixture_count_5",
                len(away_split),
                Decimal("1"),
                refs(away_split),
                team_id=fixture.away_team_id,
                **shared,
            ),
        ]
