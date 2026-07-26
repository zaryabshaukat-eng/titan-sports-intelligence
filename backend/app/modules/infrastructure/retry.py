from collections.abc import Callable


async def retry(operation: Callable[[], object], attempts: int = 3):
    last = None
    for _ in range(attempts):
        try:
            return await operation()
        except Exception as exc:
            last = exc
    raise last
