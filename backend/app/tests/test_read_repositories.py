"""Database-independent query-shape tests for read repositories."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast

from app.modules.market_data.read_repositories import OddsSnapshotRepository
from app.modules.market_data.schemas import OddsSnapshotFilters, PaginationParams


class _ReadSession:
    """Small async-session substitute which captures the paginated statement."""

    def __init__(self) -> None:
        self.statement: object | None = None

    async def scalar(self, _: object) -> int:
        return 0

    async def execute(self, statement: object) -> SimpleNamespace:
        self.statement = statement
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))


def test_latest_odds_repository_uses_one_windowed_row_per_price_series() -> None:
    async def run() -> None:
        session = _ReadSession()
        repository = OddsSnapshotRepository(session)  # type: ignore[arg-type]

        page = await repository.list_latest(
            OddsSnapshotFilters(provider_name="Odds_Feed_V1"),
            PaginationParams(limit=25),
        )

        assert session.statement is not None
        compiled = str(cast(Any, session.statement).compile(compile_kwargs={"literal_binds": True}))
        assert page.items == []
        assert page.total == 0
        assert "row_number() OVER" in compiled
        assert "PARTITION BY market_data_odds_snapshots.provider_name" in compiled
        assert "market_data_odds_snapshots.provider_name = 'odds_feed_v1'" in compiled
        assert "LIMIT 25" in compiled

    asyncio.run(run())
