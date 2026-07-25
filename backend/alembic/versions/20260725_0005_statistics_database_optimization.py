"""Correct Statistics indexes and ingestion-run constraints.

Revision ID: 20260725_0005
Revises: 20260725_0004
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260725_0005"
down_revision: str | None = "20260725_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add only indexes and checks needed by established Statistics access paths."""
    # `statistics_categories.code` is already backed by its unique constraint.
    op.drop_index("ix_statistics_categories_code", table_name="statistics_categories")
    op.create_check_constraint(
        "ck_statistics_runs_received_count",
        "statistics_ingestion_runs",
        "received_count >= 0",
    )
    op.create_check_constraint(
        "ck_statistics_runs_created_count",
        "statistics_ingestion_runs",
        "snapshots_created_count >= 0",
    )
    op.create_check_constraint(
        "ck_statistics_runs_failed_count",
        "statistics_ingestion_runs",
        "failed_count >= 0",
    )
    for name, table, columns in (
        (
            "ix_statistics_runs_provider_started",
            "statistics_ingestion_runs",
            ["provider_id", "started_at"],
        ),
        ("ix_statistics_raw_ingestion_run", "statistics_raw_payloads", ["ingestion_run_id"]),
        ("ix_statistics_raw_fixture", "statistics_raw_payloads", ["canonical_fixture_id"]),
        (
            "ix_statistics_snapshots_series_latest",
            "statistics_snapshots",
            ["series_id", "observed_at", "created_at"],
        ),
        ("ix_statistics_snapshots_ingestion_run", "statistics_snapshots", ["ingestion_run_id"]),
        ("ix_statistics_snapshots_raw_payload", "statistics_snapshots", ["raw_payload_id"]),
        ("ix_statistics_audits_ingestion_run", "statistics_audits", ["ingestion_run_id"]),
        ("ix_statistics_audits_raw_payload", "statistics_audits", ["raw_payload_id"]),
        (
            "ix_statistics_audits_provider_created",
            "statistics_audits",
            ["provider_id", "created_at"],
        ),
        ("ix_statistics_outbox_ingestion_run", "statistics_outbox_events", ["ingestion_run_id"]),
        ("ix_statistics_outbox_raw_payload", "statistics_outbox_events", ["raw_payload_id"]),
        (
            "ix_statistics_outbox_unpublished",
            "statistics_outbox_events",
            ["published_at", "created_at"],
        ),
    ):
        op.create_index(name, table, columns)


def downgrade() -> None:
    """Remove the corrective schema objects in reverse dependency order."""
    for name, table in (
        ("ix_statistics_outbox_unpublished", "statistics_outbox_events"),
        ("ix_statistics_outbox_raw_payload", "statistics_outbox_events"),
        ("ix_statistics_outbox_ingestion_run", "statistics_outbox_events"),
        ("ix_statistics_audits_provider_created", "statistics_audits"),
        ("ix_statistics_audits_raw_payload", "statistics_audits"),
        ("ix_statistics_audits_ingestion_run", "statistics_audits"),
        ("ix_statistics_snapshots_raw_payload", "statistics_snapshots"),
        ("ix_statistics_snapshots_ingestion_run", "statistics_snapshots"),
        ("ix_statistics_snapshots_series_latest", "statistics_snapshots"),
        ("ix_statistics_raw_fixture", "statistics_raw_payloads"),
        ("ix_statistics_raw_ingestion_run", "statistics_raw_payloads"),
        ("ix_statistics_runs_provider_started", "statistics_ingestion_runs"),
    ):
        op.drop_index(name, table_name=table)
    op.drop_constraint(
        "ck_statistics_runs_failed_count", "statistics_ingestion_runs", type_="check"
    )
    op.drop_constraint(
        "ck_statistics_runs_created_count", "statistics_ingestion_runs", type_="check"
    )
    op.drop_constraint(
        "ck_statistics_runs_received_count", "statistics_ingestion_runs", type_="check"
    )
    op.create_index("ix_statistics_categories_code", "statistics_categories", ["code"])
