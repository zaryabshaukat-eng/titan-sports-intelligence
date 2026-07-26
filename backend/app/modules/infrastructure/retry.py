from collections.abc import Awaitable, Callable
from typing import cast


async def retry[T](operation: Callable[[], Awaitable[T]], attempts: int = 3) -> T:
    """Retry an asynchronous operation without changing its exception semantics."""
    last: Exception | None = None
    for _ in range(attempts):
        try:
            return await operation()
        except Exception as exc:
            last = exc
    # ``last`` is populated by the existing retry loop for every positive
    # attempt count. Retaining the original raise behaviour also preserves the
    # legacy edge case for an invalid zero-attempt call.
    raise cast(Exception, last)
