"""Migration-chain validation without requiring a live PostgreSQL instance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex

from app.modules.feature_store import models as feature_store_models  # noqa: F401
from app.modules.ingestion import models as ingestion_models  # noqa: F401
from app.modules.market_data import models as market_data_models  # noqa: F401
from app.modules.sports import models as sports_models  # noqa: F401
from app.modules.statistics import models as statistics_models  # noqa: F401
from app.shared.persistence.base import Base


def _offline_upgrade_sql() -> str:
    """Compile the migration chain without a database, returning its PostgreSQL DDL."""
    backend_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=backend_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_alembic_offline_upgrade_and_downgrade_cover_full_chain() -> None:
    """Compile every migration in both directions so broken DDL is caught in CI."""
    backend_root = Path(__file__).resolve().parents[2]
    for command in (
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        [sys.executable, "-m", "alembic", "downgrade", "head:base", "--sql"],
    ):
        result = subprocess.run(
            command, cwd=backend_root, capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stderr


def test_declared_model_indexes_are_present_in_final_offline_migration_sql() -> None:
    """Prevent model indexes from drifting away from the final Alembic schema."""
    sql = _offline_upgrade_sql()
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            creation = f"CREATE INDEX {index.name} ON {table.name}"
            unique_creation = f"CREATE UNIQUE INDEX {index.name} ON {table.name}"
            assert creation in sql or unique_creation in sql, (
                f"Missing migration for {table.name}.{index.name}"
            )


def test_latest_snapshot_indexes_match_window_query_order_and_outbox_predicates() -> None:
    """Assert optimized model metadata has the exact PostgreSQL index shapes it requires."""
    indexes = {
        index.name: str(CreateIndex(index).compile(dialect=postgresql.dialect()))
        for table in Base.metadata.tables.values()
        for index in table.indexes
    }

    assert (
        "(series_id, observed_at DESC, created_at DESC)"
        in indexes["ix_statistics_snapshots_series_latest"]
    )
    assert (
        "(provider_name, bookmaker_id, selection_id, observed_at DESC, created_at DESC)"
        in indexes["ix_market_data_odds_snapshots_latest_series"]
    )
    for name in (
        "ix_ingestion_outbox_events_delivery_ready",
        "ix_market_data_outbox_events_delivery_ready",
        "ix_statistics_outbox_events_delivery_ready",
    ):
        assert "WHERE published_at IS NULL AND dead_lettered_at IS NULL" in indexes[name]
    assert (
        "(fixture_id, feature_definition_id, observed_at DESC)"
        in indexes["ix_feature_store_values_fixture_definition_observed"]
    )


def test_feature_store_migration_enforces_append_only_history() -> None:
    sql = _offline_upgrade_sql()

    assert "CREATE FUNCTION feature_store_reject_mutation()" in sql
    assert "CREATE TRIGGER feature_store_feature_values_immutable" in sql
    assert "CREATE TRIGGER feature_store_lineage_immutable" in sql
