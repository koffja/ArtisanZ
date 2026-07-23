"""Tests for the queued pure processed-frame worker boundary."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from PyQt6.QtCore import QCoreApplication, QEventLoop, QThread, QTimer, Qt

from artisanlib.processed_frame_worker import (
    ProcessedFrameRequest,
    ProcessedFrameRequestChannel,
    ProcessedFrameWorker,
)
from artisanlib.sample_processing import build_live_processed_sample_frame


def _request(sample_times: tuple[float, ...] = (0.0, 1.0, 2.0)) -> ProcessedFrameRequest:
    return ProcessedFrameRequest(
        timestamp=2.0,
        sample_count=3,
        latest_et=190.0,
        latest_bt=185.0,
        smoothed_et=189.0,
        smoothed_bt=184.0,
        pid_process_value=184.0,
        raw_delta_et=8.0,
        raw_delta_bt=6.0,
        ror_limit_enabled=False,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
        charge_index=0,
        dry_index=0,
        drop_index=0,
        delta_et_filter=0.0,
        delta_bt_filter=0.0,
        delta_et_samples=2,
        delta_bt_samples=2,
        fix_max_time=False,
        lock_time_x=False,
        sample_times=sample_times,
        start_of_x=-30.0,
        end_of_x=600.0,
        tp_alarm_timeindex=None,
        tp_max_roast_time=120.0,
        auto_charge_idx=0,
        auto_charge_flag=False,
        auto_charge_enabled=False,
        auto_drop_idx=0,
        auto_drop_flag=False,
        auto_drop_enabled=False,
        mode='C',
    )


def test_request_is_immutable_and_helper_equivalent() -> None:
    request = _request()

    result = build_live_processed_sample_frame(**request.as_kwargs())

    assert request.sample_times == (0.0, 1.0, 2.0)
    assert result.displayed_delta_et == 8.0
    assert result.displayed_delta_bt == 6.0
    assert result.delta_et_window == (1, 3)
    assert result.delta_bt_window == (1, 3)


def test_request_snapshot_does_not_follow_source_sequence() -> None:
    source = [0.0, 1.0]
    request = _request(source)  # type: ignore[arg-type]
    source.append(2.0)

    assert request.sample_times == (0.0, 1.0)
    assert request.as_kwargs()['sample_times'] == (0.0, 1.0)
    with pytest.raises(FrozenInstanceError):
        request.timestamp = 3.0  # type: ignore[misc]


def test_worker_reports_typed_error_and_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    import artisanlib.processed_frame_worker as worker_module

    errors: list[tuple[int, str]] = []
    results: list[int] = []
    worker = ProcessedFrameWorker()
    worker.error.connect(lambda sequence, message: errors.append((sequence, message)))
    worker.result_ready.connect(lambda sequence, _result: results.append(sequence))

    def fail(**_kwargs: object) -> object:
        raise ValueError('invalid frame')

    monkeypatch.setattr(worker_module, 'build_live_processed_sample_frame', fail)
    worker.process(11, _request())
    assert errors == [(11, 'ValueError: invalid frame')]
    assert results == []

    monkeypatch.setattr(worker_module, 'build_live_processed_sample_frame', build_live_processed_sample_frame)
    worker.process(12, _request())
    assert results == [12]


def test_worker_queues_request_and_returns_result_on_gui_thread() -> None:
    app = QCoreApplication.instance() or QCoreApplication([])
    thread = QThread()
    thread.setObjectName('processed-frame-worker-test')
    worker = ProcessedFrameWorker()
    channel = ProcessedFrameRequestChannel()
    worker.moveToThread(thread)
    channel.request.connect(worker.process, type=Qt.ConnectionType.QueuedConnection)

    worker_thread_names: list[str] = []
    results: list[tuple[int, object, str]] = []
    loop = QEventLoop()

    def observe_worker_result(_sequence: int, _result: object) -> None:
        worker_thread_names.append(QThread.currentThread().objectName())

    def receive_result(sequence: int, result: object) -> None:
        results.append((sequence, result, QThread.currentThread().objectName()))
        loop.quit()

    worker.result_ready.connect(observe_worker_result, type=Qt.ConnectionType.DirectConnection)
    worker.result_ready.connect(receive_result, type=Qt.ConnectionType.QueuedConnection)
    thread.finished.connect(worker.deleteLater)
    thread.start()
    try:
        channel.request.emit(7, _request())
        QTimer.singleShot(2000, loop.quit)
        loop.exec()

        assert len(results) == 1
        assert results[0][0] == 7
        assert results[0][1].displayed_delta_bt == 6.0
        assert worker_thread_names == ['processed-frame-worker-test']
        assert results[0][2] == app.thread().objectName()
    finally:
        thread.quit()
        assert thread.wait(2000)
