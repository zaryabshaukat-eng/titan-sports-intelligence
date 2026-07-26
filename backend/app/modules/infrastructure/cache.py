from __future__ import annotations

import json
from typing import TypeVar

from app.modules.infrastructure.monitoring import metrics

T = TypeVar("T")


class Cache:
    def __init__(self, redis: object, namespace: str = "titan"):
        self.redis = redis
        self.namespace = namespace

    def key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> object | None:
        try:
            value = await self.redis.client.get(self.key(key))
            metrics.cache_hits += int(bool(value))
            metrics.cache_misses += int(not bool(value))
            return json.loads(value) if value else None
        except Exception:
            metrics.cache_misses += 1
            return None

    async def set(self, key: str, value: object, ttl: int) -> bool:
        try:
            return bool(
                await self.redis.client.set(
                    self.key(key), json.dumps(value, sort_keys=True, default=str), ex=ttl
                )
            )
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        try:
            return bool(await self.redis.client.delete(self.key(key)))
        except Exception:
            return False
