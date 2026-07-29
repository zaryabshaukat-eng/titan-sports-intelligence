"""Create immutable Explainability Engine records.

Revision ID: 20260726_0013
Revises: 20260726_0012
"""

# ruff: noqa: E501
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0013"
down_revision: str | None = "20260726_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
run_status = postgresql.ENUM(
    "completed", "validation_failed", name="explainability_run_status", create_type=False
)
validation_status = postgresql.ENUM(
    "passed", "failed", name="explainability_validation_status", create_type=False
)
UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()
TIME = sa.DateTime(timezone=True)


def base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", TIME, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    b = op.get_bind()
    run_status.create(b, checkfirst=True)
    validation_status.create(b, checkfirst=True)
    op.create_table(
        "explainability_runs",
        *base(),
        sa.Column("run_code", sa.String(96), nullable=False),
        sa.Column("probability_run_id", UUID, nullable=False),
        sa.Column("consensus_run_id", UUID, nullable=False),
        sa.Column("risk_run_id", UUID, nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("parameters", JSONB, nullable=False),
        sa.Column("status", run_status, nullable=False),
        sa.Column("input_checksum", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["probability_run_id"], ["probability_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["consensus_run_id"], ["consensus_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["risk_run_id"], ["risk_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["dataset_snapshot_id"], ["research_dataset_snapshots.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["feature_set_version_id"],
            ["feature_store_feature_set_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_code", name="uq_explainability_run_code"),
        sa.UniqueConstraint("idempotency_key", name="uq_explainability_run_idempotency"),
    )
    for n, c in (
        ("ix_explainability_runs_probability_run_id", ["probability_run_id"]),
        ("ix_explainability_runs_consensus_run_id", ["consensus_run_id"]),
        ("ix_explainability_runs_risk_run_id", ["risk_run_id"]),
        ("ix_explainability_runs_risk_created", ["risk_run_id", "created_at"]),
    ):
        op.create_index(n, "explainability_runs", c)
    op.create_table(
        "explanations",
        *base(),
        sa.Column("explainability_run_id", UUID, nullable=False),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("market_type", sa.String(96), nullable=False),
        sa.Column("outcome", sa.String(96), nullable=False),
        sa.Column("explanation_summary", sa.Text, nullable=False),
        sa.Column("confidence", sa.Numeric(20, 8), nullable=False),
        sa.Column("evidence_completeness", sa.Numeric(20, 8), nullable=False),
        sa.Column("traceability_score", sa.Numeric(20, 8), nullable=False),
        sa.Column("coverage_score", sa.Numeric(20, 8), nullable=False),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_explanation_confidence_range"
        ),
        sa.ForeignKeyConstraint(
            ["explainability_run_id"], ["explainability_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "explainability_run_id",
            "fixture_id",
            "market_type",
            "outcome",
            name="uq_explanation_run_fixture_market_outcome",
        ),
    )
    for n, c in (
        ("ix_explanations_explainability_run_id", ["explainability_run_id"]),
        ("ix_explanations_fixture_id", ["fixture_id"]),
        ("ix_explanations_fixture_market", ["fixture_id", "market_type", "outcome"]),
    ):
        op.create_index(n, "explanations", c)
    op.create_table(
        "explanation_feature_contributions",
        *base(),
        sa.Column("explanation_id", UUID, nullable=False),
        sa.Column("feature_id", sa.String(128), nullable=False),
        sa.Column("feature_value", sa.Numeric(20, 8)),
        sa.Column("contribution", sa.Numeric(20, 8), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("source_feature_value_id", UUID, nullable=False),
        sa.ForeignKeyConstraint(["explanation_id"], ["explanations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["source_feature_value_id"], ["feature_store_feature_values.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "explanation_id", "feature_id", name="uq_explanation_contribution_feature"
        ),
    )
    op.create_index(
        "ix_explanation_feature_contributions_explanation_id",
        "explanation_feature_contributions",
        ["explanation_id"],
    )
    for table in ("explanation_evidence_references", "explanation_reasoning_steps"):
        extra = [
            sa.Column(
                "sequence" if table.endswith("references") else "position",
                sa.Integer,
                nullable=False,
            ),
            sa.Column(
                "source_type" if table.endswith("references") else "stage",
                sa.String(64),
                nullable=False,
            ),
            sa.Column(
                "source_id" if table.endswith("references") else "description",
                sa.Text if not table.endswith("references") else sa.String(128),
                nullable=False,
            ),
            sa.Column(
                "description" if table.endswith("references") else "source_type",
                sa.Text if table.endswith("references") else sa.String(64),
                nullable=False,
            ),
        ]
        if not table.endswith("references"):
            extra.append(sa.Column("source_id", sa.String(128), nullable=False))
        op.create_table(
            table,
            *base(),
            sa.Column("explanation_id", UUID, nullable=False),
            *extra,
            sa.ForeignKeyConstraint(["explanation_id"], ["explanations.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(f"ix_{table}_explanation_id", table, ["explanation_id"])
    op.create_table(
        "explainability_lineage",
        *base(),
        sa.Column("explainability_run_id", UUID, nullable=False),
        sa.Column("probability_run_id", UUID, nullable=False),
        sa.Column("consensus_run_id", UUID, nullable=False),
        sa.Column("risk_run_id", UUID, nullable=False),
        sa.Column("dataset_snapshot_id", UUID, nullable=False),
        sa.Column("feature_set_version_id", UUID, nullable=False),
        sa.Column("research_experiment_id", UUID, nullable=False),
        sa.Column("parameters_checksum", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("explainability_run_id", name="uq_explainability_lineage_run"),
    )
    op.create_table(
        "explainability_validation_records",
        *base(),
        sa.Column("explainability_run_id", UUID, nullable=False),
        sa.Column("rule_name", sa.String(96), nullable=False),
        sa.Column("status", validation_status, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(
            ["explainability_run_id"], ["explainability_runs.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "explainability_run_id", "rule_name", name="uq_explainability_validation_run_rule"
        ),
    )
    op.create_index(
        "ix_explainability_validation_run",
        "explainability_validation_records",
        ["explainability_run_id"],
    )
    op.execute(
        "CREATE FUNCTION explainability_reject_mutation() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Explainability historical records are immutable'; END; $$ LANGUAGE plpgsql;"
    )
    for t in (
        "explainability_runs",
        "explanations",
        "explanation_feature_contributions",
        "explanation_evidence_references",
        "explanation_reasoning_steps",
        "explainability_lineage",
        "explainability_validation_records",
    ):
        op.execute(
            f"CREATE TRIGGER {t}_immutable BEFORE UPDATE OR DELETE ON {t} FOR EACH ROW EXECUTE FUNCTION explainability_reject_mutation()"
        )


def downgrade() -> None:
    for t in (
        "explainability_validation_records",
        "explainability_lineage",
        "explanation_reasoning_steps",
        "explanation_evidence_references",
        "explanation_feature_contributions",
        "explanations",
        "explainability_runs",
    ):
        op.drop_table(t)
    op.execute("DROP FUNCTION explainability_reject_mutation()")
    validation_status.drop(op.get_bind(), checkfirst=True)
    run_status.drop(op.get_bind(), checkfirst=True)
