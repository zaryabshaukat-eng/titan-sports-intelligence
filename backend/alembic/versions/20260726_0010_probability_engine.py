"""Create immutable Probability Engine runs, outputs, calibration, evaluation, and lineage.

Revision ID: 20260726_0010
Revises: 20260726_0009
"""
# ruff: noqa: E501

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0010"
down_revision: str | None = "20260726_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

calibration_method = sa.Enum(
    "platt", "isotonic", "temperature", name="probability_calibration_method"
)
run_status = sa.Enum("completed", "validation_failed", name="probability_run_status")
validation_status = sa.Enum("passed", "failed", name="probability_validation_status")
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
    """Create the standalone Probability bounded context without changing source contexts."""
    bind = op.get_bind()
    for item in (calibration_method, run_status, validation_status):
        item.create(bind, checkfirst=True)

    op.create_table(
        "probability_calibration_versions",
        *_base_columns(),
        sa.Column("calibration_code", sa.String(96), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("method", calibration_method, nullable=False),
        sa.Column("parameters", JSONB, nullable=False),
        sa.Column("compatible_model_identifiers", JSONB, nullable=False),
        sa.Column("owner", sa.String(128), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "calibration_code", "version", name="uq_probability_calibration_code_version"
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_probability_calibration_idempotency"),
    )
    op.create_index(
        "ix_probability_calibration_method_created",
        "probability_calibration_versions",
        ["method", "created_at"],
    )

    op.create_table(
        "probability_runs",
        *_base_columns(),
        sa.Column("run_code", sa.String(96), nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("research_experiment_id", UUID, nullable=False),
        sa.Column("model_identifier", sa.String(96), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("calibration_version_id", UUID, nullable=True),
        sa.Column("market_type", sa.String(96), nullable=False),
        sa.Column("outcome", sa.String(96), nullable=False),
        sa.Column("parameters", JSONB, nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.Column("prediction_timestamp", TIMESTAMP, nullable=False),
        sa.Column("status", run_status, nullable=False),
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
            ["calibration_version_id"],
            ["probability_calibration_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_code", name="uq_probability_run_code"),
        sa.UniqueConstraint("idempotency_key", name="uq_probability_run_idempotency"),
    )
    op.create_index(
        "ix_probability_runs_dataset_snapshot_id", "probability_runs", ["dataset_snapshot_id"]
    )
    op.create_index(
        "ix_probability_runs_feature_set_version_id",
        "probability_runs",
        ["feature_set_version_id"],
    )
    op.create_index(
        "ix_probability_runs_research_experiment_id",
        "probability_runs",
        ["research_experiment_id"],
    )
    op.create_index(
        "ix_probability_runs_dataset_created",
        "probability_runs",
        ["dataset_snapshot_id", "created_at"],
    )
    op.create_index(
        "ix_probability_runs_experiment_created",
        "probability_runs",
        ["research_experiment_id", "created_at"],
    )
    op.create_index(
        "ix_probability_runs_model_created",
        "probability_runs",
        ["model_identifier", "model_version", "created_at"],
    )

    op.create_table(
        "probability_outputs",
        *_base_columns(),
        sa.Column("probability_run_id", UUID, nullable=False),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("market_type", sa.String(96), nullable=False),
        sa.Column("outcome", sa.String(96), nullable=False),
        sa.Column("estimated_probability", sa.Numeric(20, 8), nullable=False),
        sa.Column("confidence_interval_low", sa.Numeric(20, 8), nullable=False),
        sa.Column("confidence_interval_high", sa.Numeric(20, 8), nullable=False),
        sa.Column("calibration_version", sa.String(161), nullable=True),
        sa.Column("prediction_timestamp", TIMESTAMP, nullable=False),
        sa.Column("support_count", sa.Integer, nullable=False),
        sa.CheckConstraint(
            "estimated_probability >= 0 AND estimated_probability <= 1",
            name="ck_probability_output_probability_range",
        ),
        sa.CheckConstraint(
            "confidence_interval_low >= 0 AND confidence_interval_high <= 1",
            name="ck_probability_output_confidence_range",
        ),
        sa.CheckConstraint(
            "confidence_interval_low <= estimated_probability "
            "AND estimated_probability <= confidence_interval_high",
            name="ck_probability_output_confidence_contains_estimate",
        ),
        sa.CheckConstraint("support_count >= 1", name="ck_probability_output_support_count"),
        sa.ForeignKeyConstraint(
            ["probability_run_id"], ["probability_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "probability_run_id",
            "fixture_id",
            "market_type",
            "outcome",
            name="uq_probability_output_run_fixture_market_outcome",
        ),
    )
    op.create_index(
        "ix_probability_outputs_probability_run_id", "probability_outputs", ["probability_run_id"]
    )
    op.create_index("ix_probability_outputs_fixture_id", "probability_outputs", ["fixture_id"])
    op.create_index(
        "ix_probability_outputs_fixture_market_prediction",
        "probability_outputs",
        ["fixture_id", "market_type", "prediction_timestamp"],
    )

    op.create_table(
        "probability_evaluations",
        *_base_columns(),
        sa.Column("probability_run_id", UUID, nullable=False),
        sa.Column("evaluation_code", sa.String(96), nullable=False),
        sa.Column("sample_count", sa.Integer, nullable=False),
        sa.Column("metrics", JSONB, nullable=False),
        sa.Column("reliability", JSONB, nullable=False),
        sa.Column("input_checksum", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.CheckConstraint("sample_count >= 1", name="ck_probability_evaluation_sample_count"),
        sa.ForeignKeyConstraint(
            ["probability_run_id"], ["probability_runs.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "probability_run_id", "evaluation_code", name="uq_probability_evaluation_run_code"
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_probability_evaluation_idempotency"),
    )
    op.create_index(
        "ix_probability_evaluations_probability_run_id",
        "probability_evaluations",
        ["probability_run_id"],
    )
    op.create_index(
        "ix_probability_evaluations_run_created",
        "probability_evaluations",
        ["probability_run_id", "created_at"],
    )

    op.create_table(
        "probability_lineage",
        *_base_columns(),
        sa.Column("probability_run_id", UUID, nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("research_experiment_id", UUID, nullable=False),
        sa.Column("model_identifier", sa.String(96), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("calibration_version", sa.String(161), nullable=True),
        sa.Column("parameters_checksum", sa.String(64), nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(
            ["probability_run_id"], ["probability_runs.id"], ondelete="RESTRICT"
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("probability_run_id", name="uq_probability_lineage_run"),
    )

    op.create_table(
        "probability_validation_records",
        *_base_columns(),
        sa.Column("probability_run_id", UUID, nullable=False),
        sa.Column("rule_name", sa.String(96), nullable=False),
        sa.Column("status", validation_status, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(
            ["probability_run_id"], ["probability_runs.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "probability_run_id", "rule_name", name="uq_probability_validation_run_rule"
        ),
    )
    op.create_index(
        "ix_probability_validation_run", "probability_validation_records", ["probability_run_id"]
    )

    op.execute(
        """
        CREATE FUNCTION probability_reject_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Probability historical records are immutable';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table_name in (
        "probability_calibration_versions",
        "probability_runs",
        "probability_outputs",
        "probability_evaluations",
        "probability_lineage",
        "probability_validation_records",
    ):
        op.execute(
            f"CREATE TRIGGER {table_name}_immutable "
            f"BEFORE UPDATE OR DELETE ON {table_name} "
            "FOR EACH ROW EXECUTE FUNCTION probability_reject_mutation()"
        )


def downgrade() -> None:
    """Remove only Probability Engine schema objects in dependency order."""
    op.drop_index("ix_probability_validation_run", table_name="probability_validation_records")
    op.drop_table("probability_validation_records")
    op.drop_table("probability_lineage")
    op.drop_index("ix_probability_evaluations_run_created", table_name="probability_evaluations")
    op.drop_index(
        "ix_probability_evaluations_probability_run_id", table_name="probability_evaluations"
    )
    op.drop_table("probability_evaluations")
    op.drop_index(
        "ix_probability_outputs_fixture_market_prediction", table_name="probability_outputs"
    )
    op.drop_index("ix_probability_outputs_fixture_id", table_name="probability_outputs")
    op.drop_index("ix_probability_outputs_probability_run_id", table_name="probability_outputs")
    op.drop_table("probability_outputs")
    op.drop_index("ix_probability_runs_model_created", table_name="probability_runs")
    op.drop_index("ix_probability_runs_experiment_created", table_name="probability_runs")
    op.drop_index("ix_probability_runs_dataset_created", table_name="probability_runs")
    op.drop_index("ix_probability_runs_research_experiment_id", table_name="probability_runs")
    op.drop_index("ix_probability_runs_feature_set_version_id", table_name="probability_runs")
    op.drop_index("ix_probability_runs_dataset_snapshot_id", table_name="probability_runs")
    op.drop_table("probability_runs")
    op.drop_index(
        "ix_probability_calibration_method_created", table_name="probability_calibration_versions"
    )
    op.drop_table("probability_calibration_versions")
    op.execute("DROP FUNCTION probability_reject_mutation()")
    validation_status.drop(op.get_bind(), checkfirst=True)
    run_status.drop(op.get_bind(), checkfirst=True)
    calibration_method.drop(op.get_bind(), checkfirst=True)
