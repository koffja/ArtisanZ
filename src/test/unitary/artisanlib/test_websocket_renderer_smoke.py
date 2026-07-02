from __future__ import annotations

import pytest

from dev_simulator.ws_server import ServerState

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
    assert result.temperature_item_count >= 4
    assert result.ror_item_count >= 2
    assert result.renderer_event_item_count >= result.event_count
    assert result.renderer_event_value_item_count == result.event_value_count
    assert result.renderer_guide_item_count == 3
    assert result.full_snapshot_count >= 1
    assert result.live_update_count >= 1
    assert result.max_update_ms >= result.avg_update_ms > 0.0
