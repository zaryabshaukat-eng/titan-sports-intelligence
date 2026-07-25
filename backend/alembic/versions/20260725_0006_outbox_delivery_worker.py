"""Add local delivery leasing and retry metadata to existing outbox tables.

Revision ID: 20260725_0006
Revises: 20260725_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260725_0006"
down_revision: str | None = "20260725_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OUTBOX_TABLES = (
    "ingestion_outbox_events",
    "market_data_outbox_events",
    "statistics_outbox_events",
)


def upgrade() -> None:
    """Add bounded retry and lease fields without changing event payload schemas."""
    for table in OUTBOX_TABLES:
        with op.batch_alter_table(table) as batch:
            if table == "statistics_outbox_events":
                batch.add_column(
                    sa.Column("delivery_attempts", sa.Integer(), nullable=False, server_default="0")
                )
            batch.add_column(
                sa.Column(
                    "next_attempt_at",
                    sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                )
            )
            batch.add_column(sa.Column("lease_owner", sa.String(length=96), nullable=True))
            batch.add_column(
                sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True)
            )
            batch.add_column(sa.Column("last_error", sa.Text(), nullable=True))
            batch.add_column(
                sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True)
            )
        op.create_index(
            f"ix_{table}_delivery_ready",
            table,
            ["next_attempt_at", "lease_expires_at"],
            postgresql_where=sa.text("published_at IS NULL AND dead_lettered_at IS NULL"),
        )


def downgrade() -> None:
    """Remove worker delivery metadata while retaining original immutable events."""
    for table in reversed(OUTBOX_TABLES):
        op.drop_index(f"ix_{table}_delivery_ready", table_name=table)
        with op.batch_alter_table(table) as batch:
            batch.drop_column("dead_lettered_at")
            batch.drop_column("last_error")
            batch.drop_column("lease_expires_at")
            batch.drop_column("lease_owner")
            batch.drop_column("next_attempt_at")
            if table == "statistics_outbox_events":
                batch.drop_column("delivery_attempts")
