"""Asynchronous PostgreSQL engine and request-scoped session dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseSessionManager:
    """Own the process-level engine and create isolated unit-of-work sessions."""

    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
        )

    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield one transactional session and roll back uncommitted failures."""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def ping(self) -> bool:
        """Verify that a short database query can be executed."""
        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True

    async def outbox_backlog(self) -> dict[str, int]:
        """Return pending delivery counts without reading event payloads."""
        statement = text(
            "SELECT 'fixture_ingestion' AS context, count(*) AS total "
            "FROM ingestion_outbox_events WHERE published_at IS NULL AND dead_lettered_at IS NULL "
            "UNION ALL "
            "SELECT 'market_data' AS context, count(*) AS total "
            "FROM market_data_outbox_events "
            "WHERE published_at IS NULL AND dead_lettered_at IS NULL "
            "UNION ALL "
            "SELECT 'statistics' AS context, count(*) AS total "
            "FROM statistics_outbox_events WHERE published_at IS NULL AND dead_lettered_at IS NULL"
        )
        async with self._engine.connect() as connection:
            rows = (await connection.execute(statement)).all()
        return {str(row.context): int(row.total) for row in rows}

    async def dispose(self) -> None:
        """Release the application connection pool during shutdown."""
        await self._engine.dispose()


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped SQLAlchemy session."""
    manager: DatabaseSessionManager = request.app.state.database
    async for session in manager.session():
        yield session
