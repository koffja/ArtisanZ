from __future__ import annotations

from pathlib import Path

import pytest

from artisanlib.plot_export_parity_smoke import (
    render_snapshot_export_parity,
    run_profile_export_parity_smoke,
    run_websocket_export_parity_smoke,
)
from artisanlib.websocket_renderer_smoke import (
    WebSocketPushEvent,
    WebSocketTemperatureSample,
    build_snapshot_from_websocket_stream,
)


def test_render_snapshot_export_parity_writes_both_pngs(
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

    result = render_snapshot_export_parity(
        snapshot,
        output_dir=tmp_path,
        prefix='direct snapshot',
        width=640,
        height=360,
        dpi=80,
        use_opengl=False,
    )

    matplotlib_path = Path(result.matplotlib.path)
    pyqtgraph_path = Path(result.pyqtgraph.path)
    assert result.prefix == 'direct-snapshot'
    assert matplotlib_path.exists()
    assert pyqtgraph_path.exists()
    assert matplotlib_path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assert pyqtgraph_path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assert result.matplotlib.byte_count > 1000
    assert result.pyqtgraph.byte_count > 1000
    assert result.pyqtgraph.sampled_non_background_pixel_count > 0
    assert result.view_state_within_tolerance is True
    assert result.view_state_max_delta <= 2.0
    assert result.matplotlib.ror_line_count >= 2
    assert result.pyqtgraph.ror_item_count >= 2
    assert result.matplotlib.event_artist_count == result.event_count * 2
    assert result.matplotlib.phase_artist_count == result.phase_band_count
    assert result.matplotlib.area_artist_count == result.area_count
    assert result.matplotlib.event_value_artist_count == result.event_value_count
    assert result.matplotlib.guide_artist_count == result.guide_count
    assert result.pyqtgraph.renderer_event_item_count >= result.event_count
    assert result.pyqtgraph.renderer_area_item_count == result.area_count
    assert result.pyqtgraph.renderer_event_value_item_count == result.event_value_count
    assert result.pyqtgraph.renderer_guide_item_count == result.guide_count
    assert result.area_count == 1


def test_run_websocket_export_parity_smoke_uses_event_heavy_virtual_data(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    result = run_websocket_export_parity_smoke(
        sample_count=12,
        fixed_step_ms=30_000.0,
        scenario='event-heavy',
        output_dir=tmp_path,
        width=640,
        height=360,
        dpi=80,
        use_opengl=False,
    )

    assert Path(result.matplotlib.path).exists()
    assert Path(result.pyqtgraph.path).exists()
    assert result.event_count >= 10
    assert result.event_value_count >= 6
    assert result.guide_count == 3
    assert result.area_count == 1
    assert result.view_state_within_tolerance is True
    assert result.matplotlib.phase_artist_count == result.phase_band_count
    assert result.matplotlib.area_artist_count == result.area_count
    assert result.matplotlib.event_value_artist_count == result.event_value_count
    assert result.matplotlib.guide_artist_count == result.guide_count
    assert result.pyqtgraph.renderer_area_item_count == result.area_count
    assert result.pyqtgraph.renderer_event_value_item_count == result.event_value_count
    assert result.pyqtgraph.renderer_guide_item_count == result.guide_count
    assert result.matplotlib.byte_count > 1000
    assert result.pyqtgraph.byte_count > 1000
    assert result.pyqtgraph.sampled_non_background_pixel_count > 0


def test_run_profile_export_parity_smoke_uses_saved_alog(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    profile_path = Path('test/data/profile1.alog')

    result = run_profile_export_parity_smoke(
        profile_path,
        output_dir=tmp_path,
        width=800,
        height=450,
        dpi=100,
        use_opengl=False,
    )

    assert result.source_kind == 'profile'
    assert result.source_path == str(profile_path)
    assert result.sample_count > 1000
    assert Path(result.matplotlib.path).exists()
    assert Path(result.pyqtgraph.path).exists()
    assert result.event_count >= 10
    assert result.event_value_count >= 5
    assert result.phase_band_count == 3
    assert result.area_count == 1
    assert result.view_state_within_tolerance is True
    assert result.matplotlib.phase_artist_count == result.phase_band_count
    assert result.matplotlib.area_artist_count == result.area_count
    assert result.pyqtgraph.renderer_area_item_count == result.area_count
    assert result.matplotlib.byte_count > 1000
    assert result.pyqtgraph.byte_count > 1000
    assert result.pyqtgraph.sampled_non_background_pixel_count > 0
