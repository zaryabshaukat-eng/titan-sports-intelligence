"""Align index ordering and metadata with TITAN's production read paths.

Revision ID: 20260725_0007
Revises: 20260725_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260725_0007"
down_revision: str | None = "20260725_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Optimize newest-observation window queries without altering stored data."""
    op.drop_index("ix_statistics_snapshots_series_latest", table_name="statistics_snapshots")
    op.create_index(
        "ix_statistics_snapshots_series_latest",
        "statistics_snapshots",
        ["series_id", sa.text("observed_at DESC"), sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_market_data_odds_snapshots_latest_series",
        "market_data_odds_snapshots",
        [
            "provider_name",
            "bookmaker_id",
            "selection_id",
            sa.text("observed_at DESC"),
            sa.text("created_at DESC"),
        ],
    )


def downgrade() -> None:
    """Restore the predecessor's Statistics index and remove the new Odds index."""
    op.drop_index(
        "ix_market_data_odds_snapshots_latest_series",
        table_name="market_data_odds_snapshots",
    )
    op.drop_index("ix_statistics_snapshots_series_latest", table_name="statistics_snapshots")
    op.create_index(
        "ix_statistics_snapshots_series_latest",
        "statistics_snapshots",
        ["series_id", "observed_at", "created_at"],
    )
