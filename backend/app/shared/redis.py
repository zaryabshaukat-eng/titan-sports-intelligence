"""Redis client lifecycle management for future cache and job integrations."""

from __future__ import annotations

from redis.asyncio import Redis


class RedisClient:
    """Own a lazily connected Redis client for one application process."""

    def __init__(self, redis_url: str) -> None:
        self.client: Redis = Redis.from_url(redis_url, decode_responses=True)

    async def ping(self) -> bool:
        """Verify that Redis is reachable when a readiness check requires it."""
        return bool(await self.client.ping())

    async def close(self) -> None:
        """Close the client connection pool during application shutdown."""
        await self.client.aclose()
