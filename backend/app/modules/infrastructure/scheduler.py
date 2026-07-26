from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.modules.infrastructure.monitoring import metrics


@dataclass
class Schedule:
    name: str
    interval_seconds: int
    task: Callable[[], Awaitable[None]]
    next_at: datetime


class Scheduler:
    def __init__(self):
        self.items: list[Schedule] = []

    def register(self, name: str, interval_seconds: int, task: Callable[[], Awaitable[None]]):
        self.items.append(Schedule(name, interval_seconds, task, datetime.now(UTC)))

    async def tick(self):
        now = datetime.now(UTC)
        for item in self.items:
            if item.next_at <= now:
                await item.task()
                metrics.scheduler_runs += 1
                item.next_at = now + timedelta(seconds=item.interval_seconds)
