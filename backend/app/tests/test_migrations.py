"""Migration-chain validation without requiring a live PostgreSQL instance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex

from app.modules.consensus import models as consensus_models  # noqa: F401
from app.modules.evaluation import models as evaluation_models  # noqa: F401
from app.modules.explainability import models as explainability_models  # noqa: F401
from app.modules.feature_store import models as feature_store_models  # noqa: F401
from app.modules.ingestion import models as ingestion_models  # noqa: F401
from app.modules.market_data import models as market_data_models  # noqa: F401
from app.modules.probability import models as probability_models  # noqa: F401
from app.modules.research import models as research_models  # noqa: F401
from app.modules.risk import models as risk_models  # noqa: F401
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


def test_research_migration_enforces_append_only_artifacts() -> None:
    """Research snapshots and evidence must remain immutable after insertion."""
    sql = _offline_upgrade_sql()

    assert "CREATE FUNCTION research_reject_mutation()" in sql
    assert "CREATE TRIGGER research_dataset_snapshots_immutable" in sql
    assert "CREATE TRIGGER research_experiments_immutable" in sql
    assert "CREATE TRIGGER research_hypothesis_evaluations_immutable" in sql


def test_probability_migration_enforces_append_only_artifacts() -> None:
    """Probability configurations, estimates, and scores must remain immutable evidence."""
    sql = _offline_upgrade_sql()

    assert "CREATE FUNCTION probability_reject_mutation()" in sql
    assert "CREATE TRIGGER probability_runs_immutable" in sql
    assert "CREATE TRIGGER probability_outputs_immutable" in sql
    assert "CREATE TRIGGER probability_evaluations_immutable" in sql


def test_consensus_migration_enforces_append_only_artifacts() -> None:
    """Consensus probabilities and their evidence must remain immutable historical records."""
    sql = _offline_upgrade_sql()

    assert "CREATE FUNCTION consensus_reject_mutation()" in sql
    assert "CREATE TRIGGER consensus_runs_immutable" in sql
    assert "CREATE TRIGGER consensus_outputs_immutable" in sql


def test_risk_migration_enforces_append_only_artifacts() -> None:
    sql = _offline_upgrade_sql()
    assert "CREATE FUNCTION risk_reject_mutation()" in sql
    assert "CREATE TRIGGER risk_runs_immutable" in sql
    assert "CREATE TRIGGER risk_outputs_immutable" in sql


def test_explainability_migration_enforces_append_only_artifacts() -> None:
    sql = _offline_upgrade_sql()
    assert "CREATE FUNCTION explainability_reject_mutation()" in sql
    assert "CREATE TRIGGER explainability_runs_immutable" in sql
    assert "CREATE TRIGGER explanations_immutable" in sql


def test_backtest_migration_enforces_append_only_artifacts() -> None:
    sql = _offline_upgrade_sql()
    assert "CREATE FUNCTION backtest_reject_mutation()" in sql
    assert "CREATE TRIGGER backtest_runs_immutable" in sql
    assert "CREATE TRIGGER backtest_results_immutable" in sql
