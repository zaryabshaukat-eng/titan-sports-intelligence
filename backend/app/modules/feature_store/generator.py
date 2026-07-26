"""Canonical-data-only source reader and generator result contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feature_store.metadata import fingerprint
from app.modules.market_data.models import OddsSnapshot
from app.modules.sports.models import Fixture, Season
from app.modules.statistics.models import StatisticSnapshot


@dataclass(frozen=True, slots=True)
class SourceReference:
    """One canonical database record used to calculate a feature value."""

    source_module: str
    source_entity_type: str
    source_record_id: UUID
    observed_at: datetime | None
    source_fingerprint: str | None = None


@dataclass(frozen=True, slots=True)
class FixtureContext:
    """Canonical target identity shared by all generators for a fixture regeneration run."""

    fixture_id: UUID
    home_team_id: UUID
    away_team_id: UUID
    competition_id: UUID
    season_id: UUID
    scheduled_start_at: datetime


@dataclass(frozen=True, slots=True)
class GeneratedFeature:
    """In-memory result before validation and append-only persistence."""

    feature_id: str
    value: object | None
    quality_score: Decimal
    sources: tuple[SourceReference, ...]
    fixture_id: UUID | None = None
    team_id: UUID | None = None
    player_id: UUID | None = None
    competition_id: UUID | None = None
    season_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class FeatureGenerationContext:
    """Input to plugins; all source access happens through this canonical reader."""

    fixture: FixtureContext
    as_of: datetime
    source_reader: CanonicalFeatureSourceReader


class CanonicalFeatureSourceReader:
    """Read only canonical Sports, Market Data, and Statistics records for generation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def fixture_context(self, fixture_id: UUID) -> FixtureContext | None:
        """Load the canonical fixture and its competition/season identity once per run."""
        statement = (
            select(Fixture, Season.competition_id)
            .join(Season, Season.id == Fixture.season_id)
            .where(Fixture.id == fixture_id)
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        fixture, competition_id = row
        return FixtureContext(
            fixture_id=fixture.id,
            home_team_id=fixture.home_team_id,
            away_team_id=fixture.away_team_id,
            competition_id=competition_id,
            season_id=fixture.season_id,
            scheduled_start_at=fixture.scheduled_start_at,
        )

    async def previous_team_fixtures(
        self, *, team_id: UUID, as_of: datetime, home_only: bool | None = None, limit: int = 5
    ) -> list[Fixture]:
        """Return chronologically recent canonical fixtures without reading provider identities."""
        statement = select(Fixture).where(Fixture.scheduled_start_at < as_of)
        if home_only is True:
            statement = statement.where(Fixture.home_team_id == team_id)
        elif home_only is False:
            statement = statement.where(Fixture.away_team_id == team_id)
        else:
            statement = statement.where(
                or_(Fixture.home_team_id == team_id, Fixture.away_team_id == team_id)
            )
        statement = statement.order_by(Fixture.scheduled_start_at.desc()).limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def latest_odds(self, *, fixture_id: UUID, as_of: datetime) -> list[OddsSnapshot]:
        """Return the latest immutable price per provider/bookmaker/selection as of the cutoff."""
        ranked = (
            select(
                OddsSnapshot.id.label("snapshot_id"),
                func.row_number()
                .over(
                    partition_by=(
                        OddsSnapshot.provider_name,
                        OddsSnapshot.bookmaker_id,
                        OddsSnapshot.selection_id,
                    ),
                    order_by=(OddsSnapshot.observed_at.desc(), OddsSnapshot.created_at.desc()),
                )
                .label("rank"),
            )
            .where(OddsSnapshot.fixture_id == fixture_id, OddsSnapshot.observed_at <= as_of)
            .subquery()
        )
        statement = (
            select(OddsSnapshot)
            .join(ranked, ranked.c.snapshot_id == OddsSnapshot.id)
            .where(ranked.c.rank == 1)
            .order_by(OddsSnapshot.observed_at.desc(), OddsSnapshot.created_at.desc())
        )
        return list((await self._session.scalars(statement)).all())

    async def statistic_history(
        self, *, fixture_id: UUID, as_of: datetime
    ) -> list[StatisticSnapshot]:
        """Return immutable statistic snapshots through the historical regeneration cutoff."""
        statement = (
            select(StatisticSnapshot)
            .where(
                StatisticSnapshot.fixture_id == fixture_id, StatisticSnapshot.observed_at <= as_of
            )
            .order_by(StatisticSnapshot.observed_at.desc(), StatisticSnapshot.created_at.desc())
        )
        return list((await self._session.scalars(statement)).all())


def source_from_fixture(fixture: Fixture) -> SourceReference:
    """Build immutable lineage for a canonical fixture row."""
    return SourceReference(
        source_module="sports",
        source_entity_type="fixture",
        source_record_id=fixture.id,
        observed_at=fixture.scheduled_start_at,
        source_fingerprint=fingerprint(
            {"id": fixture.id, "scheduled_start_at": fixture.scheduled_start_at}
        ),
    )
