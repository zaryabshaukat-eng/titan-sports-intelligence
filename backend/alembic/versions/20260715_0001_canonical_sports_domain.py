"""Create the canonical, provider-neutral Sports domain.

Revision ID: 20260715_0001
Revises:
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260715_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


competition_type = sa.Enum(
    "league", "cup", "tournament", "playoff", "friendly", "other", name="sports_competition_type"
)
season_status = sa.Enum("planned", "active", "completed", "cancelled", name="sports_season_status")
team_type = sa.Enum("club", "national", "representative", "other", name="sports_team_type")
official_role = sa.Enum(
    "referee",
    "assistant_referee",
    "fourth_official",
    "video_assistant",
    "other",
    name="sports_official_role",
)

UUID = postgresql.UUID(as_uuid=True)
TIMESTAMP = sa.DateTime(timezone=True)


def audit_columns(*, soft_delete: bool = False) -> list[sa.Column[object]]:
    """Return the consistent audit fields applied to canonical entities."""
    columns: list[sa.Column[object]] = [
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "created_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
    ]
    if soft_delete:
        columns.append(sa.Column("deleted_at", TIMESTAMP, nullable=True))
    return columns


def upgrade() -> None:
    """Create canonical sports tables, constraints, indexes, and status taxonomy."""
    bind = op.get_bind()
    competition_type.create(bind, checkfirst=True)
    season_status.create(bind, checkfirst=True)
    team_type.create(bind, checkfirst=True)
    official_role.create(bind, checkfirst=True)

    op.create_table(
        "sports_timezones",
        *audit_columns(),
        sa.Column("iana_name", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint(
            "char_length(iana_name) >= 3", name="ck_sports_timezones_iana_name_length"
        ),
        sa.UniqueConstraint("iana_name", name="uq_sports_timezones_iana_name"),
    )

    op.create_table(
        "sports_countries",
        *audit_columns(soft_delete=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("iso_code", sa.String(length=2), nullable=False),
        sa.Column("iso3_code", sa.String(length=3), nullable=True),
        sa.CheckConstraint("char_length(iso_code) = 2", name="ck_sports_countries_iso_code_length"),
        sa.CheckConstraint("iso_code = upper(iso_code)", name="ck_sports_countries_iso_code_upper"),
        sa.CheckConstraint(
            "iso3_code IS NULL OR char_length(iso3_code) = 3",
            name="ck_sports_countries_iso3_code_length",
        ),
        sa.CheckConstraint(
            "iso3_code IS NULL OR iso3_code = upper(iso3_code)",
            name="ck_sports_countries_iso3_code_upper",
        ),
        sa.UniqueConstraint("name", name="uq_sports_countries_name"),
        sa.UniqueConstraint("iso_code", name="uq_sports_countries_iso_code"),
        sa.UniqueConstraint("iso3_code", name="uq_sports_countries_iso3_code"),
    )
    op.create_index("ix_sports_countries_deleted_at", "sports_countries", ["deleted_at"])

    op.create_table(
        "sports_country_timezones",
        *audit_columns(),
        sa.Column("country_id", UUID, nullable=False),
        sa.Column("timezone_id", UUID, nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["country_id"], ["sports_countries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timezone_id"], ["sports_timezones.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "country_id", "timezone_id", name="uq_sports_country_timezones_country_timezone"
        ),
    )
    op.create_index(
        "ix_sports_country_timezones_country_id", "sports_country_timezones", ["country_id"]
    )
    op.create_index(
        "ix_sports_country_timezones_timezone_id", "sports_country_timezones", ["timezone_id"]
    )
    op.create_index(
        "uq_sports_country_timezones_one_primary",
        "sports_country_timezones",
        ["country_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )

    op.create_table(
        "sports_leagues",
        *audit_columns(soft_delete=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("short_name", sa.String(length=64), nullable=True),
        sa.Column("sport", sa.String(length=32), nullable=False),
        sa.Column("country_id", UUID, nullable=True),
        sa.CheckConstraint("char_length(sport) >= 2", name="ck_sports_leagues_sport_length"),
        sa.ForeignKeyConstraint(["country_id"], ["sports_countries.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "country_id", "sport", "name", name="uq_sports_leagues_country_sport_name"
        ),
    )
    op.create_index("ix_sports_leagues_country_id", "sports_leagues", ["country_id"])
    op.create_index("ix_sports_leagues_deleted_at", "sports_leagues", ["deleted_at"])
    op.create_index("ix_sports_leagues_name", "sports_leagues", ["name"])
    op.create_index("ix_sports_leagues_sport", "sports_leagues", ["sport"])

    op.create_table(
        "sports_competitions",
        *audit_columns(soft_delete=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("short_name", sa.String(length=64), nullable=True),
        sa.Column("sport", sa.String(length=32), nullable=False),
        sa.Column("competition_type", competition_type, nullable=False),
        sa.Column("league_id", UUID, nullable=True),
        sa.Column("country_id", UUID, nullable=True),
        sa.Column("default_timezone_id", UUID, nullable=True),
        sa.CheckConstraint("char_length(sport) >= 2", name="ck_sports_competitions_sport_length"),
        sa.ForeignKeyConstraint(["league_id"], ["sports_leagues.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["country_id"], ["sports_countries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["default_timezone_id"], ["sports_timezones.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("league_id", "name", name="uq_sports_competitions_league_name"),
    )
    op.create_index(
        "ix_sports_competitions_competition_type", "sports_competitions", ["competition_type"]
    )
    op.create_index("ix_sports_competitions_country_id", "sports_competitions", ["country_id"])
    op.create_index(
        "ix_sports_competitions_default_timezone_id", "sports_competitions", ["default_timezone_id"]
    )
    op.create_index("ix_sports_competitions_deleted_at", "sports_competitions", ["deleted_at"])
    op.create_index("ix_sports_competitions_league_id", "sports_competitions", ["league_id"])
    op.create_index("ix_sports_competitions_name", "sports_competitions", ["name"])
    op.create_index("ix_sports_competitions_sport", "sports_competitions", ["sport"])

    op.create_table(
        "sports_seasons",
        *audit_columns(soft_delete=True),
        sa.Column("competition_id", UUID, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", season_status, nullable=False),
        sa.CheckConstraint("start_date <= end_date", name="ck_sports_seasons_date_range"),
        sa.ForeignKeyConstraint(
            ["competition_id"], ["sports_competitions.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("competition_id", "name", name="uq_sports_seasons_competition_name"),
    )
    op.create_index("ix_sports_seasons_competition_id", "sports_seasons", ["competition_id"])
    op.create_index("ix_sports_seasons_deleted_at", "sports_seasons", ["deleted_at"])
    op.create_index("ix_sports_seasons_status", "sports_seasons", ["status"])

    op.create_table(
        "sports_venues",
        *audit_columns(soft_delete=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("country_id", UUID, nullable=True),
        sa.Column("timezone_id", UUID, nullable=True),
        sa.CheckConstraint("capacity IS NULL OR capacity >= 0", name="ck_sports_venues_capacity"),
        sa.ForeignKeyConstraint(["country_id"], ["sports_countries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["timezone_id"], ["sports_timezones.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("country_id", "name", name="uq_sports_venues_country_name"),
    )
    op.create_index("ix_sports_venues_city", "sports_venues", ["city"])
    op.create_index("ix_sports_venues_country_id", "sports_venues", ["country_id"])
    op.create_index("ix_sports_venues_deleted_at", "sports_venues", ["deleted_at"])
    op.create_index("ix_sports_venues_name", "sports_venues", ["name"])
    op.create_index("ix_sports_venues_timezone_id", "sports_venues", ["timezone_id"])

    op.create_table(
        "sports_teams",
        *audit_columns(soft_delete=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("short_name", sa.String(length=64), nullable=True),
        sa.Column("sport", sa.String(length=32), nullable=False),
        sa.Column("team_type", team_type, nullable=False),
        sa.Column("founded_year", sa.SmallInteger(), nullable=True),
        sa.Column("country_id", UUID, nullable=True),
        sa.Column("home_venue_id", UUID, nullable=True),
        sa.CheckConstraint(
            "founded_year IS NULL OR founded_year > 0", name="ck_sports_teams_founded_year"
        ),
        sa.CheckConstraint("char_length(sport) >= 2", name="ck_sports_teams_sport_length"),
        sa.ForeignKeyConstraint(["country_id"], ["sports_countries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["home_venue_id"], ["sports_venues.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "country_id", "sport", "name", name="uq_sports_teams_country_sport_name"
        ),
    )
    op.create_index("ix_sports_teams_country_id", "sports_teams", ["country_id"])
    op.create_index("ix_sports_teams_deleted_at", "sports_teams", ["deleted_at"])
    op.create_index("ix_sports_teams_home_venue_id", "sports_teams", ["home_venue_id"])
    op.create_index("ix_sports_teams_name", "sports_teams", ["name"])
    op.create_index("ix_sports_teams_sport", "sports_teams", ["sport"])
    op.create_index("ix_sports_teams_team_type", "sports_teams", ["team_type"])

    op.create_table(
        "sports_fixture_statuses",
        *audit_columns(),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_terminal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), server_default="0", nullable=False),
        sa.CheckConstraint("sort_order >= 0", name="ck_sports_fixture_statuses_sort_order"),
        sa.UniqueConstraint("code", name="uq_sports_fixture_statuses_code"),
    )

    fixture_status_table = sa.table(
        "sports_fixture_statuses",
        sa.column("id", UUID),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_terminal", sa.Boolean()),
        sa.column("sort_order", sa.SmallInteger()),
    )
    op.bulk_insert(
        fixture_status_table,
        [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "code": "scheduled",
                "name": "Scheduled",
                "description": "Fixture is scheduled.",
                "is_terminal": False,
                "sort_order": 0,
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "code": "delayed",
                "name": "Delayed",
                "description": "Fixture start is delayed.",
                "is_terminal": False,
                "sort_order": 10,
            },
            {
                "id": "00000000-0000-0000-0000-000000000003",
                "code": "postponed",
                "name": "Postponed",
                "description": "Fixture has been postponed.",
                "is_terminal": False,
                "sort_order": 20,
            },
            {
                "id": "00000000-0000-0000-0000-000000000004",
                "code": "live",
                "name": "Live",
                "description": "Fixture is in progress.",
                "is_terminal": False,
                "sort_order": 30,
            },
            {
                "id": "00000000-0000-0000-0000-000000000005",
                "code": "halftime",
                "name": "Halftime",
                "description": "Fixture is at halftime or an interval.",
                "is_terminal": False,
                "sort_order": 40,
            },
            {
                "id": "00000000-0000-0000-0000-000000000006",
                "code": "finished",
                "name": "Finished",
                "description": "Fixture completed normally.",
                "is_terminal": True,
                "sort_order": 50,
            },
            {
                "id": "00000000-0000-0000-0000-000000000007",
                "code": "cancelled",
                "name": "Cancelled",
                "description": "Fixture was cancelled.",
                "is_terminal": True,
                "sort_order": 60,
            },
            {
                "id": "00000000-0000-0000-0000-000000000008",
                "code": "abandoned",
                "name": "Abandoned",
                "description": "Fixture was abandoned after scheduling or commencement.",
                "is_terminal": True,
                "sort_order": 70,
            },
        ],
    )

    op.create_table(
        "sports_fixtures",
        *audit_columns(),
        sa.Column("season_id", UUID, nullable=False),
        sa.Column("home_team_id", UUID, nullable=False),
        sa.Column("away_team_id", UUID, nullable=False),
        sa.Column("fixture_status_id", UUID, nullable=False),
        sa.Column("venue_id", UUID, nullable=True),
        sa.Column("timezone_id", UUID, nullable=True),
        sa.Column("scheduled_start_at", TIMESTAMP, nullable=False),
        sa.Column("scheduled_end_at", TIMESTAMP, nullable=True),
        sa.Column("round_name", sa.String(length=128), nullable=True),
        sa.Column("stage_name", sa.String(length=128), nullable=True),
        sa.CheckConstraint(
            "home_team_id <> away_team_id", name="ck_sports_fixtures_distinct_teams"
        ),
        sa.CheckConstraint(
            "scheduled_end_at IS NULL OR scheduled_end_at >= scheduled_start_at",
            name="ck_sports_fixtures_schedule_range",
        ),
        sa.ForeignKeyConstraint(["season_id"], ["sports_seasons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["home_team_id"], ["sports_teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["away_team_id"], ["sports_teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["fixture_status_id"], ["sports_fixture_statuses.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["venue_id"], ["sports_venues.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["timezone_id"], ["sports_timezones.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "season_id",
            "home_team_id",
            "away_team_id",
            "scheduled_start_at",
            name="uq_sports_fixtures_season_teams_start",
        ),
    )
    op.create_index("ix_sports_fixtures_away_team_id", "sports_fixtures", ["away_team_id"])
    op.create_index(
        "ix_sports_fixtures_fixture_status_id", "sports_fixtures", ["fixture_status_id"]
    )
    op.create_index("ix_sports_fixtures_home_team_id", "sports_fixtures", ["home_team_id"])
    op.create_index(
        "ix_sports_fixtures_scheduled_start_at", "sports_fixtures", ["scheduled_start_at"]
    )
    op.create_index("ix_sports_fixtures_season_id", "sports_fixtures", ["season_id"])
    op.create_index(
        "ix_sports_fixtures_status_start",
        "sports_fixtures",
        ["fixture_status_id", "scheduled_start_at"],
    )
    op.create_index("ix_sports_fixtures_timezone_id", "sports_fixtures", ["timezone_id"])
    op.create_index("ix_sports_fixtures_venue_id", "sports_fixtures", ["venue_id"])

    op.create_table(
        "sports_officials",
        *audit_columns(soft_delete=True),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("country_id", UUID, nullable=True),
        sa.ForeignKeyConstraint(["country_id"], ["sports_countries.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_sports_officials_country_id", "sports_officials", ["country_id"])
    op.create_index("ix_sports_officials_deleted_at", "sports_officials", ["deleted_at"])
    op.create_index("ix_sports_officials_full_name", "sports_officials", ["full_name"])

    op.create_table(
        "sports_fixture_officials",
        *audit_columns(),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("official_id", UUID, nullable=False),
        sa.Column("role", official_role, nullable=False),
        sa.Column("assignment_order", sa.SmallInteger(), server_default="0", nullable=False),
        sa.CheckConstraint(
            "assignment_order >= 0", name="ck_sports_fixture_officials_assignment_order"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["official_id"], ["sports_officials.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "fixture_id", "official_id", name="uq_sports_fixture_officials_fixture_official"
        ),
        sa.UniqueConstraint(
            "fixture_id",
            "role",
            "assignment_order",
            name="uq_sports_fixture_officials_fixture_role_order",
        ),
    )
    op.create_index(
        "ix_sports_fixture_officials_fixture_id", "sports_fixture_officials", ["fixture_id"]
    )
    op.create_index(
        "ix_sports_fixture_officials_official_id", "sports_fixture_officials", ["official_id"]
    )
    op.create_index("ix_sports_fixture_officials_role", "sports_fixture_officials", ["role"])

    op.create_table(
        "sports_fixture_status_history",
        *audit_columns(),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("fixture_status_id", UUID, nullable=False),
        sa.Column("effective_at", TIMESTAMP, nullable=False),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["fixture_status_id"], ["sports_fixture_statuses.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "fixture_id",
            "fixture_status_id",
            "effective_at",
            name="uq_sports_fixture_status_history_transition",
        ),
    )
    op.create_index(
        "ix_sports_fixture_status_history_fixture_id",
        "sports_fixture_status_history",
        ["fixture_id"],
    )
    op.create_index(
        "ix_sports_fixture_status_history_fixture_effective",
        "sports_fixture_status_history",
        ["fixture_id", "effective_at"],
    )
    op.create_index(
        "ix_sports_fixture_status_history_fixture_status_id",
        "sports_fixture_status_history",
        ["fixture_status_id"],
    )


def downgrade() -> None:
    """Remove sports tables and their controlled-vocabulary enum types."""
    op.drop_table("sports_fixture_status_history")
    op.drop_table("sports_fixture_officials")
    op.drop_table("sports_officials")
    op.drop_table("sports_fixtures")
    op.drop_table("sports_fixture_statuses")
    op.drop_table("sports_teams")
    op.drop_table("sports_venues")
    op.drop_table("sports_seasons")
    op.drop_table("sports_competitions")
    op.drop_table("sports_leagues")
    op.drop_table("sports_country_timezones")
    op.drop_table("sports_countries")
    op.drop_table("sports_timezones")

    bind = op.get_bind()
    official_role.drop(bind, checkfirst=True)
    team_type.drop(bind, checkfirst=True)
    season_status.drop(bind, checkfirst=True)
    competition_type.drop(bind, checkfirst=True)
