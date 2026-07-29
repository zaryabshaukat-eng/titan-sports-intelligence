"""Create versioned, append-only Feature Store metadata, values, lineage, and validation evidence.

Revision ID: 20260726_0008
Revises: 20260725_0007
"""
# ruff: noqa: E501

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0008"
down_revision: str | None = "20260725_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

feature_type = postgresql.ENUM(
    "temporal",
    "team",
    "fixture",
    "market",
    "statistical",
    "player",
    name="feature_store_feature_type",
    create_type=False,
)
data_type = postgresql.ENUM(
    "number",
    "integer",
    "boolean",
    "string",
    "json",
    name="feature_store_data_type",
    create_type=False,
)
missing_policy = postgresql.ENUM(
    "reject", "null", "zero", name="feature_store_missing_value_policy", create_type=False
)
generation_status = postgresql.ENUM(
    "running", "completed", "failed", name="feature_store_generation_status", create_type=False
)
validation_status = postgresql.ENUM(
    "passed", "failed", name="feature_store_validation_status", create_type=False
)


def upgrade() -> None:
    """Create immutable Feature Store tables and read-path indexes without changing prior domains."""
    feature_type.create(op.get_bind(), checkfirst=True)
    data_type.create(op.get_bind(), checkfirst=True)
    missing_policy.create(op.get_bind(), checkfirst=True)
    generation_status.create(op.get_bind(), checkfirst=True)
    validation_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "feature_store_feature_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "feature_store_feature_set_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("feature_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("generator_version", sa.String(length=64), nullable=False),
        sa.Column("definition_checksum", sa.String(length=64), nullable=False),
        sa.Column("source_modules", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(
            ["feature_set_id"], ["feature_store_feature_sets.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feature_set_id", "version", name="uq_feature_store_set_version"),
    )
    op.create_index(
        "ix_feature_store_feature_set_versions_feature_set_id",
        "feature_store_feature_set_versions",
        ["feature_set_id"],
    )
    op.create_index(
        "ix_feature_store_set_versions_set_created",
        "feature_store_feature_set_versions",
        ["feature_set_id", "created_at"],
    )
    op.create_table(
        "feature_store_feature_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("feature_set_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.Column("source_modules", postgresql.JSONB(), nullable=False),
        sa.Column("dependencies", postgresql.JSONB(), nullable=False),
        sa.Column("calculation_logic", sa.Text(), nullable=False),
        sa.Column("feature_type", feature_type, nullable=False),
        sa.Column("data_type", data_type, nullable=False),
        sa.Column("missing_value_policy", missing_policy, nullable=False),
        sa.Column("validity_window_seconds", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "feature_set_version_id", "feature_id", name="uq_feature_store_definition_feature_id"
        ),
    )
    op.create_index(
        "ix_feature_store_feature_definitions_feature_set_version_id",
        "feature_store_feature_definitions",
        ["feature_set_version_id"],
    )
    op.create_index(
        "ix_feature_store_definitions_set_type",
        "feature_store_feature_definitions",
        ["feature_set_version_id", "feature_type"],
    )
    op.create_table(
        "feature_store_generation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("feature_set_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fixture_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generator_version", sa.String(length=64), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("status", generation_status, nullable=False),
        sa.Column("generated_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "generated_count >= 0", name="ck_feature_store_generation_generated_count"
        ),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_feature_store_generation_idempotency"),
    )
    op.create_index(
        "ix_feature_store_generation_runs_feature_set_version_id",
        "feature_store_generation_runs",
        ["feature_set_version_id"],
    )
    op.create_index(
        "ix_feature_store_generation_runs_fixture_id",
        "feature_store_generation_runs",
        ["fixture_id"],
    )
    op.create_index(
        "ix_feature_store_generation_fixture_asof",
        "feature_store_generation_runs",
        ["fixture_id", "as_of"],
    )
    op.create_index(
        "ix_feature_store_generation_set_status",
        "feature_store_generation_runs",
        ["feature_set_version_id", "status"],
    )
    op.create_table(
        "feature_store_feature_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("generation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fixture_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("competition_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("season_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("numeric_value", sa.Numeric(20, 8), nullable=True),
        sa.Column("quality_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(fixture_id IS NOT NULL)::int + (team_id IS NOT NULL)::int + (player_id IS NOT NULL)::int + (competition_id IS NOT NULL)::int + (season_id IS NOT NULL)::int >= 1",
            name="ck_feature_store_value_has_subject",
        ),
        sa.CheckConstraint(
            "quality_score >= 0 AND quality_score <= 1", name="ck_feature_store_value_quality"
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="ck_feature_store_value_validity_window",
        ),
        sa.ForeignKeyConstraint(
            ["generation_run_id"], ["feature_store_generation_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["feature_definition_id"], ["feature_store_feature_definitions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["sports_teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["player_id"], ["statistics_players.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["competition_id"], ["sports_competitions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["season_id"], ["sports_seasons.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "generation_run_id", "feature_definition_id", name="uq_feature_store_run_definition"
        ),
    )
    op.create_index(
        "ix_feature_store_feature_values_generation_run_id",
        "feature_store_feature_values",
        ["generation_run_id"],
    )
    op.create_index(
        "ix_feature_store_feature_values_feature_definition_id",
        "feature_store_feature_values",
        ["feature_definition_id"],
    )
    op.create_index(
        "ix_feature_store_values_fixture_definition_observed",
        "feature_store_feature_values",
        ["fixture_id", "feature_definition_id", sa.text("observed_at DESC")],
    )
    op.create_index(
        "ix_feature_store_values_team_observed",
        "feature_store_feature_values",
        ["team_id", sa.text("observed_at DESC")],
    )
    op.create_index(
        "ix_feature_store_values_player_observed",
        "feature_store_feature_values",
        ["player_id", sa.text("observed_at DESC")],
    )
    op.create_index(
        "ix_feature_store_values_competition_observed",
        "feature_store_feature_values",
        ["competition_id", sa.text("observed_at DESC")],
    )
    op.create_index(
        "ix_feature_store_values_season_observed",
        "feature_store_feature_values",
        ["season_id", sa.text("observed_at DESC")],
    )
    op.create_table(
        "feature_store_lineage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("feature_value_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_module", sa.String(length=64), nullable=False),
        sa.Column("source_entity_type", sa.String(length=96), nullable=False),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("calculation_logic", sa.Text(), nullable=False),
        sa.Column("generator_version", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["feature_value_id"], ["feature_store_feature_values.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "feature_value_id",
            "source_module",
            "source_entity_type",
            "source_record_id",
            name="uq_feature_store_lineage_source",
        ),
    )
    op.create_index(
        "ix_feature_store_lineage_feature", "feature_store_lineage", ["feature_value_id"]
    )
    op.create_index(
        "ix_feature_store_lineage_source",
        "feature_store_lineage",
        ["source_module", "source_record_id"],
    )
    op.create_table(
        "feature_store_validation_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("generation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_value_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rule_name", sa.String(length=96), nullable=False),
        sa.Column("status", validation_status, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["generation_run_id"], ["feature_store_generation_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["feature_definition_id"], ["feature_store_feature_definitions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["feature_value_id"], ["feature_store_feature_values.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "generation_run_id",
            "feature_definition_id",
            "rule_name",
            name="uq_feature_store_validation_rule",
        ),
    )
    op.create_index(
        "ix_feature_store_validation_run", "feature_store_validation_records", ["generation_run_id"]
    )
    op.execute(
        """
        CREATE FUNCTION feature_store_reject_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Feature Store historical records are immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table_name in (
        "feature_store_feature_set_versions",
        "feature_store_feature_definitions",
        "feature_store_feature_values",
        "feature_store_lineage",
        "feature_store_validation_records",
    ):
        op.execute(
            f"CREATE TRIGGER {table_name}_immutable "
            f"BEFORE UPDATE OR DELETE ON {table_name} "
            "FOR EACH ROW EXECUTE FUNCTION feature_store_reject_mutation()"
        )


def downgrade() -> None:
    """Remove only Feature Store structures in reverse dependency order."""
    op.drop_index("ix_feature_store_validation_run", table_name="feature_store_validation_records")
    op.drop_table("feature_store_validation_records")
    op.drop_index("ix_feature_store_lineage_source", table_name="feature_store_lineage")
    op.drop_index("ix_feature_store_lineage_feature", table_name="feature_store_lineage")
    op.drop_table("feature_store_lineage")
    for name in (
        "ix_feature_store_values_season_observed",
        "ix_feature_store_values_competition_observed",
        "ix_feature_store_values_player_observed",
        "ix_feature_store_values_team_observed",
        "ix_feature_store_values_fixture_definition_observed",
        "ix_feature_store_feature_values_feature_definition_id",
        "ix_feature_store_feature_values_generation_run_id",
    ):
        op.drop_index(name, table_name="feature_store_feature_values")
    op.drop_table("feature_store_feature_values")
    for name in (
        "ix_feature_store_generation_set_status",
        "ix_feature_store_generation_fixture_asof",
        "ix_feature_store_generation_runs_fixture_id",
        "ix_feature_store_generation_runs_feature_set_version_id",
    ):
        op.drop_index(name, table_name="feature_store_generation_runs")
    op.drop_table("feature_store_generation_runs")
    op.drop_index(
        "ix_feature_store_definitions_set_type", table_name="feature_store_feature_definitions"
    )
    op.drop_index(
        "ix_feature_store_feature_definitions_feature_set_version_id",
        table_name="feature_store_feature_definitions",
    )
    op.drop_table("feature_store_feature_definitions")
    op.drop_index(
        "ix_feature_store_set_versions_set_created", table_name="feature_store_feature_set_versions"
    )
    op.drop_index(
        "ix_feature_store_feature_set_versions_feature_set_id",
        table_name="feature_store_feature_set_versions",
    )
    op.drop_table("feature_store_feature_set_versions")
    op.drop_table("feature_store_feature_sets")
    op.execute("DROP FUNCTION feature_store_reject_mutation()")
    validation_status.drop(op.get_bind(), checkfirst=True)
    generation_status.drop(op.get_bind(), checkfirst=True)
    missing_policy.drop(op.get_bind(), checkfirst=True)
    data_type.drop(op.get_bind(), checkfirst=True)
    feature_type.drop(op.get_bind(), checkfirst=True)
