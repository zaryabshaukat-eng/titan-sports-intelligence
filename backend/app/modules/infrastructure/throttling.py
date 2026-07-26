from time import monotonic

from app.modules.infrastructure.monitoring import metrics


class LocalRateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60):
        self.limit, self.window, self.values = limit, window_seconds, {}

    def allow(self, key: str) -> bool:
        now = monotonic()
        items = [x for x in self.values.get(key, []) if x > now - self.window]
        self.values[key] = items
        if len(items) >= self.limit:
            metrics.rate_limited += 1
            return False
        items.append(now)
        return True
