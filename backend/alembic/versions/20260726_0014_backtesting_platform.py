"""Create immutable backtesting and simulation records.

Revision ID: 20260726_0014
Revises: 20260726_0013
"""

# ruff: noqa: E501
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0014"
down_revision: str | None = "20260726_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None
status = sa.Enum("completed", "validation_failed", name="backtest_run_status")
scenario = sa.Enum(
    "historical_replay",
    "rolling_window",
    "expanding_window",
    "walk_forward",
    "time_split",
    name="backtest_scenario",
)
validation = sa.Enum("passed", "failed", name="backtest_validation_status")
UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()
TIME = sa.DateTime(timezone=True)


def b():
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", TIME, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    status.create(bind, checkfirst=True)
    scenario.create(bind, checkfirst=True)
    validation.create(bind, checkfirst=True)
    op.create_table(
        "backtest_runs",
        *b(),
        sa.Column("run_code", sa.String(96), nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("research_experiment_id", UUID, nullable=False),
        sa.Column("probability_run_id", UUID, nullable=False),
        sa.Column("consensus_run_id", UUID, nullable=False),
        sa.Column("risk_run_id", UUID, nullable=False),
        sa.Column("explainability_run_id", UUID, nullable=False),
        sa.Column("scenario", scenario, nullable=False),
        sa.Column("parameters", JSONB, nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.Column("status", status, nullable=False),
        sa.Column("input_checksum", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["research_dataset_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["research_experiment_id"], ["research_experiments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["probability_run_id"], ["probability_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["consensus_run_id"], ["consensus_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["risk_run_id"], ["risk_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["explainability_run_id"], ["explainability_runs.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_code", name="uq_backtest_run_code"),
        sa.UniqueConstraint("idempotency_key", name="uq_backtest_run_idempotency"),
    )
    for n, c in (
        ("ix_backtest_runs_dataset_snapshot_id", ["dataset_snapshot_id"]),
        ("ix_backtest_runs_feature_set_version_id", ["feature_set_version_id"]),
        ("ix_backtest_runs_research_experiment_id", ["research_experiment_id"]),
        ("ix_backtest_runs_probability_run_id", ["probability_run_id"]),
        ("ix_backtest_runs_consensus_run_id", ["consensus_run_id"]),
        ("ix_backtest_runs_risk_run_id", ["risk_run_id"]),
        ("ix_backtest_runs_explainability_run_id", ["explainability_run_id"]),
        ("ix_backtest_runs_dataset_created", ["dataset_snapshot_id", "created_at"]),
    ):
        op.create_index(n, "backtest_runs", c)
    op.create_table(
        "backtest_results",
        *b(),
        sa.Column("backtest_run_id", UUID, nullable=False),
        sa.Column("probability_output_id", UUID, nullable=False),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("market_type", sa.String(96), nullable=False),
        sa.Column("outcome", sa.String(96), nullable=False),
        sa.Column("predicted_probability", sa.Numeric(20, 8), nullable=False),
        sa.Column("observed_outcome", sa.Boolean, nullable=False),
        sa.Column("prediction_timestamp", TIME, nullable=False),
        sa.Column("fixture_start_at", TIME, nullable=False),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["probability_output_id"], ["probability_outputs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "backtest_run_id", "probability_output_id", name="uq_backtest_result_run_output"
        ),
    )
    op.create_index("ix_backtest_results_backtest_run_id", "backtest_results", ["backtest_run_id"])
    op.create_index("ix_backtest_results_fixture", "backtest_results", ["fixture_id"])
    op.create_table(
        "backtest_metrics",
        *b(),
        sa.Column("backtest_run_id", UUID, nullable=False),
        sa.Column("sample_count", sa.Integer, nullable=False),
        sa.Column("metrics", JSONB, nullable=False),
        sa.Column("reliability", JSONB, nullable=False),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("backtest_run_id", name="uq_backtest_metric_run"),
    )
    op.create_table(
        "backtest_lineage",
        *b(),
        sa.Column("backtest_run_id", UUID, nullable=False),
        sa.Column("parameters_checksum", sa.String(64), nullable=False),
        sa.Column("artifact_ids", JSONB, nullable=False),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("backtest_run_id", name="uq_backtest_lineage_run"),
    )
    op.create_table(
        "backtest_validation_records",
        *b(),
        sa.Column("backtest_run_id", UUID, nullable=False),
        sa.Column("rule_name", sa.String(96), nullable=False),
        sa.Column("status", validation, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("backtest_run_id", "rule_name", name="uq_backtest_validation_run_rule"),
    )
    op.create_index(
        "ix_backtest_validation_run", "backtest_validation_records", ["backtest_run_id"]
    )
    op.execute(
        "CREATE FUNCTION backtest_reject_mutation() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Backtest historical records are immutable'; END; $$ LANGUAGE plpgsql;"
    )
    for t in (
        "backtest_runs",
        "backtest_results",
        "backtest_metrics",
        "backtest_lineage",
        "backtest_validation_records",
    ):
        op.execute(
            f"CREATE TRIGGER {t}_immutable BEFORE UPDATE OR DELETE ON {t} FOR EACH ROW EXECUTE FUNCTION backtest_reject_mutation()"
        )


def downgrade() -> None:
    for t in (
        "backtest_validation_records",
        "backtest_lineage",
        "backtest_metrics",
        "backtest_results",
        "backtest_runs",
    ):
        op.drop_table(t)
    op.execute("DROP FUNCTION backtest_reject_mutation()")
    validation.drop(op.get_bind(), checkfirst=True)
    scenario.drop(op.get_bind(), checkfirst=True)
    status.drop(op.get_bind(), checkfirst=True)
