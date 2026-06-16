"""Retry-with-backoff helper shared by the live feeds.

Cloud IPs (e.g. GitHub Actions) get intermittently rate-limited by public market
data hosts. A few spaced retries turn a transient 429/timeout into a success,
which keeps the hands-off daily refresh consistent instead of silently dropping a
symbol. Pair this with the generators' "skip writing on an empty pull" guard so a
hard block degrades gracefully rather than clobbering a good exhibit.
"""

from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def with_retries(call: Callable[[int], T], attempts: int = 4, backoff: float = 1.0) -> T:
    """Call ``call(attempt)`` up to ``attempts`` times with exponential backoff.

    ``call`` receives the 0-based attempt index (so a feed can rotate hosts across
    attempts). Waits ``backoff * 2**attempt`` plus a little jitter between tries;
    ``backoff=0`` disables sleeping (used in tests). Re-raises the last exception
    if every attempt fails.
    """
    last_exc: Exception | None = None
    for attempt in range(max(1, attempts)):
        try:
            return call(attempt)
        except Exception as exc:  # noqa: BLE001 - transient network errors are expected
            last_exc = exc
            if attempt < attempts - 1 and backoff > 0:
                time.sleep(backoff * (2 ** attempt) + random.uniform(0, backoff * 0.25))
    raise last_exc if last_exc else RuntimeError("all retry attempts failed")
