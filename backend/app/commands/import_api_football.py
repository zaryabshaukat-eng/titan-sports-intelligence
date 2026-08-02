"""Run one explicit API-Football Premier League fixture import."""

from __future__ import annotations

import asyncio
import json

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.modules.ingestion.api_football_import import ApiFootballFixtureImportService
from app.modules.ingestion.providers.api_football_client import ApiFootballClient


async def main() -> None:
    """Discover the provider's current Premier League season and import its fixtures once."""
    settings = get_settings()
    configure_logging(settings.log_level)
    if settings.api_football_api_key is None:
        raise RuntimeError("TITAN_API_FOOTBALL_API_KEY is required for this explicit import")

    client = ApiFootballClient(settings.api_football_api_key.get_secret_value())
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            result = await ApiFootballFixtureImportService(
                session=session,
                source=client,
            ).import_current_premier_league_season()
            await session.commit()
        print(
            json.dumps(
                {
                    "season_year": result.season_year,
                    "fixture_count": result.fixture_count,
                    "inserted_count": result.ingestion.inserted_count,
                    "updated_count": result.ingestion.updated_count,
                    "unchanged_count": result.ingestion.unchanged_count,
                    "failed_count": result.ingestion.failed_count,
                }
            )
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
