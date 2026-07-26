from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4


@dataclass(slots=True)
class Job:
    id: str
    name: str
    payload: dict[str, object]
    available_at: datetime
    attempts: int = 0
    status: str = "queued"


class InMemoryQueue:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.keys: set[str] = set()

    async def enqueue(
        self,
        name: str,
        payload: dict[str, object],
        delay_seconds: float = 0,
        key: str | None = None,
    ) -> Job:
        if key and key in self.keys:
            return next(x for x in self.jobs.values() if x.payload.get("_key") == key)
        job = Job(
            str(uuid4()),
            name,
            {**payload, **({"_key": key} if key else {})},
            datetime.now(UTC) + timedelta(seconds=delay_seconds),
        )
        self.jobs[job.id] = job
        if key:
            self.keys.add(key)
        return job

    async def claim(self) -> Job | None:
        now = datetime.now(UTC)
        for job in self.jobs.values():
            if job.status == "queued" and job.available_at <= now:
                job.status = "running"
                return job
        return None

    async def complete(self, job: Job) -> None:
        job.status = "completed"

    async def fail(self, job: Job, max_attempts: int, delay: float) -> None:
        job.attempts += 1
        job.status = "dead_letter" if job.attempts >= max_attempts else "queued"
        job.available_at = datetime.now(UTC) + timedelta(seconds=delay)

    async def depth(self) -> int:
        return sum(x.status == "queued" for x in self.jobs.values())
