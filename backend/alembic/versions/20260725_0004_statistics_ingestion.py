"""Create the immutable Statistics Ingestion bounded context.

Revision ID: 20260725_0004
Revises: 20260725_0003
"""

# ruff: noqa: E501, E701, E702
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260725_0004"
down_revision: str | None = "20260725_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()
TS = sa.DateTime(timezone=True)
RUN = postgresql.ENUM(
    "running",
    "completed",
    "completed_with_errors",
    "failed",
    name="statistics_run_status",
    create_type=False,
)
RAW = postgresql.ENUM(
    "received",
    "valid",
    "invalid",
    "applied",
    name="statistics_raw_payload_status",
    create_type=False,
)
AUDIT = postgresql.ENUM(
    "processed",
    "unchanged",
    "validation_failed",
    name="statistics_audit_outcome",
    create_type=False,
)
SCOPE = postgresql.ENUM("fixture", "team", "player", name="statistics_scope", create_type=False)
MAPPING = postgresql.ENUM(
    "fixture",
    "team",
    "player",
    "category",
    name="statistics_mapping_entity_type",
    create_type=False,
)
EVENT = postgresql.ENUM(
    "StatisticsIngested",
    "StatisticsUpdated",
    "StatisticsValidationFailed",
    name="statistics_event_type",
    create_type=False,
)


