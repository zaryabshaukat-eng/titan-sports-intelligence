"""Optional live PostgreSQL validation for the latest reversible index migration."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.skipif(
    not os.getenv("TITAN_TEST_DATABASE_URL"), reason="TITAN_TEST_DATABASE_URL is not configured"
)
def test_latest_migration_round_trip_preserves_rows_and_recreates_indexes() -> None:
    """Downgrade and re-upgrade only the reversible latest-index migration on a test database."""

    async def run() -> None:
        engine = create_async_engine(os.environ["TITAN_TEST_DATABASE_URL"])
        marker = f"migration-check-{uuid4().hex}"
        marker_id = str(uuid4())
        try:
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        "INSERT INTO statistics_categories "
                        "(id, code, name, value_schema, is_active) "
                        "VALUES (CAST(:id AS uuid), :code, :name, '{}'::jsonb, true)"
                    ),
                    {"id": marker_id, "code": marker, "name": marker},
                )
            backend_root = Path(__file__).resolve().parents[2]
            environment = {
                **os.environ,
                "TITAN_DATABASE_URL": os.environ["TITAN_TEST_DATABASE_URL"],
            }
            for command in (
                [sys.executable, "-m", "alembic", "downgrade", "20260725_0006"],
                [sys.executable, "-m", "alembic", "upgrade", "head"],
            ):
                result = subprocess.run(
                    command,
                    cwd=backend_root,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert result.returncode == 0, result.stderr
            async with engine.connect() as connection:
                preserved = await connection.scalar(
                    text("SELECT count(*) FROM statistics_categories WHERE code = :code"),
                    {"code": marker},
                )
                index_exists = await connection.scalar(
                    text(
                        "SELECT to_regclass('public.ix_market_data_odds_snapshots_latest_series') "
                        "IS NOT NULL"
                    )
                )
                assert preserved == 1
                assert index_exists is True
        finally:
            async with engine.begin() as connection:
                await connection.execute(
                    text("DELETE FROM statistics_categories WHERE code = :code"), {"code": marker}
                )
            await engine.dispose()

    asyncio.run(run())
