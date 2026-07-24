"""Queued worker boundary for deterministic live sample frame decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from artisanlib.sample_processing import (
    LiveInputFilterRequest,
    LiveInputFilterResult,
    LiveThermalInputRequest,
    build_live_input_filter_result,
    build_live_processed_sample_frame,
    build_live_thermal_input_result,
)


@dataclass(frozen=True, slots=True)
class ProcessedFrameRequest:
    """Immutable input snapshot for one live processed-frame decision."""

    timestamp: float
    sample_count: int
    latest_et: float
    latest_bt: float
    smoothed_et: float | None
    smoothed_bt: float | None
    pid_process_value: float | None
    raw_delta_et: float | None
    raw_delta_bt: float | None
    ror_limit_enabled: bool
    max_ror_limit: float
    ror_limit: float
    ror_limit_min: float
    charge_index: int
    dry_index: int
    drop_index: int
    delta_et_filter: float
    delta_bt_filter: float
    delta_et_samples: int
    delta_bt_samples: int
    fix_max_time: bool
    lock_time_x: bool
    sample_times: tuple[float, ...]
    start_of_x: float
    end_of_x: float
    tp_alarm_timeindex: int | None
    tp_max_roast_time: float
    auto_charge_idx: int
    auto_charge_flag: bool
    auto_charge_enabled: bool
    auto_drop_idx: int
    auto_drop_flag: bool
    auto_drop_enabled: bool
    mode: str

    def __post_init__(self) -> None:
        # Type annotations do not protect callers that pass a live list at runtime.
        object.__setattr__(self, 'sample_times', tuple(self.sample_times))

    def as_kwargs(self) -> dict[str, Any]:
        """Return helper-compatible keyword arguments without exposing live lists."""
        return asdict(self)


class ProcessedFrameRequestChannel(QObject):
    """GUI-owned signal channel used to queue requests into the worker thread."""

    request = pyqtSignal(int, object)
    input_filter_request = pyqtSignal(int, object)
    thermal_request = pyqtSignal(int, object)


class ProcessedFrameWorker(QObject):
    """Compute pure frame decisions on a dedicated Qt event-loop thread."""

    result_ready = pyqtSignal(int, object)
    input_filter_result_ready = pyqtSignal(int, object)
    thermal_result_ready = pyqtSignal(int, object)
    error = pyqtSignal(int, str)
    input_filter_error = pyqtSignal(int, str)
    thermal_error = pyqtSignal(int, str)

    @pyqtSlot(int, object)
    def process(self, sequence: int, request: ProcessedFrameRequest) -> None:
        try:
            result = build_live_processed_sample_frame(**request.as_kwargs())
        except Exception as exc:  # pylint: disable=broad-except
            self.error.emit(sequence, f'{type(exc).__name__}: {exc}')
            return
        self.result_ready.emit(sequence, result)

    @pyqtSlot(int, object)
    def process_input_filter(self, sequence: int, request: LiveInputFilterRequest) -> None:
        try:
            result = build_live_input_filter_result(request)
        except Exception as exc:  # pylint: disable=broad-except
            self.input_filter_error.emit(sequence, f'{type(exc).__name__}: {exc}')
            return
        self.input_filter_result_ready.emit(sequence, result)

    @pyqtSlot(int, object)
    def process_thermal(self, sequence: int, request: LiveThermalInputRequest) -> None:
        try:
            result = build_live_thermal_input_result(request)
        except Exception as exc:  # pylint: disable=broad-except
            self.thermal_error.emit(sequence, f'{type(exc).__name__}: {exc}')
            return
        self.thermal_result_ready.emit(sequence, result)


__all__ = [
    'LiveInputFilterRequest',
    'LiveInputFilterResult',
    'ProcessedFrameRequest',
    'ProcessedFrameRequestChannel',
    'ProcessedFrameWorker',
]
