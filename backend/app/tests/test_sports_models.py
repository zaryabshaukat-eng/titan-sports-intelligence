"""Unit tests for canonical Sports metadata and relationship configuration."""

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from app.modules.sports.models import Base, Country, Fixture, FixtureOfficial, FixtureStatus, Season


def test_sports_models_configure_all_relationships() -> None:
    """Relationship paths are valid before any provider data reaches the domain."""
    configure_mappers()
    assert "sports_fixtures" in Base.metadata.tables
    assert Country.__mapper__.relationships["timezone_links"].uselist is True
    assert Fixture.__mapper__.relationships["home_team"].uselist is False
    assert FixtureOfficial.__mapper__.relationships["official"].uselist is False


def test_sports_models_define_canonical_integrity_constraints() -> None:
    """Critical constraints prevent invalid temporal and fixture identity records."""
    fixture_checks = {
        constraint.name
        for constraint in Fixture.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    season_uniques = {
        constraint.name
        for constraint in Season.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert "ck_sports_fixtures_distinct_teams" in fixture_checks
    assert "ck_sports_fixtures_schedule_range" in fixture_checks
    assert "uq_sports_seasons_competition_name" in season_uniques
    assert FixtureStatus.__table__.primary_key.columns.keys() == ["id"]
