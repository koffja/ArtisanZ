from __future__ import annotations

import atexit
from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextlib import suppress
from dataclasses import dataclass
from functools import wraps
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Final
from typing import ParamSpec, TypeVar


_ENV_FLAG: Final[str] = 'ARTISANZ_GUI_PERF'
_EXPORT_FILE_ENV_FLAG: Final[str] = 'ARTISANZ_GUI_PERF_FILE'
_DEFAULT_EXPORT_FILENAME: Final[str] = 'artisanz-gui-perf.jsonl'
_P = ParamSpec('_P')
_R = TypeVar('_R')


def _env_enabled() -> bool:
    return os.environ.get(_ENV_FLAG, '').strip().lower() in {'1', 'true', 'yes', 'on'}


@dataclass
class _Metric:
    count: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0

    def add_duration(self, duration_ms: float) -> None:
        self.count += 1
        self.total_ms += duration_ms
        self.max_ms = max(self.max_ms, duration_ms)

    def add_count(self, amount: int) -> None:
        self.count += amount

    def as_dict(self) -> dict[str, float | int]:
        avg_ms = self.total_ms / self.count if self.count else 0.0
        return {
            'count': self.count,
            'total_ms': self.total_ms,
            'avg_ms': avg_ms,
            'max_ms': self.max_ms,
        }


class GuiPerfRecorder:
    def __init__(self, enabled: bool | None = None) -> None:
        self.enabled = _env_enabled() if enabled is None else enabled
        self._metrics: defaultdict[str, _Metric] = defaultdict(_Metric)

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        if not self.enabled:
            yield
            return
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._metrics[name].add_duration(duration_ms)

    def count(self, name: str, amount: int = 1) -> None:
        if self.enabled:
            self._metrics[name].add_count(amount)

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        return {name: metric.as_dict() for name, metric in sorted(self._metrics.items())}

    def summary_lines(self) -> list[str]:
        lines: list[str] = []
        for name, metric in self.snapshot().items():
            lines.append(
                f"{name}: count={metric['count']} "
                f"total_ms={metric['total_ms']:.3f} "
                f"avg_ms={metric['avg_ms']:.3f} "
                f"max_ms={metric['max_ms']:.3f}"
            )
        return lines

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('w', encoding='utf-8') as outfile:
            for name, metric in self.snapshot().items():
                outfile.write(json.dumps({'name': name, **metric}, sort_keys=True))
                outfile.write('\n')


_RECORDER = GuiPerfRecorder()


def get_gui_perf_recorder() -> GuiPerfRecorder:
    return _RECORDER


def gui_perf_enabled() -> bool:
    return _env_enabled()


def default_gui_perf_export_path() -> Path:
    return Path(tempfile.gettempdir()) / _DEFAULT_EXPORT_FILENAME


def gui_perf_export_path() -> Path | None:
    raw_path = os.environ.get(_EXPORT_FILE_ENV_FLAG, '').strip()
    if raw_path:
        return Path(raw_path)
    if gui_perf_enabled():
        return default_gui_perf_export_path()
    return None


def export_gui_perf_metrics() -> Path | None:
    if not _RECORDER.enabled:
        return None
    perf_path = gui_perf_export_path()
    if perf_path is None:
        return None
    _RECORDER.write_jsonl(perf_path)
    return perf_path


def _export_gui_perf_metrics_at_exit() -> None:
    with suppress(Exception):
        export_gui_perf_metrics()


@contextmanager
def gui_perf_span(name: str) -> Iterator[None]:
    with _RECORDER.span(name):
        yield


def gui_perf_count(name: str, amount: int = 1) -> None:
    _RECORDER.count(name, amount)


def gui_perf_tracked(name: str) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    def decorate(func: Callable[_P, _R]) -> Callable[_P, _R]:
        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            with gui_perf_span(name):
                return func(*args, **kwargs)

        return wrapper

    return decorate


atexit.register(_export_gui_perf_metrics_at_exit)