def cols() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", TS, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for item in (RUN, RAW, AUDIT, SCOPE, MAPPING, EVENT):
        item.create(bind, checkfirst=True)
    op.create_table(
        "statistics_providers",
        *cols(),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
    )
    op.create_table(
        "statistics_categories",
        *cols(),
        sa.Column("code", sa.String(96), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("value_schema", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
    )
    op.create_table(
        "statistics_versions",
        *cols(),
        sa.Column(
            "provider_id",
            UUID,
            sa.ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            UUID,
            sa.ForeignKey("statistics_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("schema", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.UniqueConstraint(
            "provider_id",
            "category_id",
            "version",
            name="uq_statistics_versions_provider_category_version",
        ),
    )
    op.create_table(
        "statistics_fixture_statistics",
        *cols(),
        sa.Column(
            "fixture_id",
            UUID,
            sa.ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            UUID,
            sa.ForeignKey("statistics_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            UUID,
            sa.ForeignKey("statistics_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "fixture_id", "category_id", "version_id", name="uq_statistics_fixture_series"
        ),
    )
    op.create_table(
        "statistics_team_statistics",
        *cols(),
        sa.Column(
            "fixture_id",
            UUID,
            sa.ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "team_id", UUID, sa.ForeignKey("sports_teams.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "category_id",
            UUID,
            sa.ForeignKey("statistics_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            UUID,
            sa.ForeignKey("statistics_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "fixture_id", "team_id", "category_id", "version_id", name="uq_statistics_team_series"
        ),
    )
    op.create_table(
        "statistics_players",
        *cols(),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("birth_date", sa.String(10)),
        sa.Column("nationality", sa.String(2)),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.UniqueConstraint("name", "birth_date", name="uq_statistics_players_name_birth_date"),
    )
    op.create_table(
        "statistics_player_statistics",
        *cols(),
        sa.Column(
            "fixture_id",
            UUID,
            sa.ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "player_id",
            UUID,
            sa.ForeignKey("statistics_players.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("team_id", UUID, sa.ForeignKey("sports_teams.id", ondelete="RESTRICT")),
        sa.Column(
            "category_id",
            UUID,
            sa.ForeignKey("statistics_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            UUID,
            sa.ForeignKey("statistics_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "fixture_id",
            "player_id",
            "category_id",
            "version_id",
            name="uq_statistics_player_series",
        ),
    )
    op.create_table(
        "statistics_ingestion_runs",
        *cols(),
        sa.Column(
            "provider_id",
            UUID,
            sa.ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", RUN, nullable=False),
        sa.Column("started_at", TS, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("completed_at", TS),
        sa.Column("received_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("snapshots_created_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer, server_default="0", nullable=False),
    )
    op.create_table(
        "statistics_raw_payloads",
        *cols(),
        sa.Column(
            "ingestion_run_id",
            UUID,
            sa.ForeignKey("statistics_ingestion_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            UUID,
            sa.ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider_fixture_id", sa.String(128)),
        sa.Column("fixture_provider_name", sa.String(64)),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("validation_status", RAW, nullable=False),
        sa.Column("validation_errors", JSONB),
        sa.Column(
            "canonical_fixture_id", UUID, sa.ForeignKey("sports_fixtures.id", ondelete="RESTRICT")
        ),
        sa.Column("processed_at", TS),
        sa.UniqueConstraint(
            "provider_id", "idempotency_key", name="uq_statistics_raw_provider_key"
        ),
    )
    op.create_table(
        "statistics_provider_mappings",
        *cols(),
        sa.Column(
            "provider_id",
            UUID,
            sa.ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("entity_type", MAPPING, nullable=False),
        sa.Column("provider_entity_id", sa.String(128), nullable=False),
        sa.Column("canonical_entity_id", UUID, nullable=False),
        sa.UniqueConstraint(
            "provider_id",
            "entity_type",
            "provider_entity_id",
            name="uq_statistics_provider_mapping",
        ),
    )
    op.create_table(
        "statistics_snapshots",
        *cols(),
        sa.Column(
            "ingestion_run_id",
            UUID,
            sa.ForeignKey("statistics_ingestion_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "raw_payload_id",
            UUID,
            sa.ForeignKey("statistics_raw_payloads.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            UUID,
            sa.ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "fixture_id",
            UUID,
            sa.ForeignKey("sports_fixtures.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("scope", SCOPE, nullable=False),
        sa.Column("series_id", UUID, nullable=False),
        sa.Column(
            "fixture_statistic_id",
            UUID,
            sa.ForeignKey("statistics_fixture_statistics.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "team_statistic_id",
            UUID,
            sa.ForeignKey("statistics_team_statistics.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "player_statistic_id",
            UUID,
            sa.ForeignKey("statistics_player_statistics.id", ondelete="RESTRICT"),
        ),
        sa.Column("values", JSONB, nullable=False),
        sa.Column("observed_at", TS, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "(fixture_statistic_id IS NOT NULL)::int + (team_statistic_id IS NOT NULL)::int + (player_statistic_id IS NOT NULL)::int = 1",
            name="ck_statistics_snapshot_one_series",
        ),
        sa.UniqueConstraint(
            "provider_id",
            "scope",
            "series_id",
            "observed_at",
            "checksum",
            name="uq_statistics_snapshot_observation",
        ),
    )
    op.create_table(
        "statistics_audits",
        *cols(),
        sa.Column(
            "ingestion_run_id",
            UUID,
            sa.ForeignKey("statistics_ingestion_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "raw_payload_id",
            UUID,
            sa.ForeignKey("statistics_raw_payloads.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            UUID,
            sa.ForeignKey("statistics_providers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("outcome", AUDIT, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("changes", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("error_details", JSONB),
    )
    op.create_table(
        "statistics_outbox_events",
        *cols(),
        sa.Column(
            "ingestion_run_id",
            UUID,
            sa.ForeignKey("statistics_ingestion_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "raw_payload_id",
            UUID,
            sa.ForeignKey("statistics_raw_payloads.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("event_type", EVENT, nullable=False),
        sa.Column("event_key", sa.String(192), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("published_at", TS),
        sa.UniqueConstraint("event_type", "event_key", name="uq_statistics_outbox_event"),
    )
    for table, cols_ in {
        "statistics_categories": ["code"],
        "statistics_snapshots": ["fixture_id", "observed_at"],
        "statistics_raw_payloads": ["checksum"],
        "statistics_provider_mappings": ["canonical_entity_id"],
    }.items():
        op.create_index("ix_" + table + "_" + "_".join(cols_), table, cols_)


def downgrade() -> None:
    for table in (
        "statistics_outbox_events",
        "statistics_audits",
        "statistics_snapshots",
        "statistics_provider_mappings",
        "statistics_raw_payloads",
        "statistics_ingestion_runs",
        "statistics_player_statistics",
        "statistics_players",
        "statistics_team_statistics",
        "statistics_fixture_statistics",
        "statistics_versions",
        "statistics_categories",
        "statistics_providers",
    ):
        op.drop_table(table)
    bind = op.get_bind()
    for item in (EVENT, MAPPING, SCOPE, AUDIT, RAW, RUN):
        item.drop(bind, checkfirst=True)
