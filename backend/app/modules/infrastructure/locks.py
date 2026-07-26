from __future__ import annotations

from uuid import uuid4


class DistributedLock:
    def __init__(self, redis: object, name: str, lease_seconds: int):
        self.redis, self.name, self.token, self.lease = (
            redis,
            f"titan:lock:{name}",
            str(uuid4()),
            lease_seconds,
        )

    async def acquire(self) -> bool:
        try:
            return bool(await self.redis.client.set(self.name, self.token, nx=True, ex=self.lease))
        except Exception:
            return False

    async def renew(self) -> bool:
        try:
            return (
                bool(await self.redis.client.expire(self.name, self.lease))
                if await self.redis.client.get(self.name) == self.token
                else False
            )
        except Exception:
            return False

    async def release(self) -> bool:
        try:
            return (
                bool(await self.redis.client.delete(self.name))
                if await self.redis.client.get(self.name) == self.token
                else False
            )
        except Exception:
            return False
