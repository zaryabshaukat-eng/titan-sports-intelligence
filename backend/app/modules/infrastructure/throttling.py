from time import monotonic

from app.modules.infrastructure.monitoring import metrics


class LocalRateLimiter:
    """In-process sliding-window limiter with explicit internal state typing."""

    def __init__(self, limit: int, window_seconds: float = 60) -> None:
        self.limit = limit
        self.window = window_seconds
        self.values: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        now = monotonic()
        items = [x for x in self.values.get(key, []) if x > now - self.window]
        self.values[key] = items
        if len(items) >= self.limit:
            metrics.rate_limited += 1
            return False
        items.append(now)
        return True
