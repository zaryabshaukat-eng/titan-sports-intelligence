import asyncio

from app.modules.infrastructure.cache import Cache
from app.modules.infrastructure.locks import DistributedLock
from app.modules.infrastructure.queue import InMemoryQueue
from app.modules.infrastructure.workers import Worker


class Client:
    def __init__(self):
        self.values = {}

    async def get(self, k):
        return self.values.get(k)

    async def set(self, k, v, **kwargs):
        if kwargs.get("nx") and k in self.values:
            return False
        self.values[k] = v
        return True

    async def delete(self, k):
        return int(self.values.pop(k, None) is not None)

    async def expire(self, k, _):
        return k in self.values


class Redis:
    client = Client()


class Broken:
    class client:
        async def get(*_):
            raise RuntimeError()

        async def delete(*_):
            raise RuntimeError()


def test_cache_lock_and_concurrent_claims() -> None:
    asyncio.run(_exercise())


async def _exercise() -> None:
    cache = Cache(Redis())
    assert await cache.set("a", {"x": 1}, 1)
    assert await cache.get("a") == {"x": 1}
    assert await cache.delete("a")
    assert await Cache(Broken()).get("x") is None
    lock = DistributedLock(Redis(), "x", 1)
    assert await lock.acquire()
    assert not await DistributedLock(Redis(), "x", 1).acquire()
    assert await lock.renew()
    assert await lock.release()
    assert await DistributedLock(Redis(), "x", 1).acquire()
    queue = InMemoryQueue()
    await queue.enqueue("ok", {})
    calls = []

    async def ok(_):
        calls.append(1)

    await asyncio.gather(Worker(queue, {"ok": ok}).run_once(), Worker(queue, {"ok": ok}).run_once())
    assert calls == [1]
