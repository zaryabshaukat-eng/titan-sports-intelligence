from dataclasses import asdict, dataclass


@dataclass
class InfrastructureMetrics:
    cache_hits: int = 0
    cache_misses: int = 0
    lock_conflicts: int = 0
    lock_renewals: int = 0
    retries: int = 0
    dead_letters: int = 0
    worker_jobs: int = 0
    scheduler_runs: int = 0
    rate_limited: int = 0

    def snapshot(self) -> dict[str, int]:
        return asdict(self)


metrics = InfrastructureMetrics()
