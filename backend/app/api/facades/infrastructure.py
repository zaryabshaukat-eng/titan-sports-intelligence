"""Thin API facade for existing infrastructure operational state."""

from app.modules.infrastructure.monitoring import metrics
from app.shared.redis import RedisClient


class InfrastructureApiFacade:
    def __init__(self, redis: RedisClient) -> None:
        self._redis = redis

    async def health(self) -> dict[str, str]:
        try:
            redis_ready = await self._redis.ping()
        except Exception:
            redis_ready = False
        return {
            "redis": "ready" if redis_ready else "not_ready",
            "queue": "local_outbox",
            "worker": "configured",
            "scheduler": "configuration_driven",
        }

    @staticmethod
    def status() -> dict[str, object]:
        return {"status": "ok", "metrics": metrics.snapshot()}
