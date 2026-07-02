from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from artisanlib.plot_pyqtgraph_export import PyQtGraphSnapshotPngResult, export_pyqtgraph_snapshot_png
from artisanlib.plot_snapshot_extractor import build_roast_plot_snapshot


DEFAULT_EXPORT_WIDTH = 1280
DEFAULT_EXPORT_HEIGHT = 720


@dataclass(frozen=True, slots=True)
class PyQtGraphUserExportResult:
    path: str
    width: int
    height: int
    byte_count: int
    sampled_non_background_pixel_count: int
    temperature_item_count: int
    ror_item_count: int
    event_item_count: int
    event_value_item_count: int
    guide_item_count: int
    area_item_count: int


def export_current_graph_pyqtgraph_png(
        source: object,
        output_path: str | Path,
        *,
        width: int | None = None,
        height: int | None = None,
        use_opengl: bool = False) -> PyQtGraphUserExportResult:
    export_width, export_height = current_graph_export_size(
        source,
        width=width,
        height=height,
    )
    result = export_pyqtgraph_snapshot_png(
        build_roast_plot_snapshot(source),
        normalize_png_export_path(output_path),
        width=export_width,
        height=export_height,
        use_opengl=use_opengl,
    )
    return _user_export_result(result)


def normalize_png_export_path(path: str | Path) -> str:
    filename = str(path)
    if not filename.lower().endswith('.png'):
        filename += '.png'
    return filename


def current_graph_export_size(
        source: object,
        *,
        width: int | None = None,
        height: int | None = None) -> tuple[int, int]:
    if width is not None and width <= 0:
        raise ValueError(f'export width must be positive, got {width}')
    if height is not None and height <= 0:
        raise ValueError(f'export height must be positive, got {height}')
    widget_width, widget_height = _current_graph_widget_size(source)
    export_width = width or widget_width or DEFAULT_EXPORT_WIDTH
    export_height = height or widget_height or DEFAULT_EXPORT_HEIGHT
    return export_width, export_height


def _current_graph_widget_size(source: object) -> tuple[int | None, int | None]:
    widget = _current_graph_widget(source)
    if widget is None:
        return None, None
    width = _positive_int_from_callable(widget, 'width')
    height = _positive_int_from_callable(widget, 'height')
    if width is None or height is None:
        return None, None
    return width, height


def _current_graph_widget(source: object) -> object | None:
    graph_widget = getattr(source, 'graph_widget', None)
    if callable(graph_widget):
        widget = graph_widget()
        if widget is not None:
            return widget
    pyqtgraph_target = getattr(source, 'plot_pyqtgraph_target', None)
    widget = getattr(pyqtgraph_target, 'widget', None)
    if widget is not None:
        return widget
    return getattr(source, 'canvas', None)


def _positive_int_from_callable(target: object, method_name: str) -> int | None:
    method = getattr(target, method_name, None)
    if not callable(method):
        return None
    value = method()
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return None
    return integer if integer > 0 else None


def _user_export_result(result: PyQtGraphSnapshotPngResult) -> PyQtGraphUserExportResult:
    return PyQtGraphUserExportResult(
        path=result.path,
        width=result.width,
        height=result.height,
        byte_count=result.byte_count,
        sampled_non_background_pixel_count=result.sampled_non_background_pixel_count,
        temperature_item_count=result.temperature_item_count,
        ror_item_count=result.ror_item_count,
        event_item_count=result.renderer_event_item_count,
        event_value_item_count=result.renderer_event_value_item_count,
        guide_item_count=result.renderer_guide_item_count,
        area_item_count=result.renderer_area_item_count,
    )


__all__ = [
    'DEFAULT_EXPORT_HEIGHT',
    'DEFAULT_EXPORT_WIDTH',
    'PyQtGraphUserExportResult',
    'current_graph_export_size',
    'export_current_graph_pyqtgraph_png',
    'normalize_png_export_path',
]
