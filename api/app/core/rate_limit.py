from collections import defaultdict, deque
from math import ceil
from threading import Lock
from time import monotonic

from app.core.exceptions import AppError


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = monotonic()
        with self._lock:
            events = self._events[key]
            while events and events[0] <= now - self.window_seconds:
                events.popleft()
            if len(events) >= self.limit:
                retry_after = max(1, ceil(self.window_seconds - (now - events[0])))
                raise AppError(
                    429,
                    "RATE_LIMITED",
                    "Muitas tentativas. Aguarde um instante e tente novamente.",
                    retry_after,
                )
            events.append(now)
