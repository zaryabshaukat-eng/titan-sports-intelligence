"""Create immutable advisory continuous-improvement evidence."""

# ruff: noqa: E501
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260726_0016"
down_revision = "20260726_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None
U = postgresql.UUID(as_uuid=True)
J = postgresql.JSONB()
T = sa.DateTime(timezone=True)
S = sa.Enum("completed", "validation_failed", name="improvement_status")
R = sa.Enum(
    "feature_retirement",
    "feature_promotion",
    "feature_redesign",
    "model_retirement",
    "model_promotion",
    "calibration_replacement",
    "consensus_change",
    "risk_adjustment",
    "research_priority",
    name="improvement_recommendation_type",
)
D = sa.Enum("proposed", "human_approved", "human_rejected", name="improvement_decision_status")


def b():
    return [
        sa.Column("id", U, primary_key=True),
        sa.Column("created_at", T, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def a(n, *c):
    op.create_table(
        n,
        *b(),
        sa.Column(
            "improvement_run_id",
            U,
            sa.ForeignKey("improvement_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *c,
    )
    op.create_index(f"ix_{n}_improvement_run_id", n, ["improvement_run_id"])


def upgrade():
    bind = op.get_bind()
    S.create(bind, checkfirst=True)
    R.create(bind, checkfirst=True)
    D.create(bind, checkfirst=True)
    op.create_table(
        "improvement_configurations",
        *b(),
        sa.Column("code", sa.String(96)),
        sa.Column("version", sa.String(64)),
        sa.Column("analyzer_versions", J),
        sa.Column("thresholds", J),
        sa.Column("checksum", sa.String(64), unique=True),
        sa.UniqueConstraint("code", "version", name="uq_improvement_config"),
    )
    op.create_table(
        "improvement_runs",
        *b(),
        sa.Column("run_code", sa.String(96)),
        sa.Column(
            "configuration_id",
            U,
            sa.ForeignKey("improvement_configurations.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "evaluation_run_id",
            U,
            sa.ForeignKey("monitoring_evaluation_runs.id", ondelete="RESTRICT"),
        ),
        sa.Column("backtest_run_id", U, sa.ForeignKey("backtest_runs.id", ondelete="RESTRICT")),
        sa.Column("status", S),
        sa.Column("input_checksum", sa.String(64)),
        sa.Column("idempotency_key", sa.String(64)),
        sa.UniqueConstraint("run_code", name="uq_improvement_run"),
        sa.UniqueConstraint("idempotency_key", name="uq_improvement_key"),
    )
    op.create_index(
        "ix_improvement_runs_evaluation_run_id", "improvement_runs", ["evaluation_run_id"]
    )
    op.create_index("ix_improvement_runs_backtest_run_id", "improvement_runs", ["backtest_run_id"])
    a(
        "improvement_recommendations",
        sa.Column("recommendation_type", R),
        sa.Column("title", sa.String(160)),
        sa.Column("rationale", sa.Text),
        sa.Column("confidence", sa.Float),
        sa.Column("analyzer_id", sa.String(96)),
        sa.Column("payload", J),
    )
    a(
        "improvement_recommendation_evidence",
        sa.Column(
            "recommendation_id",
            U,
            sa.ForeignKey("improvement_recommendations.id", ondelete="RESTRICT"),
        ),
        sa.Column("evidence", J),
    )
    a(
        "improvement_candidate_models",
        sa.Column("model_identifier", sa.String(96)),
        sa.Column("model_version", sa.String(64)),
        sa.Column("evidence", J),
    )
    a(
        "improvement_candidate_features",
        sa.Column(
            "feature_set_version_id",
            U,
            sa.ForeignKey("feature_store_feature_set_versions.id", ondelete="RESTRICT"),
        ),
        sa.Column("action", sa.String(64)),
        sa.Column("evidence", J),
    )
    a(
        "improvement_promotion_decisions",
        sa.Column(
            "recommendation_id",
            U,
            sa.ForeignKey("improvement_recommendations.id", ondelete="RESTRICT"),
        ),
        sa.Column("status", D),
        sa.Column("note", sa.Text),
    )
    a(
        "improvement_validation_records",
        sa.Column("rule_name", sa.String(96)),
        sa.Column("status", sa.String(16)),
        sa.Column("message", sa.Text),
    )
    a(
        "improvement_lineage_records",
        sa.Column("artifact_ids", J),
        sa.Column("checksum", sa.String(64)),
    )
    op.execute(
        "CREATE FUNCTION improvement_reject_mutation() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Improvement artifacts are immutable'; END; $$ LANGUAGE plpgsql;"
    )
    for n in (
        "improvement_configurations",
        "improvement_runs",
        "improvement_recommendations",
        "improvement_recommendation_evidence",
        "improvement_candidate_models",
        "improvement_candidate_features",
        "improvement_promotion_decisions",
        "improvement_validation_records",
        "improvement_lineage_records",
    ):
        op.execute(
            f"CREATE TRIGGER {n}_immutable BEFORE UPDATE OR DELETE ON {n} FOR EACH ROW EXECUTE FUNCTION improvement_reject_mutation()"
        )


def downgrade():
    for n in (
        "improvement_lineage_records",
        "improvement_validation_records",
        "improvement_promotion_decisions",
        "improvement_candidate_features",
        "improvement_candidate_models",
        "improvement_recommendation_evidence",
        "improvement_recommendations",
        "improvement_runs",
        "improvement_configurations",
    ):
        op.drop_table(n)
    op.execute("DROP FUNCTION improvement_reject_mutation()")
    D.drop(op.get_bind(), checkfirst=True)
    R.drop(op.get_bind(), checkfirst=True)
    S.drop(op.get_bind(), checkfirst=True)
