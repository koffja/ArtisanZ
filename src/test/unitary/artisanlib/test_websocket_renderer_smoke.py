from __future__ import annotations

from pathlib import Path

import pytest

from dev_simulator.ws_server import ServerState

from artisanlib.plot_snapshot import AreaFillSnapshot
from artisanlib.plot_pyqtgraph_export import export_pyqtgraph_snapshot_png
from artisanlib.websocket_renderer_smoke import (
    WebSocketPushEvent,
    WebSocketTemperatureSample,
    build_snapshot_from_websocket_stream,
    run_websocket_pyqtgraph_validation,
)


def test_server_state_fixed_step_advances_deterministically() -> None:
    state = ServerState(fixed_step_ms=2500.0)

    assert state.advance() == 0.0
    assert state.advance() == 2500.0
    assert state.advance() == 5000.0


def test_server_state_fixed_step_rejects_non_positive_values() -> None:
    with pytest.raises(ValueError, match='fixed_step_ms must be positive'):
        ServerState(fixed_step_ms=0.0)


def test_build_snapshot_from_websocket_stream_adds_curves_overlays_and_guides() -> None:
    samples = (
        WebSocketTemperatureSample(time_s=0.0, bt=180.0, et=190.0),
        WebSocketTemperatureSample(time_s=30.0, bt=165.0, et=184.0),
        WebSocketTemperatureSample(time_s=60.0, bt=150.0, et=178.0),
    )
    events = (
        WebSocketPushEvent(
            time_s=30.0,
            label='Power',
            event_type=1,
            color='#B4685C',
            value=72.0,
        ),
    )

    snapshot = build_snapshot_from_websocket_stream(samples, events)

    assert [curve.name for curve in snapshot.curves] == ['BT', 'ET', 'Delta BT', 'Delta ET']
    assert snapshot.curves[2].y == (None, -30.0, -30.0)
    assert len(snapshot.events) == 1
    assert len(snapshot.event_values) == 1
    assert len(snapshot.phase_bands) == 3
    assert {guide.kind for guide in snapshot.guides} == {'auc', 'bbp', 'charge_target'}
    assert snapshot.areas == ()


def test_build_snapshot_from_websocket_stream_adds_auc_area_after_drop() -> None:
    samples = (
        WebSocketTemperatureSample(time_s=0.0, bt=180.0, et=190.0),
        WebSocketTemperatureSample(time_s=60.0, bt=130.0, et=180.0),
        WebSocketTemperatureSample(time_s=120.0, bt=165.0, et=190.0),
        WebSocketTemperatureSample(time_s=180.0, bt=190.0, et=205.0),
    )
    events = (
        WebSocketPushEvent(time_s=0.0, label='CHARGE', event_type=100, color='#5E6B6E', kind='main'),
        WebSocketPushEvent(time_s=180.0, label='DROP', event_type=106, color='#5E6B6E', kind='main'),
    )

    snapshot = build_snapshot_from_websocket_stream(samples, events)

    assert snapshot.areas == (
        AreaFillSnapshot.from_sequences(
            x=[60.0, 120.0, 180.0],
            y=[130.0, 165.0, 190.0],
            baseline=130.0,
            color='#767676',
            label='AUC area',
            opacity=0.28,
            kind='auc',
        ),
    )


def test_export_pyqtgraph_snapshot_png_writes_renderer_evidence(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    samples = (
        WebSocketTemperatureSample(time_s=0.0, bt=180.0, et=190.0),
        WebSocketTemperatureSample(time_s=60.0, bt=130.0, et=180.0),
        WebSocketTemperatureSample(time_s=120.0, bt=165.0, et=190.0),
        WebSocketTemperatureSample(time_s=180.0, bt=190.0, et=205.0),
    )
    events = (
        WebSocketPushEvent(time_s=0.0, label='CHARGE', event_type=100, color='#5E6B6E', kind='main'),
        WebSocketPushEvent(time_s=60.0, label='Power', event_type=1, color='#B4685C', value=72.0),
        WebSocketPushEvent(time_s=180.0, label='DROP', event_type=106, color='#5E6B6E', kind='main'),
    )
    snapshot = build_snapshot_from_websocket_stream(samples, events)
    output_path = tmp_path / 'snapshot.png'

    result = export_pyqtgraph_snapshot_png(
        snapshot,
        output_path,
        width=640,
        height=360,
        use_opengl=False,
        pixel_sample_stride=8,
    )

    assert result.path == str(output_path)
    assert output_path.exists()
    assert result.byte_count == output_path.stat().st_size
    assert result.byte_count > 0
    assert result.width > 0
    assert result.height > 0
    assert result.sampled_pixel_count > 0
    assert result.sampled_non_background_pixel_count > 0
    assert result.temperature_item_count >= 4
    assert result.ror_item_count >= 2
    assert result.renderer_event_item_count >= 3
    assert result.renderer_event_value_item_count == 1
    assert result.renderer_guide_item_count == 3
    assert result.renderer_area_item_count == 1
    assert result.view_state.time_axis.maximum > result.view_state.time_axis.minimum


def test_websocket_pyqtgraph_validation_runs_with_virtual_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    result = run_websocket_pyqtgraph_validation(
        sample_count=12,
        fixed_step_ms=30_000.0,
        use_opengl=False,
    )

    assert result.sample_count == 12
    assert result.data_message_count == 12
    assert result.push_message_count >= 5
    assert result.event_count >= 5
    assert result.event_value_count >= 2
    assert result.guide_count == 3
    assert result.area_count == 1
    assert result.temperature_item_count >= 4
    assert result.ror_item_count >= 2
    assert result.renderer_event_item_count >= result.event_count
    assert result.renderer_event_value_item_count == result.event_value_count
    assert result.renderer_guide_item_count == 3
    assert result.renderer_area_item_count == result.area_count
    assert result.full_snapshot_count >= 1
    assert result.live_update_count >= 1
    assert result.max_update_ms >= result.avg_update_ms > 0.0


def test_websocket_pyqtgraph_validation_runs_event_heavy_screenshot(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    screenshot_file = tmp_path / 'event-heavy.png'

    result = run_websocket_pyqtgraph_validation(
        sample_count=24,
        fixed_step_ms=15_000.0,
        use_opengl=False,
        scenario='event-heavy',
        screenshot_file=str(screenshot_file),
    )

    assert result.event_count >= 10
    assert result.event_value_count >= 6
    assert result.area_count == 1
    assert result.renderer_area_item_count == 1
    assert result.screenshot_file == str(screenshot_file)
    assert result.screenshot_width is not None and result.screenshot_width > 0
    assert result.screenshot_height is not None and result.screenshot_height > 0
    assert result.screenshot_byte_count is not None and result.screenshot_byte_count > 0
    assert result.screenshot_sampled_pixel_count is not None and result.screenshot_sampled_pixel_count > 0
    assert (
        result.screenshot_sampled_non_background_pixel_count is not None
        and result.screenshot_sampled_non_background_pixel_count > 0
    )
    assert screenshot_file.exists()
    assert screenshot_file.stat().st_size > 0
