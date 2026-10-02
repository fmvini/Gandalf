from concurrent.futures import ThreadPoolExecutor

import pytest

from app.core.exceptions import AppError
from app.core.rate_limit import RateLimiter


def test_expired_keys_are_reclaimed_without_revisiting_each_key(monkeypatch):
    monkeypatch.setattr("app.core.rate_limit.monotonic", lambda: 0)
    limiter = RateLimiter(2)
    for index in range(100):
        limiter.check(str(index))
    monkeypatch.setattr("app.core.rate_limit.monotonic", lambda: 60)
    limiter.check("new")
    assert list(limiter._events) == ["new"]


def test_capacity_does_not_evict_live_blocks_and_recovers_at_expiry(monkeypatch):
    monkeypatch.setattr("app.core.rate_limit.monotonic", lambda: 0)
    limiter = RateLimiter(1, max_keys=2)
    limiter.check("first")
    limiter.check("second")
    for key in ["new", "first", "second"]:
        with pytest.raises(AppError) as error:
            limiter.check(key)
        assert error.value.status_code == 429
        assert error.value.retry_after == 60
    assert len(limiter._events) == 2
    monkeypatch.setattr("app.core.rate_limit.monotonic", lambda: 60)
    limiter.check("new")
    assert list(limiter._events) == ["new"]


def test_last_accepted_event_controls_retirement_not_blocked_requests(monkeypatch):
    clock = [0]
    monkeypatch.setattr("app.core.rate_limit.monotonic", lambda: clock[0])
    limiter = RateLimiter(2, max_keys=2)
    limiter.check("first")
    clock[0] = 1
    limiter.check("second")
    clock[0] = 2
    limiter.check("first")
    clock[0] = 61
    limiter.check("new")
    assert set(limiter._events) == {"first", "new"}
    limiter.check("first")  # first event expired, one slot available
    with pytest.raises(AppError) as error:
        limiter.check("first")
    assert error.value.retry_after == 1


def test_concurrent_requests_cannot_exceed_limit_or_capacity(monkeypatch):
    monkeypatch.setattr("app.core.rate_limit.monotonic", lambda: 0)
    limiter = RateLimiter(3, max_keys=2)

    def attempt(key):
        try:
            limiter.check(key)
            return True
        except AppError:
            return False

    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(attempt, ["same"] * 16))
        unique = list(workers.map(attempt, [str(i) for i in range(16)]))
    assert sum(results) == 3
    assert sum(unique) == 1
    assert len(limiter._events) == 2
