from __future__ import annotations

import threading
import time
from collections.abc import Callable

from .model import TemperatureSample


class TemperatureCache:
    def __init__(self, stale_after: float, clock: Callable[[], float] | None = None) -> None:
        self._stale_after = stale_after
        self._clock = clock or time.monotonic
        self._lock = threading.RLock()
        self._sample: TemperatureSample | None = None

    def update(self, sample: TemperatureSample) -> None:
        with self._lock:
            self._sample = sample

    def get(self) -> TemperatureSample | None:
        with self._lock:
            return self._sample

    def sample_age(self) -> float | None:
        with self._lock:
            if self._sample is None:
                return None
            return self._clock() - self._sample.timestamp

    def is_stale(self) -> bool:
        with self._lock:
            if self._sample is None:
                return True
            return self._clock() - self._sample.timestamp > self._stale_after
