from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse, unquote

import pytest

from artisanlib.plot_report_export import (
    export_saved_profile_report_graph_comparison,
    report_graph_comparison_from_parity,
    report_graph_image_url,
)
from artisanlib.websocket_renderer_smoke import (
    WebSocketTemperatureSample,
    build_snapshot_from_websocket_stream,
)
from artisanlib.plot_export_parity_smoke import render_snapshot_export_parity


def test_report_graph_image_url_matches_report_cache_buster_style() -> None:
    url = report_graph_image_url('/tmp/artisanz report graph.png', cache_buster=42)

    assert url.startswith('file:')
    assert 'artisanz%20report%20graph.png' in url
    assert url.endswith('?dummy=42')


def test_report_graph_image_url_resolves_relative_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    relative_path = Path('reports') / 'graph.png'
    relative_path.parent.mkdir()
    relative_path.write_bytes(b'png')

    url = report_graph_image_url(relative_path)

    parsed = urlparse(url)
    assert parsed.scheme == 'file'
    assert Path(unquote(parsed.path)) == relative_path.resolve()


def test_export_saved_profile_report_graph_comparison_builds_report_assets(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')

    comparison = export_saved_profile_report_graph_comparison(
        'test/data/profile1.alog',
        output_dir=tmp_path,
        prefix='profile1-report',
        width=800,
        height=450,
        dpi=100,
        use_opengl=False,
        cache_buster=123,
    )

    assert comparison.source_kind == 'profile'
    assert comparison.source_path == 'test/data/profile1.alog'
    assert comparison.title == 'Guji Shakiso'
    assert comparison.sample_count > 1000
    assert comparison.view_state_matches is True
    assert comparison.view_state_within_tolerance is True
    assert comparison.view_state_max_delta == 0.0
    assert comparison.event_count >= 10
    assert comparison.event_value_count >= 5
    assert comparison.phase_band_count == 3
    assert comparison.area_count == 1

    assert comparison.matplotlib.backend == 'matplotlib'
    assert comparison.matplotlib.width == 800
    assert comparison.matplotlib.height == 450
    assert comparison.matplotlib.byte_count > 1000
    assert comparison.matplotlib.sampled_non_background_pixel_count is None
    assert Path(comparison.matplotlib.path).exists()
    assert comparison.matplotlib.url.startswith('file:')
    assert comparison.matplotlib.url.endswith('?dummy=123')

    assert comparison.pyqtgraph.backend == 'pyqtgraph'
    assert comparison.pyqtgraph.width == 800
    assert comparison.pyqtgraph.height == 450
    assert comparison.pyqtgraph.byte_count > 1000
    assert comparison.pyqtgraph.sampled_non_background_pixel_count is not None
    assert comparison.pyqtgraph.sampled_non_background_pixel_count > 0
    assert Path(comparison.pyqtgraph.path).exists()
    assert comparison.pyqtgraph.url.startswith('file:')
    assert comparison.pyqtgraph.url.endswith('?dummy=123')


def test_report_graph_comparison_requires_saved_profile_source(tmp_path: Path) -> None:
    samples = (
        WebSocketTemperatureSample(time_s=0.0, bt=120.0, et=160.0),
        WebSocketTemperatureSample(time_s=60.0, bt=150.0, et=180.0),
    )
    snapshot = build_snapshot_from_websocket_stream(samples)
    parity = render_snapshot_export_parity(
        snapshot,
        source_kind='websocket',
        source_path=None,
        sample_count=len(samples),
        output_dir=tmp_path,
        width=640,
        height=360,
        dpi=100,
        use_opengl=False,
    )

    with pytest.raises(ValueError, match='requires a saved profile source'):
        report_graph_comparison_from_parity(parity, width=640, height=360)


def test_report_graph_comparison_rejects_non_profile_with_source_path(tmp_path: Path) -> None:
    samples = (
        WebSocketTemperatureSample(time_s=0.0, bt=120.0, et=160.0),
        WebSocketTemperatureSample(time_s=60.0, bt=150.0, et=180.0),
    )
    snapshot = build_snapshot_from_websocket_stream(samples)
    parity = render_snapshot_export_parity(
        snapshot,
        source_kind='websocket',
        source_path='virtual.websocket',
        sample_count=len(samples),
        output_dir=tmp_path,
        width=640,
        height=360,
        dpi=100,
        use_opengl=False,
    )

    with pytest.raises(ValueError, match='requires a saved profile source'):
        report_graph_comparison_from_parity(parity, width=640, height=360)


def test_export_saved_profile_report_graph_comparison_rejects_missing_profile(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        export_saved_profile_report_graph_comparison(
            tmp_path / 'missing.alog',
            output_dir=tmp_path,
        )
