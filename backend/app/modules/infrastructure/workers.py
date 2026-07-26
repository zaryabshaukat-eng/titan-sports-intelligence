from collections.abc import Awaitable, Callable

from app.modules.infrastructure.monitoring import metrics
from app.modules.infrastructure.queue import InMemoryQueue


class Worker:
    def __init__(
        self,
        queue: InMemoryQueue,
        handlers: dict[str, Callable[[dict[str, object]], Awaitable[None]]],
        max_attempts: int = 3,
    ):
        self.queue, self.handlers, self.max_attempts = queue, handlers, max_attempts

    async def run_once(self) -> bool:
        job = await self.queue.claim()
        if not job:
            return False
        try:
            await self.handlers[job.name](job.payload)
            await self.queue.complete(job)
        except Exception:
            metrics.retries += 1
            await self.queue.fail(job, self.max_attempts, 2**job.attempts)
            metrics.dead_letters += int(job.status == "dead_letter")
        metrics.worker_jobs += 1
        return True
