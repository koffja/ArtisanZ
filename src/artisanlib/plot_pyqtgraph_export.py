from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from artisanlib.plot_pyqtgraph_widget import create_pyqtgraph_plot_target
from artisanlib.plot_snapshot import RendererViewState, RoastPlotSnapshot


@dataclass(frozen=True, slots=True)
class PyQtGraphWidgetPngResult:
    path: str
    width: int
    height: int
    byte_count: int
    sampled_pixel_count: int
    sampled_non_background_pixel_count: int


@dataclass(frozen=True, slots=True)
class PyQtGraphSnapshotPngResult:
    path: str
    width: int
    height: int
    byte_count: int
    sampled_pixel_count: int
    sampled_non_background_pixel_count: int
    temperature_item_count: int
    ror_item_count: int
    renderer_event_item_count: int
    renderer_event_value_item_count: int
    renderer_guide_item_count: int
    renderer_area_item_count: int
    view_state: RendererViewState


def export_pyqtgraph_snapshot_png(
        snapshot: RoastPlotSnapshot,
        output_path: str | Path,
        *,
        width: int = 1280,
        height: int = 720,
        use_opengl: bool = False,
        pixel_sample_stride: int = 4) -> PyQtGraphSnapshotPngResult:
    from PyQt6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    target = create_pyqtgraph_plot_target(
        use_opengl=use_opengl,
        include_ror=snapshot.ror_axis is not None,
    )
    try:
        target.renderer.set_snapshot(snapshot)
        application.processEvents()
        image_result = save_pyqtgraph_widget_png(
            target.widget,
            output_path,
            application=application,
            width=width,
            height=height,
            pixel_sample_stride=pixel_sample_stride,
        )
        return PyQtGraphSnapshotPngResult(
            path=image_result.path,
            width=image_result.width,
            height=image_result.height,
            byte_count=image_result.byte_count,
            sampled_pixel_count=image_result.sampled_pixel_count,
            sampled_non_background_pixel_count=image_result.sampled_non_background_pixel_count,
            temperature_item_count=_plot_data_item_count(target.temperature_plot),
            ror_item_count=0 if target.ror_plot is None else _plot_data_item_count(target.ror_plot),
            renderer_event_item_count=target.renderer.event_item_count(),
            renderer_event_value_item_count=target.renderer.event_value_item_count(),
            renderer_guide_item_count=target.renderer.guide_item_count(),
            renderer_area_item_count=target.renderer.area_item_count(),
            view_state=target.renderer.export_view_state(),
        )
    finally:
        target.close()


def save_pyqtgraph_widget_png(
        widget: object,
        output_path: str | Path,
        *,
        application: object | None = None,
        width: int = 1280,
        height: int = 720,
        pixel_sample_stride: int = 4,
        background_rgb: tuple[int, int, int] = (248, 247, 241),
        color_tolerance: int = 8) -> PyQtGraphWidgetPngResult:
    if width <= 0 or height <= 0:
        raise ValueError(f'PNG export size must be positive, got {width}x{height}')
    if pixel_sample_stride <= 0:
        raise ValueError(f'pixel_sample_stride must be positive, got {pixel_sample_stride}')

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _call_if_available(widget, 'resize', width, height)
    _call_if_available(widget, 'show')
    _process_events(application)

    grab = getattr(widget, 'grab', None)
    if not callable(grab):
        raise RuntimeError('PyQtGraph widget does not support grab() for PNG export')
    pixmap = grab()
    is_null = getattr(pixmap, 'isNull', None)
    if callable(is_null) and is_null():
        raise RuntimeError('PyQtGraph widget grab produced a null pixmap')
    save = getattr(pixmap, 'save', None)
    if not callable(save) or not save(str(path)):
        raise RuntimeError(f'Failed to save PyQtGraph PNG to {path}')

    image = pixmap.toImage()
    image_width = int(image.width())
    image_height = int(image.height())
    sampled_pixels, non_background_pixels = _sample_non_background_pixels(
        image,
        background_rgb=background_rgb,
        color_tolerance=color_tolerance,
        stride=pixel_sample_stride,
    )
    return PyQtGraphWidgetPngResult(
        path=str(path),
        width=image_width,
        height=image_height,
        byte_count=path.stat().st_size,
        sampled_pixel_count=sampled_pixels,
        sampled_non_background_pixel_count=non_background_pixels,
    )


def _sample_non_background_pixels(
        image: object,
        *,
        background_rgb: tuple[int, int, int],
        color_tolerance: int,
        stride: int) -> tuple[int, int]:
    pixel_color = getattr(image, 'pixelColor', None)
    if not callable(pixel_color):
        return (0, 0)
    sampled_pixels = 0
    non_background_pixels = 0
    width = int(image.width())
    height = int(image.height())
    for y in range(0, height, stride):
        for x in range(0, width, stride):
            color = pixel_color(x, y)
            sampled_pixels += 1
            if _rgb_distance_exceeds_tolerance(
                    (int(color.red()), int(color.green()), int(color.blue())),
                    background_rgb,
                    color_tolerance,
            ):
                non_background_pixels += 1
    return sampled_pixels, non_background_pixels


def _rgb_distance_exceeds_tolerance(
        rgb: tuple[int, int, int],
        background_rgb: tuple[int, int, int],
        tolerance: int) -> bool:
    return any(abs(channel - background) > tolerance for channel, background in zip(rgb, background_rgb, strict=True))


def _plot_data_item_count(plot: object) -> int:
    list_data_items = getattr(plot, 'listDataItems', None)
    if callable(list_data_items):
        return len(list_data_items())
    return 0


def _process_events(application: object | None) -> None:
    process_events = getattr(application, 'processEvents', None)
    if callable(process_events):
        process_events()


def _call_if_available(target: object, method_name: str, *args: object, **kwargs: object) -> None:
    method = getattr(target, method_name, None)
    if callable(method):
        method(*args, **kwargs)


__all__ = [
    'PyQtGraphSnapshotPngResult',
    'PyQtGraphWidgetPngResult',
    'export_pyqtgraph_snapshot_png',
    'save_pyqtgraph_widget_png',
]
