from __future__ import annotations

from pathlib import Path

import pytest

from artisanlib.plot_profile_snapshot import ProfileSnapshotSource
from artisanlib.plot_user_export import (
    DEFAULT_EXPORT_HEIGHT,
    DEFAULT_EXPORT_WIDTH,
    current_graph_export_size,
    export_current_graph_pyqtgraph_png,
    normalize_png_export_path,
)
from artisanlib.util import deserialize


class FakeWidget:
    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height

    def width(self) -> int:
        return self._width

    def height(self) -> int:
        return self._height


class FakeGraphSource:
    def __init__(self, widget: FakeWidget | None = None) -> None:
        self._widget = widget

    def graph_widget(self) -> FakeWidget | None:
        return self._widget


def test_normalize_png_export_path_appends_png_case_insensitively() -> None:
    assert normalize_png_export_path('/tmp/profile') == '/tmp/profile.png'
    assert normalize_png_export_path('/tmp/profile.PNG') == '/tmp/profile.PNG'
    assert normalize_png_export_path(Path('/tmp/profile.jpg')) == '/tmp/profile.jpg.png'


def test_current_graph_export_size_uses_current_widget_dimensions() -> None:
    assert current_graph_export_size(FakeGraphSource(FakeWidget(900, 500))) == (900, 500)


def test_current_graph_export_size_uses_defaults_without_widget() -> None:
    assert current_graph_export_size(FakeGraphSource()) == (DEFAULT_EXPORT_WIDTH, DEFAULT_EXPORT_HEIGHT)


def test_current_graph_export_size_rejects_invalid_explicit_size() -> None:
    with pytest.raises(ValueError, match='export width must be positive'):
        current_graph_export_size(FakeGraphSource(), width=0)
    with pytest.raises(ValueError, match='export height must be positive'):
        current_graph_export_size(FakeGraphSource(), height=-1)


def test_export_current_graph_pyqtgraph_png_uses_saved_profile_source(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    profile = deserialize('test/data/profile1.alog')
    source = ProfileSnapshotSource(profile)

    result = export_current_graph_pyqtgraph_png(
        source,
        tmp_path / 'profile-export',
        width=640,
        height=360,
        use_opengl=False,
    )

    output_path = Path(result.path)
    assert output_path.exists()
    assert output_path.name == 'profile-export.png'
    assert output_path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assert result.width == 640
    assert result.height == 360
    assert result.byte_count > 1000
    assert result.sampled_non_background_pixel_count > 0
    assert result.temperature_item_count >= 2
    assert result.ror_item_count >= 2
    assert result.event_item_count >= 10
    assert result.event_value_item_count >= 5
    assert result.area_item_count == 1
