"""Create immutable Risk Engine records.

Revision ID: 20260726_0012
Revises: 20260726_0011
"""

# ruff: noqa: E501
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0012"
down_revision: str | None = "20260726_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
status = sa.Enum("completed", "validation_failed", name="risk_run_status")
validation_status = sa.Enum("passed", "failed", name="risk_validation_status")
UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()
TIME = sa.DateTime(timezone=True)


def base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", TIME, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    status.create(bind, checkfirst=True)
    validation_status.create(bind, checkfirst=True)
    op.create_table(
        "risk_runs",
        *base(),
        sa.Column("run_code", sa.String(96), nullable=False),
        sa.Column("consensus_run_id", UUID, nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("parameters", JSONB, nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.Column("status", status, nullable=False),
        sa.Column("input_checksum", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["consensus_run_id"], ["consensus_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["research_dataset_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_code", name="uq_risk_run_code"),
        sa.UniqueConstraint("idempotency_key", name="uq_risk_run_idempotency"),
    )
    for n, c in (
        ("ix_risk_runs_consensus_run_id", ["consensus_run_id"]),
        ("ix_risk_runs_dataset_snapshot_id", ["dataset_snapshot_id"]),
        ("ix_risk_runs_feature_set_version_id", ["feature_set_version_id"]),
        ("ix_risk_runs_consensus_created", ["consensus_run_id", "created_at"]),
    ):
        op.create_index(n, "risk_runs", c)
    op.create_table(
        "risk_outputs",
        *base(),
        sa.Column("risk_run_id", UUID, nullable=False),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("market_type", sa.String(96), nullable=False),
        sa.Column("outcome", sa.String(96), nullable=False),
        sa.Column("overall_risk_score", sa.Numeric(20, 8), nullable=False),
        sa.Column("uncertainty_score", sa.Numeric(20, 8), nullable=False),
        sa.Column("stability_score", sa.Numeric(20, 8), nullable=False),
        sa.Column("calibration_risk", sa.Numeric(20, 8), nullable=False),
        sa.Column("agreement_risk", sa.Numeric(20, 8), nullable=False),
        sa.Column("data_quality_risk", sa.Numeric(20, 8), nullable=False),
        sa.Column("completeness_score", sa.Numeric(20, 8), nullable=False),
        sa.Column("components", JSONB, nullable=False),
        sa.CheckConstraint(
            "overall_risk_score >= 0 AND overall_risk_score <= 1",
            name="ck_risk_output_overall_range",
        ),
        sa.ForeignKeyConstraint(["risk_run_id"], ["risk_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "risk_run_id",
            "fixture_id",
            "market_type",
            "outcome",
            name="uq_risk_output_run_fixture_market_outcome",
        ),
    )
    for n, c in (
        ("ix_risk_outputs_risk_run_id", ["risk_run_id"]),
        ("ix_risk_outputs_fixture_id", ["fixture_id"]),
        ("ix_risk_outputs_fixture_market", ["fixture_id", "market_type", "outcome"]),
    ):
        op.create_index(n, "risk_outputs", c)
    op.create_table(
        "risk_lineage",
        *base(),
        sa.Column("risk_run_id", UUID, nullable=False),
        sa.Column("consensus_run_id", UUID, nullable=False),
        sa.Column("probability_run_ids", JSONB, nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("parameters_checksum", sa.String(64), nullable=False),
        sa.Column("random_seed", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(["risk_run_id"], ["risk_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["consensus_run_id"], ["consensus_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["research_dataset_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("risk_run_id", name="uq_risk_lineage_run"),
    )
    op.create_table(
        "risk_validation_records",
        *base(),
        sa.Column("risk_run_id", UUID, nullable=False),
        sa.Column("rule_name", sa.String(96), nullable=False),
        sa.Column("status", validation_status, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(["risk_run_id"], ["risk_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("risk_run_id", "rule_name", name="uq_risk_validation_run_rule"),
    )
    op.create_index("ix_risk_validation_run", "risk_validation_records", ["risk_run_id"])
    op.execute(
        "CREATE FUNCTION risk_reject_mutation() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Risk historical records are immutable'; END; $$ LANGUAGE plpgsql;"
    )
    for t in ("risk_runs", "risk_outputs", "risk_lineage", "risk_validation_records"):
        op.execute(
            f"CREATE TRIGGER {t}_immutable BEFORE UPDATE OR DELETE ON {t} FOR EACH ROW EXECUTE FUNCTION risk_reject_mutation()"
        )


def downgrade() -> None:
    for t in ("risk_validation_records", "risk_lineage", "risk_outputs", "risk_runs"):
        op.drop_table(t)
    op.execute("DROP FUNCTION risk_reject_mutation()")
    validation_status.drop(op.get_bind(), checkfirst=True)
    status.drop(op.get_bind(), checkfirst=True)
