from tools.peak_p1_proxy.cache import TemperatureCache
from tools.peak_p1_proxy.model import TemperatureSample


def sample(timestamp: float = 10.0) -> TemperatureSample:
    return TemperatureSample(
        bt=159.8,
        et=171.5,
        exhaust=176.1,
        inlet=166.1,
        at=171.5,
        timestamp=timestamp,
    )


def test_cache_starts_empty_and_stale() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 100.0)

    assert cache.get() is None
    assert cache.is_stale()


def test_cache_returns_latest_sample_before_stale_timeout() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 12.0)
    cache.update(sample(timestamp=10.0))

    assert cache.get() == sample(timestamp=10.0)
    assert not cache.is_stale()


def test_cache_marks_sample_stale_after_timeout() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 16.0)
    cache.update(sample(timestamp=10.0))

    assert cache.is_stale()
