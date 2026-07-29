"""Create immutable Consensus Engine records.

Revision ID: 20260726_0011
Revises: 20260726_0010
"""
# ruff: noqa: E501

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0011"
down_revision: str | None = "20260726_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

strategy = postgresql.ENUM(
    "weighted_average",
    "median",
    "trimmed_mean",
    "majority_voting",
    "bayesian_pooling",
    name="consensus_strategy",
    create_type=False,
)
run_status = postgresql.ENUM(
    "completed", "validation_failed", name="consensus_run_status", create_type=False
)
validation_status = postgresql.ENUM(
    "passed", "failed", name="consensus_validation_status", create_type=False
)
UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()
TIME = sa.DateTime(timezone=True)


def _base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", TIME, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for item in (strategy, run_status, validation_status):
        item.create(bind, checkfirst=True)
    op.create_table(
        "consensus_runs",
        *_base(),
        sa.Column("run_code", sa.String(96), nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("strategy", strategy, nullable=False),
        sa.Column("parameters", JSONB, nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.Column("status", run_status, nullable=False),
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
        sa.UniqueConstraint("run_code", name="uq_consensus_run_code"),
        sa.UniqueConstraint("idempotency_key", name="uq_consensus_run_idempotency"),
    )
    for name, cols in (
        ("ix_consensus_runs_feature_set_version_id", ["feature_set_version_id"]),
        ("ix_consensus_runs_dataset_snapshot_id", ["dataset_snapshot_id"]),
        ("ix_consensus_runs_dataset_created", ["dataset_snapshot_id", "created_at"]),
        ("ix_consensus_runs_strategy_created", ["strategy", "created_at"]),
    ):
        op.create_index(name, "consensus_runs", cols)
    op.create_table(
        "consensus_run_inputs",
        *_base(),
        sa.Column("consensus_run_id", UUID, nullable=False),
        sa.Column("probability_run_id", UUID, nullable=False),
        sa.Column("model_identifier", sa.String(96), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("calibration_version", sa.String(161)),
        sa.Column("research_experiment_id", UUID, nullable=False),
        sa.ForeignKeyConstraint(["consensus_run_id"], ["consensus_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["probability_run_id"], ["probability_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["research_experiment_id"], ["research_experiments.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consensus_run_id", "probability_run_id", name="uq_consensus_input_run_probability"
        ),
    )
    for name, cols in (
        ("ix_consensus_run_inputs_consensus_run_id", ["consensus_run_id"]),
        ("ix_consensus_inputs_probability_run", ["probability_run_id"]),
    ):
        op.create_index(name, "consensus_run_inputs", cols)
    op.create_table(
        "consensus_outputs",
        *_base(),
        sa.Column("consensus_run_id", UUID, nullable=False),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("market_type", sa.String(96), nullable=False),
        sa.Column("outcome", sa.String(96), nullable=False),
        sa.Column("consensus_probability", sa.Numeric(20, 8), nullable=False),
        sa.Column("confidence_score", sa.Numeric(20, 8), nullable=False),
        sa.Column("disagreement_score", sa.Numeric(20, 8), nullable=False),
        sa.Column("agreement_level", sa.String(16), nullable=False),
        sa.Column("confidence_metrics", JSONB, nullable=False),
        sa.Column("disagreement_metrics", JSONB, nullable=False),
        sa.Column("contributor_count", sa.Integer, nullable=False),
        sa.Column("expected_count", sa.Integer, nullable=False),
        sa.CheckConstraint(
            "consensus_probability >= 0 AND consensus_probability <= 1",
            name="ck_consensus_output_probability_range",
        ),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_consensus_output_confidence_range",
        ),
        sa.CheckConstraint(
            "disagreement_score >= 0 AND disagreement_score <= 1",
            name="ck_consensus_output_disagreement_range",
        ),
        sa.CheckConstraint(
            "contributor_count >= 1 AND expected_count >= contributor_count",
            name="ck_consensus_output_input_counts",
        ),
        sa.ForeignKeyConstraint(["consensus_run_id"], ["consensus_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consensus_run_id",
            "fixture_id",
            "market_type",
            "outcome",
            name="uq_consensus_output_run_fixture_market_outcome",
        ),
    )
    for name, cols in (
        ("ix_consensus_outputs_consensus_run_id", ["consensus_run_id"]),
        ("ix_consensus_outputs_fixture_id", ["fixture_id"]),
        ("ix_consensus_outputs_fixture_market", ["fixture_id", "market_type", "outcome"]),
    ):
        op.create_index(name, "consensus_outputs", cols)
    op.create_table(
        "consensus_lineage",
        *_base(),
        sa.Column("consensus_run_id", UUID, nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("probability_run_ids", JSONB, nullable=False),
        sa.Column("model_versions", JSONB, nullable=False),
        sa.Column("calibration_versions", JSONB, nullable=False),
        sa.Column("research_experiment_ids", JSONB, nullable=False),
        sa.Column("parameters_checksum", sa.String(64), nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(["consensus_run_id"], ["consensus_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["research_dataset_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("consensus_run_id", name="uq_consensus_lineage_run"),
    )
    op.create_table(
        "consensus_validation_records",
        *_base(),
        sa.Column("consensus_run_id", UUID, nullable=False),
        sa.Column("rule_name", sa.String(96), nullable=False),
        sa.Column("status", validation_status, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(["consensus_run_id"], ["consensus_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consensus_run_id", "rule_name", name="uq_consensus_validation_run_rule"
        ),
    )
    op.create_index(
        "ix_consensus_validation_run", "consensus_validation_records", ["consensus_run_id"]
    )
    op.execute(
        "CREATE FUNCTION consensus_reject_mutation() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Consensus historical records are immutable'; END; $$ LANGUAGE plpgsql;"
    )
    for table in (
        "consensus_runs",
        "consensus_run_inputs",
        "consensus_outputs",
        "consensus_lineage",
        "consensus_validation_records",
    ):
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION consensus_reject_mutation()"
        )


def downgrade() -> None:
    for table in (
        "consensus_validation_records",
        "consensus_lineage",
        "consensus_outputs",
        "consensus_run_inputs",
        "consensus_runs",
    ):
        op.drop_table(table)
    op.execute("DROP FUNCTION consensus_reject_mutation()")
    for item in (validation_status, run_status, strategy):
        item.drop(op.get_bind(), checkfirst=True)
