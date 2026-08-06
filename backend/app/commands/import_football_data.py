"""Run one explicit football-data.org Premier League fixture/status import."""

from __future__ import annotations

import asyncio
import json

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.modules.ingestion.football_data_import import FootballDataFixtureImportService
from app.modules.ingestion.providers.football_data_client import FootballDataClient


async def main() -> None:
    """Discover and import exactly one provider-confirmed Premier League season once."""
    settings = get_settings()
    configure_logging(settings.log_level)
    if settings.football_data_api_token is None:
        raise RuntimeError("TITAN_FOOTBALL_DATA_API_TOKEN is required for this explicit import")

    client = FootballDataClient(settings.football_data_api_token.get_secret_value())
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            result = await FootballDataFixtureImportService(
                session=session,
                source=client,
            ).import_current_premier_league_season()
            await session.commit()
        print(
            json.dumps(
                {
                    "season_start_year": result.season_start_year,
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
