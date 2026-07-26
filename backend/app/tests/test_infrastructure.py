import asyncio

from app.modules.infrastructure.queue import InMemoryQueue
from app.modules.infrastructure.scheduler import Scheduler
from app.modules.infrastructure.throttling import LocalRateLimiter
from app.modules.infrastructure.workers import Worker


def test_queue_worker_retry_dead_letter_and_scheduler() -> None:
    asyncio.run(_queue_worker_retry_dead_letter_and_scheduler())


async def _queue_worker_retry_dead_letter_and_scheduler() -> None:
    queue = InMemoryQueue()
    job = await queue.enqueue("x", {})
    calls = 0

    async def fail(_: dict[str, object]):
        nonlocal calls
        calls += 1
        raise RuntimeError()

    worker = Worker(queue, {"x": fail}, max_attempts=1)
    assert await worker.run_once() and job.status == "dead_letter" and calls == 1
    scheduled = 0

    async def task():
        nonlocal scheduled
        scheduled += 1

    scheduler = Scheduler()
    scheduler.register("x", 1, task)
    await scheduler.tick()
    assert scheduled == 1


def test_rate_limit_burst_protection() -> None:
    limiter = LocalRateLimiter(1)
    assert limiter.allow("user")
    assert not limiter.allow("user")
