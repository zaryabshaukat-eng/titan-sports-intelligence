"""Create append-only continuous evaluation monitoring artifacts."""
# ruff: noqa: E501

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0015"
down_revision: str | None = "20260726_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None
UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()
TIME = sa.DateTime(timezone=True)
status = postgresql.ENUM(
    "completed", "validation_failed", name="monitoring_status", create_type=False
)
validation = postgresql.ENUM(
    "passed", "failed", name="monitoring_validation_status", create_type=False
)
severity = postgresql.ENUM(
    "info", "warning", "critical", name="monitoring_alert_severity", create_type=False
)


def base():
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", TIME, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def artifact(name: str, *columns: sa.Column) -> None:
    op.create_table(
        name,
        *base(),
        sa.Column(
            "evaluation_run_id",
            UUID,
            sa.ForeignKey("monitoring_evaluation_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *columns,
    )
    op.create_index(f"ix_{name}_evaluation_run_id", name, ["evaluation_run_id"])


def upgrade() -> None:
    bind = op.get_bind()
    status.create(bind, checkfirst=True)
    validation.create(bind, checkfirst=True)
    severity.create(bind, checkfirst=True)
    op.create_table(
        "monitoring_evaluation_configurations",
        *base(),
        sa.Column("configuration_code", sa.String(96), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("thresholds", JSONB, nullable=False),
        sa.Column("analyzer_versions", JSONB, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False, unique=True),
        sa.UniqueConstraint(
            "configuration_code", "version", name="uq_monitoring_configuration_version"
        ),
    )
    op.create_table(
        "monitoring_evaluation_runs",
        *base(),
        sa.Column("run_code", sa.String(96), nullable=False),
        sa.Column(
            "configuration_id",
            UUID,
            sa.ForeignKey("monitoring_evaluation_configurations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "feature_set_version_id",
            UUID,
            sa.ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "dataset_snapshot_id",
            UUID,
            sa.ForeignKey("research_dataset_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "probability_run_id",
            UUID,
            sa.ForeignKey("probability_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "consensus_run_id",
            UUID,
            sa.ForeignKey("consensus_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "risk_run_id", UUID, sa.ForeignKey("risk_runs.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "explainability_run_id",
            UUID,
            sa.ForeignKey("explainability_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "backtest_run_id",
            UUID,
            sa.ForeignKey("backtest_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("dataset_checksum", sa.String(64), nullable=False),
        sa.Column("generator_versions", JSONB, nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.Column("status", status, nullable=False),
        sa.Column("input_checksum", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.UniqueConstraint("run_code", name="uq_monitoring_run_code"),
        sa.UniqueConstraint("idempotency_key", name="uq_monitoring_run_key"),
    )
    for column in (
        "configuration_id",
        "feature_set_version_id",
        "dataset_snapshot_id",
        "probability_run_id",
        "consensus_run_id",
        "risk_run_id",
        "explainability_run_id",
        "backtest_run_id",
    ):
        op.create_index(
            f"ix_monitoring_evaluation_runs_{column}", "monitoring_evaluation_runs", [column]
        )
    op.create_index(
        "ix_monitoring_runs_backtest_created",
        "monitoring_evaluation_runs",
        ["backtest_run_id", "created_at"],
    )
    artifact(
        "monitoring_evaluation_results",
        sa.Column("analyzer_id", sa.String(96), nullable=False),
        sa.Column("value", sa.Numeric(20, 8), nullable=False),
        sa.Column("details", JSONB, nullable=False),
    )
    artifact(
        "monitoring_drift_measurements",
        sa.Column("metric_name", sa.String(96), nullable=False),
        sa.Column("value", sa.Numeric(20, 8), nullable=False),
        sa.Column(
            "baseline_run_id",
            UUID,
            sa.ForeignKey("monitoring_evaluation_runs.id", ondelete="RESTRICT"),
        ),
    )
    artifact(
        "monitoring_quality_metrics",
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("value", sa.Numeric(20, 8), nullable=False),
        sa.Column("dimensions", JSONB, nullable=False),
    )
    artifact(
        "monitoring_provider_health",
        sa.Column("provider_name", sa.String(128), nullable=False),
        sa.Column("freshness_seconds", sa.Integer, nullable=False),
        sa.Column("completeness_score", sa.Numeric(20, 8), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
    )
    artifact(
        "monitoring_model_health",
        sa.Column("model_identifier", sa.String(96), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("metrics", JSONB, nullable=False),
    )
    artifact(
        "monitoring_feature_health",
        sa.Column(
            "feature_set_version_id",
            UUID,
            sa.ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("completeness_score", sa.Numeric(20, 8), nullable=False),
        sa.Column("metrics", JSONB, nullable=False),
    )
    artifact(
        "monitoring_calibration_health",
        sa.Column("calibration_version", sa.String(161)),
        sa.Column("metrics", JSONB, nullable=False),
    )
    artifact(
        "monitoring_alerts",
        sa.Column("severity", severity, nullable=False),
        sa.Column("alert_type", sa.String(96), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("evidence", JSONB, nullable=False),
    )
    artifact(
        "monitoring_validation_records",
        sa.Column("rule_name", sa.String(96), nullable=False),
        sa.Column("status", validation, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
    )
    artifact(
        "monitoring_lineage_records",
        sa.Column("artifact_ids", JSONB, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
    )
    op.execute(
        "CREATE FUNCTION monitoring_reject_mutation() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Monitoring artifacts are immutable'; END; $$ LANGUAGE plpgsql;"
    )
    for table in (
        "monitoring_evaluation_configurations",
        "monitoring_evaluation_runs",
        "monitoring_evaluation_results",
        "monitoring_drift_measurements",
        "monitoring_quality_metrics",
        "monitoring_provider_health",
        "monitoring_model_health",
        "monitoring_feature_health",
        "monitoring_calibration_health",
        "monitoring_alerts",
        "monitoring_validation_records",
        "monitoring_lineage_records",
    ):
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION monitoring_reject_mutation()"
        )


def downgrade() -> None:
    for table in (
        "monitoring_lineage_records",
        "monitoring_validation_records",
        "monitoring_alerts",
        "monitoring_calibration_health",
        "monitoring_feature_health",
        "monitoring_model_health",
        "monitoring_provider_health",
        "monitoring_quality_metrics",
        "monitoring_drift_measurements",
        "monitoring_evaluation_results",
        "monitoring_evaluation_runs",
        "monitoring_evaluation_configurations",
    ):
        op.drop_table(table)
    op.execute("DROP FUNCTION monitoring_reject_mutation()")
    validation.drop(op.get_bind(), checkfirst=True)
    severity.drop(op.get_bind(), checkfirst=True)
    status.drop(op.get_bind(), checkfirst=True)
