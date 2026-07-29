"""Create immutable Research Engine dataset, experiment, hypothesis, lineage, and validation records.

Revision ID: 20260726_0009
Revises: 20260726_0008
"""
# ruff: noqa: E501

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0009"
down_revision: str | None = "20260726_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

experiment_status = postgresql.ENUM(
    "completed", "validation_failed", name="research_experiment_status", create_type=False
)
analysis_type = postgresql.ENUM(
    "descriptive",
    "correlation",
    "distribution",
    "significance",
    name="research_analysis_type",
    create_type=False,
)
hypothesis_decision = postgresql.ENUM(
    "supported", "rejected", "inconclusive", name="research_hypothesis_decision", create_type=False
)
validation_status = postgresql.ENUM(
    "passed", "failed", name="research_validation_status", create_type=False
)
UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()
TIMESTAMP = sa.DateTime(timezone=True)


def _base_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "created_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
    ]


def upgrade() -> None:
    """Create the Research bounded context without altering Feature Store or source-domain tables."""
    bind = op.get_bind()
    for item in (experiment_status, analysis_type, hypothesis_decision, validation_status):
        item.create(bind, checkfirst=True)

    op.create_table(
        "research_dataset_snapshots",
        *_base_columns(),
        sa.Column("dataset_code", sa.String(96), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("owner", sa.String(128), nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("selection", JSONB, nullable=False),
        sa.Column("generator_versions", JSONB, nullable=False),
        sa.Column("source_value_count", sa.Integer, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "source_value_count >= 0", name="ck_research_dataset_source_value_count"
        ),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_code", "version", name="uq_research_dataset_code_version"),
        sa.UniqueConstraint("idempotency_key", name="uq_research_dataset_idempotency"),
    )
    op.create_index(
        "ix_research_dataset_snapshots_feature_set_version_id",
        "research_dataset_snapshots",
        ["feature_set_version_id"],
    )
    op.create_index(
        "ix_research_datasets_feature_set_created",
        "research_dataset_snapshots",
        ["feature_set_version_id", "created_at"],
    )

    op.create_table(
        "research_dataset_snapshot_rows",
        *_base_columns(),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("source_feature_value_id", UUID, nullable=False),
        sa.Column("feature_definition_id", UUID, nullable=False),
        sa.Column("feature_id", sa.String(128), nullable=False),
        sa.Column("fixture_id", UUID, nullable=True),
        sa.Column("team_id", UUID, nullable=True),
        sa.Column("player_id", UUID, nullable=True),
        sa.Column("competition_id", UUID, nullable=True),
        sa.Column("season_id", UUID, nullable=True),
        sa.Column("value", JSONB, nullable=True),
        sa.Column("numeric_value", sa.Numeric(20, 8), nullable=True),
        sa.Column("observed_at", TIMESTAMP, nullable=False),
        sa.Column("calculated_at", TIMESTAMP, nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["research_dataset_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_feature_value_id"], ["feature_store_feature_values.id"], ondelete="RESTRICT"
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
            "dataset_snapshot_id",
            "source_feature_value_id",
            name="uq_research_dataset_source_value",
        ),
    )
    op.create_index(
        "ix_research_dataset_snapshot_rows_dataset_snapshot_id",
        "research_dataset_snapshot_rows",
        ["dataset_snapshot_id"],
    )
    op.create_index(
        "ix_research_dataset_rows_snapshot_feature",
        "research_dataset_snapshot_rows",
        ["dataset_snapshot_id", "feature_id"],
    )
    op.create_index(
        "ix_research_dataset_rows_snapshot_fixture",
        "research_dataset_snapshot_rows",
        ["dataset_snapshot_id", "fixture_id"],
    )
    op.create_index(
        "ix_research_dataset_rows_snapshot_team",
        "research_dataset_snapshot_rows",
        ["dataset_snapshot_id", "team_id"],
    )

    op.create_table(
        "research_experiments",
        *_base_columns(),
        sa.Column("experiment_code", sa.String(96), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("owner", sa.String(128), nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("generator_versions", JSONB, nullable=False),
        sa.Column("parameters", JSONB, nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.Column("status", experiment_status, nullable=False),
        sa.Column("input_checksum", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["research_dataset_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("experiment_code", name="uq_research_experiment_code"),
        sa.UniqueConstraint("idempotency_key", name="uq_research_experiment_idempotency"),
    )
    op.create_index(
        "ix_research_experiments_feature_set_version_id",
        "research_experiments",
        ["feature_set_version_id"],
    )
    op.create_index(
        "ix_research_experiments_dataset_snapshot_id",
        "research_experiments",
        ["dataset_snapshot_id"],
    )
    op.create_index(
        "ix_research_experiments_dataset_created",
        "research_experiments",
        ["dataset_snapshot_id", "created_at"],
    )
    op.create_index(
        "ix_research_experiments_feature_set_created",
        "research_experiments",
        ["feature_set_version_id", "created_at"],
    )

    op.create_table(
        "research_experiment_statistic_results",
        *_base_columns(),
        sa.Column("experiment_id", UUID, nullable=False),
        sa.Column("result_key", sa.String(160), nullable=False),
        sa.Column("analysis_type", analysis_type, nullable=False),
        sa.Column("feature_id", sa.String(128), nullable=False),
        sa.Column("related_feature_id", sa.String(128), nullable=True),
        sa.Column("method", sa.String(96), nullable=False),
        sa.Column("values", JSONB, nullable=False),
        sa.Column("numeric_value", sa.Numeric(20, 8), nullable=True),
        sa.Column("sample_size", sa.Integer, nullable=False),
        sa.Column("confidence_interval_low", sa.Numeric(20, 8), nullable=True),
        sa.Column("confidence_interval_high", sa.Numeric(20, 8), nullable=True),
        sa.Column("p_value", sa.Numeric(20, 8), nullable=True),
        sa.CheckConstraint("sample_size >= 0", name="ck_research_result_sample_size"),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["research_experiments.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "experiment_id", "result_key", name="uq_research_experiment_result_key"
        ),
    )
    op.create_index(
        "ix_research_experiment_statistic_results_experiment_id",
        "research_experiment_statistic_results",
        ["experiment_id"],
    )
    op.create_index(
        "ix_research_results_experiment_analysis",
        "research_experiment_statistic_results",
        ["experiment_id", "analysis_type"],
    )

    op.create_table(
        "research_hypotheses",
        *_base_columns(),
        sa.Column("hypothesis_code", sa.String(96), nullable=False),
        sa.Column("statement", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("owner", sa.String(128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hypothesis_code", name="uq_research_hypothesis_code"),
    )

    op.create_table(
        "research_hypothesis_evaluations",
        *_base_columns(),
        sa.Column("hypothesis_id", UUID, nullable=False),
        sa.Column("experiment_id", UUID, nullable=False),
        sa.Column("statistic_result_id", UUID, nullable=True),
        sa.Column("result", sa.Text, nullable=False),
        sa.Column("evidence", JSONB, nullable=False),
        sa.Column("statistical_significance", sa.Boolean, nullable=True),
        sa.Column("p_value", sa.Numeric(20, 8), nullable=True),
        sa.Column("decision", hypothesis_decision, nullable=False),
        sa.CheckConstraint(
            "p_value IS NULL OR (p_value >= 0 AND p_value <= 1)",
            name="ck_research_hypothesis_p_value",
        ),
        sa.ForeignKeyConstraint(["hypothesis_id"], ["research_hypotheses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["research_experiments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["statistic_result_id"],
            ["research_experiment_statistic_results.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "hypothesis_id", "experiment_id", name="uq_research_hypothesis_experiment"
        ),
    )
    op.create_index(
        "ix_research_hypothesis_evaluations_hypothesis_id",
        "research_hypothesis_evaluations",
        ["hypothesis_id"],
    )
    op.create_index(
        "ix_research_hypothesis_evaluations_experiment",
        "research_hypothesis_evaluations",
        ["experiment_id"],
    )

    op.create_table(
        "research_experiment_lineage",
        *_base_columns(),
        sa.Column("experiment_id", UUID, nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("generator_versions", JSONB, nullable=False),
        sa.Column("parameters_checksum", sa.String(64), nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["research_experiments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["research_dataset_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("experiment_id", name="uq_research_experiment_lineage"),
    )

    op.create_table(
        "research_experiment_validation_records",
        *_base_columns(),
        sa.Column("experiment_id", UUID, nullable=False),
        sa.Column("rule_name", sa.String(96), nullable=False),
        sa.Column("status", validation_status, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["research_experiments.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "experiment_id", "rule_name", name="uq_research_experiment_validation_rule"
        ),
    )
    op.create_index(
        "ix_research_validation_experiment",
        "research_experiment_validation_records",
        ["experiment_id"],
    )

    op.execute(
        """
        CREATE FUNCTION research_reject_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Research historical records are immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table_name in (
        "research_dataset_snapshots",
        "research_dataset_snapshot_rows",
        "research_experiments",
        "research_experiment_statistic_results",
        "research_hypotheses",
        "research_hypothesis_evaluations",
        "research_experiment_lineage",
        "research_experiment_validation_records",
    ):
        op.execute(
            f"CREATE TRIGGER {table_name}_immutable "
            f"BEFORE UPDATE OR DELETE ON {table_name} "
            "FOR EACH ROW EXECUTE FUNCTION research_reject_mutation()"
        )


def downgrade() -> None:
    """Remove only Research Engine tables, triggers, and enum types in dependency order."""
    op.drop_index(
        "ix_research_validation_experiment", table_name="research_experiment_validation_records"
    )
    op.drop_table("research_experiment_validation_records")
    op.drop_table("research_experiment_lineage")
    op.drop_index(
        "ix_research_hypothesis_evaluations_experiment",
        table_name="research_hypothesis_evaluations",
    )
    op.drop_index(
        "ix_research_hypothesis_evaluations_hypothesis_id",
        table_name="research_hypothesis_evaluations",
    )
    op.drop_table("research_hypothesis_evaluations")
    op.drop_table("research_hypotheses")
    op.drop_index(
        "ix_research_results_experiment_analysis",
        table_name="research_experiment_statistic_results",
    )
    op.drop_index(
        "ix_research_experiment_statistic_results_experiment_id",
        table_name="research_experiment_statistic_results",
    )
    op.drop_table("research_experiment_statistic_results")
    op.drop_index("ix_research_experiments_feature_set_created", table_name="research_experiments")
    op.drop_index("ix_research_experiments_dataset_created", table_name="research_experiments")
    op.drop_index("ix_research_experiments_dataset_snapshot_id", table_name="research_experiments")
    op.drop_index(
        "ix_research_experiments_feature_set_version_id", table_name="research_experiments"
    )
    op.drop_table("research_experiments")
    op.drop_index(
        "ix_research_dataset_rows_snapshot_team", table_name="research_dataset_snapshot_rows"
    )
    op.drop_index(
        "ix_research_dataset_rows_snapshot_fixture", table_name="research_dataset_snapshot_rows"
    )
    op.drop_index(
        "ix_research_dataset_rows_snapshot_feature", table_name="research_dataset_snapshot_rows"
    )
    op.drop_index(
        "ix_research_dataset_snapshot_rows_dataset_snapshot_id",
        table_name="research_dataset_snapshot_rows",
    )
    op.drop_table("research_dataset_snapshot_rows")
    op.drop_index(
        "ix_research_datasets_feature_set_created", table_name="research_dataset_snapshots"
    )
    op.drop_index(
        "ix_research_dataset_snapshots_feature_set_version_id",
        table_name="research_dataset_snapshots",
    )
    op.drop_table("research_dataset_snapshots")
    op.execute("DROP FUNCTION research_reject_mutation()")
    validation_status.drop(op.get_bind(), checkfirst=True)
    hypothesis_decision.drop(op.get_bind(), checkfirst=True)
    analysis_type.drop(op.get_bind(), checkfirst=True)
    experiment_status.drop(op.get_bind(), checkfirst=True)
