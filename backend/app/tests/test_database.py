"""Database connectivity integration test."""

from __future__ import annotations

import asyncio
import os

import pytest

from app.shared.persistence.database import DatabaseSessionManager


def test_database_connection() -> None:
    """Execute a simple query when an explicit integration database is configured."""
    database_url = os.getenv("TITAN_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("TITAN_TEST_DATABASE_URL is not configured")

    async def verify_connection() -> None:
        manager = DatabaseSessionManager(database_url)
        try:
            assert await manager.ping() is True
        finally:
            await manager.dispose()

    asyncio.run(verify_connection())
