from collections import OrderedDict, deque
from math import ceil
from threading import Lock
from time import monotonic

from app.core.exceptions import AppError


class RateLimiter:
    def __init__(
        self, limit: int, window_seconds: int = 60, *, max_keys: int = 10_000
    ) -> None:
        if min(limit, window_seconds, max_keys) < 1:
            raise ValueError("Limiter bounds must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        # Order by last accepted event. Refused attempts never extend a bucket.
        self._events: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = Lock()

    def check(self, key: str) -> None:
        with self._lock:
            now = monotonic()
            while self._events:
                _, oldest = next(iter(self._events.items()))
                if oldest[-1] > now - self.window_seconds:
                    break
                self._events.popitem(last=False)

            events = self._events.get(key)
            if events is None:
                if len(self._events) >= self.max_keys:
                    oldest = next(iter(self._events.values()))
                    self._reject(self.window_seconds - (now - oldest[-1]))
                events = deque()
                self._events[key] = events
            while events and events[0] <= now - self.window_seconds:
                events.popleft()
            if len(events) >= self.limit:
                self._reject(self.window_seconds - (now - events[0]))
            events.append(now)
            self._events.move_to_end(key)

    @staticmethod
    def _reject(wait_seconds: float) -> None:
        raise AppError(
            429,
            "RATE_LIMITED",
            "Muitas tentativas. Aguarde um instante e tente novamente.",
            max(1, ceil(wait_seconds)),
        )
