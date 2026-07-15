"""Create fixture ingestion provenance, identity resolution, audit, and outbox records.

Revision ID: 20260715_0002
Revises: 20260715_0001
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260715_0002"
down_revision: str | None = "20260715_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
TIMESTAMP = sa.DateTime(timezone=True)
JSONB = postgresql.JSONB()

ingestion_run_status = postgresql.ENUM(
    "running",
    "completed",
    "completed_with_errors",
    "failed",
    name="ingestion_run_status",
    create_type=False,
)
raw_payload_status = postgresql.ENUM(
    "received",
    "valid",
    "invalid",
    "applied",
    name="ingestion_raw_payload_status",
    create_type=False,
)
provider_entity_type = postgresql.ENUM(
    "country",
    "league",
    "competition",
    "season",
    "team",
    "venue",
    "official",
    "timezone",
    name="ingestion_provider_entity_type",
    create_type=False,
)
ingestion_audit_outcome = postgresql.ENUM(
    "inserted",
    "updated",
    "unchanged",
    "validation_failed",
    name="ingestion_audit_outcome",
    create_type=False,
)
ingestion_event_type = postgresql.ENUM(
    "FixtureIngested",
    "FixtureUpdated",
    "FixtureValidationFailed",
    name="ingestion_event_type",
    create_type=False,
)


def audit_columns() -> list[sa.Column[object]]:
    """Return the standard UUID identity and audit timestamps for ingestion records."""
    return [
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "created_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
    ]


def upgrade() -> None:
    """Create durable data lineage, external identity links, audit history, and outbox tables."""
    bind = op.get_bind()
    ingestion_run_status.create(bind, checkfirst=True)
    raw_payload_status.create(bind, checkfirst=True)
    provider_entity_type.create(bind, checkfirst=True)
    ingestion_audit_outcome.create(bind, checkfirst=True)
    ingestion_event_type.create(bind, checkfirst=True)

    op.create_table(
        "ingestion_fixture_runs",
        *audit_columns(),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("status", ingestion_run_status, nullable=False),
        sa.Column(
            "started_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("completed_at", TIMESTAMP, nullable=True),
        sa.Column("received_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("inserted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unchanged_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failure_summary", sa.Text(), nullable=True),
        sa.CheckConstraint("received_count >= 0", name="ck_ingestion_fixture_runs_received_count"),
        sa.CheckConstraint("inserted_count >= 0", name="ck_ingestion_fixture_runs_inserted_count"),
        sa.CheckConstraint("updated_count >= 0", name="ck_ingestion_fixture_runs_updated_count"),
        sa.CheckConstraint(
            "unchanged_count >= 0", name="ck_ingestion_fixture_runs_unchanged_count"
        ),
        sa.CheckConstraint("failed_count >= 0", name="ck_ingestion_fixture_runs_failed_count"),
    )
    op.create_index(
        "ix_ingestion_fixture_runs_provider_name", "ingestion_fixture_runs", ["provider_name"]
    )
    op.create_index("ix_ingestion_fixture_runs_status", "ingestion_fixture_runs", ["status"])
    op.create_index(
        "ix_ingestion_fixture_runs_provider_started",
        "ingestion_fixture_runs",
        ["provider_name", "started_at"],
    )

    op.create_table(
        "ingestion_raw_fixture_payloads",
        *audit_columns(),
        sa.Column("ingestion_run_id", UUID, nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_fixture_id", sa.String(length=128), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("validation_status", raw_payload_status, nullable=False),
        sa.Column("validation_errors", JSONB, nullable=True),
        sa.Column(
            "ingested_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("processed_at", TIMESTAMP, nullable=True),
        sa.Column("canonical_fixture_id", UUID, nullable=True),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"], ["ingestion_fixture_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["canonical_fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "provider_name",
            "idempotency_key",
            name="uq_ingestion_raw_fixture_payloads_provider_key",
        ),
    )
    op.create_index(
        "ix_ingestion_raw_fixture_payloads_ingestion_run_id",
        "ingestion_raw_fixture_payloads",
        ["ingestion_run_id"],
    )
    op.create_index(
        "ix_ingestion_raw_fixture_payloads_provider_name",
        "ingestion_raw_fixture_payloads",
        ["provider_name"],
    )
    op.create_index(
        "ix_ingestion_raw_fixture_payloads_validation_status",
        "ingestion_raw_fixture_payloads",
        ["validation_status"],
    )
    op.create_index(
        "ix_ingestion_raw_fixture_payloads_canonical_fixture_id",
        "ingestion_raw_fixture_payloads",
        ["canonical_fixture_id"],
    )
    op.create_index(
        "ix_ingestion_raw_fixture_payloads_provider_fixture",
        "ingestion_raw_fixture_payloads",
        ["provider_name", "provider_fixture_id"],
    )
    op.create_index(
        "ix_ingestion_raw_fixture_payloads_checksum",
        "ingestion_raw_fixture_payloads",
        ["checksum"],
    )

    op.create_table(
        "ingestion_fixture_provider_identities",
        *audit_columns(),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_fixture_id", sa.String(length=128), nullable=False),
        sa.Column("fixture_id", UUID, nullable=False),
        sa.Column("latest_raw_payload_id", UUID, nullable=True),
        sa.Column("last_checksum", sa.String(length=64), nullable=False),
        sa.Column(
            "first_seen_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "last_seen_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["latest_raw_payload_id"], ["ingestion_raw_fixture_payloads.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "provider_name",
            "provider_fixture_id",
            name="uq_ingestion_fixture_provider_identities_provider_fixture",
        ),
    )
    op.create_index(
        "ix_ingestion_fixture_provider_identities_fixture",
        "ingestion_fixture_provider_identities",
        ["fixture_id"],
    )

    op.create_table(
        "ingestion_provider_entity_identities",
        *audit_columns(),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("entity_type", provider_entity_type, nullable=False),
        sa.Column("provider_entity_id", sa.String(length=128), nullable=False),
        sa.Column("canonical_entity_id", UUID, nullable=False),
        sa.Column(
            "first_seen_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "last_seen_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.UniqueConstraint(
            "provider_name",
            "entity_type",
            "provider_entity_id",
            name="uq_ingestion_provider_entity_identities_provider_entity",
        ),
    )
    op.create_index(
        "ix_ingestion_provider_entity_identities_canonical",
        "ingestion_provider_entity_identities",
        ["entity_type", "canonical_entity_id"],
    )

    op.create_table(
        "ingestion_fixture_audit",
        *audit_columns(),
        sa.Column("ingestion_run_id", UUID, nullable=False),
        sa.Column("raw_payload_id", UUID, nullable=False),
        sa.Column("fixture_id", UUID, nullable=True),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_fixture_id", sa.String(length=128), nullable=True),
        sa.Column("outcome", ingestion_audit_outcome, nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("changes", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "occurred_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"], ["ingestion_fixture_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["raw_payload_id"], ["ingestion_raw_fixture_payloads.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_ingestion_fixture_audit_ingestion_run_id",
        "ingestion_fixture_audit",
        ["ingestion_run_id"],
    )
    op.create_index(
        "ix_ingestion_fixture_audit_raw_payload_id", "ingestion_fixture_audit", ["raw_payload_id"]
    )
    op.create_index(
        "ix_ingestion_fixture_audit_fixture_id", "ingestion_fixture_audit", ["fixture_id"]
    )
    op.create_index(
        "ix_ingestion_fixture_audit_provider_name", "ingestion_fixture_audit", ["provider_name"]
    )
    op.create_index("ix_ingestion_fixture_audit_outcome", "ingestion_fixture_audit", ["outcome"])
    op.create_index(
        "ix_ingestion_fixture_audit_provider_occurred",
        "ingestion_fixture_audit",
        ["provider_name", "occurred_at"],
    )
    op.create_index(
        "ix_ingestion_fixture_audit_fixture_occurred",
        "ingestion_fixture_audit",
        ["fixture_id", "occurred_at"],
    )

    op.create_table(
        "ingestion_outbox_events",
        *audit_columns(),
        sa.Column("ingestion_run_id", UUID, nullable=False),
        sa.Column("raw_payload_id", UUID, nullable=False),
        sa.Column("fixture_id", UUID, nullable=True),
        sa.Column("event_type", ingestion_event_type, nullable=False),
        sa.Column("event_key", sa.String(length=128), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column(
            "occurred_at", TIMESTAMP, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("published_at", TIMESTAMP, nullable=True),
        sa.Column("delivery_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"], ["ingestion_fixture_runs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["raw_payload_id"], ["ingestion_raw_fixture_payloads.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["fixture_id"], ["sports_fixtures.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("event_key", name="uq_ingestion_outbox_events_event_key"),
    )
    op.create_index(
        "ix_ingestion_outbox_events_ingestion_run_id",
        "ingestion_outbox_events",
        ["ingestion_run_id"],
    )
    op.create_index(
        "ix_ingestion_outbox_events_raw_payload_id", "ingestion_outbox_events", ["raw_payload_id"]
    )
    op.create_index(
        "ix_ingestion_outbox_events_fixture_id", "ingestion_outbox_events", ["fixture_id"]
    )
    op.create_index(
        "ix_ingestion_outbox_events_event_type", "ingestion_outbox_events", ["event_type"]
    )
    op.create_index(
        "ix_ingestion_outbox_events_unpublished",
        "ingestion_outbox_events",
        ["published_at", "occurred_at"],
    )


def downgrade() -> None:
    """Remove ingestion tables before their PostgreSQL enum types."""
    op.drop_table("ingestion_outbox_events")
    op.drop_table("ingestion_fixture_audit")
    op.drop_table("ingestion_provider_entity_identities")
    op.drop_table("ingestion_fixture_provider_identities")
    op.drop_table("ingestion_raw_fixture_payloads")
    op.drop_table("ingestion_fixture_runs")

    bind = op.get_bind()
    ingestion_event_type.drop(bind, checkfirst=True)
    ingestion_audit_outcome.drop(bind, checkfirst=True)
    provider_entity_type.drop(bind, checkfirst=True)
    raw_payload_status.drop(bind, checkfirst=True)
    ingestion_run_status.drop(bind, checkfirst=True)
