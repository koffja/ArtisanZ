from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from artisanlib.plot_pyqtgraph_adapter import PyQtGraphSnapshotRenderer


@dataclass(slots=True)
class PyQtGraphPlotTarget:
    widget: object
    temperature_plot: object
    ror_plot: object | None
    time_axis: object
    ror_axis: object | None
    renderer: PyQtGraphSnapshotRenderer
    opengl_requested: bool
    _previous_opengl: bool
    _pyqtgraph: Any

    def close(self) -> None:
        close_widget = getattr(self.widget, 'close', None)
        if callable(close_widget):
            close_widget()
        self._pyqtgraph.setConfigOptions(useOpenGL=self._previous_opengl)

    def configure_axes(
            self,
            *,
            time_grid: bool,
            temperature_grid: bool,
            time_tick_step: float,
            temperature_tick_step: float,
            ror_tick_step: float,
            time_label_mode: str,
            time_axis_start: float,
            grid_alpha: float,
            grid_width: int,
            grid_color: str,
            axis_color: str) -> None:
        _call_if_available(
            self.temperature_plot,
            'showGrid',
            x=time_grid,
            y=temperature_grid,
            alpha=_visible_grid_alpha(grid_alpha))
        _configure_axis_pen(self.temperature_plot, self._pyqtgraph, grid_color, axis_color, grid_width)
        _set_axis_tick_spacing(self.temperature_plot, 'bottom', time_tick_step)
        _set_axis_tick_spacing(self.temperature_plot, 'left', temperature_tick_step)
        if self.ror_axis is not None:
            _set_axis_tick_spacing(self.temperature_plot, 'right', ror_tick_step)
        configure_label_mode = getattr(self.time_axis, 'configure_label_mode', None)
        if callable(configure_label_mode):
            configure_label_mode(time_label_mode, time_axis_start)
        time_label = 'Time (s)' if time_label_mode == 'seconds' else 'Time (min)'
        _call_if_available(self.temperature_plot, 'setLabel', 'bottom', time_label)


def create_pyqtgraph_plot_target(
        *,
        use_opengl: bool = True,
        include_ror: bool = True) -> PyQtGraphPlotTarget:
    from PyQt6.QtWidgets import QApplication
    import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]

    QApplication.instance() or QApplication([])
    previous_opengl = bool(pg.getConfigOption('useOpenGL'))
    pg.setConfigOptions(useOpenGL=use_opengl)
    pg.setConfigOptions(antialias=True)

    widget = pg.GraphicsLayoutWidget()
    _call_if_available(widget, 'setBackground', '#F8F7F1')
    time_axis = _create_time_axis(pg)
    temperature_plot = widget.addPlot(row=0, col=0, axisItems={'bottom': time_axis})
    _configure_temperature_plot(temperature_plot, pg)
    ror_plot = None
    ror_axis = None
    if include_ror:
        ror_plot, ror_axis = _create_ror_overlay(temperature_plot, pg)

    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
    )
    return PyQtGraphPlotTarget(
        widget=widget,
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        time_axis=time_axis,
        ror_axis=ror_axis,
        renderer=renderer,
        opengl_requested=use_opengl,
        _previous_opengl=previous_opengl,
        _pyqtgraph=pg,
    )


def _configure_temperature_plot(plot: object, pg: Any) -> None:
    _configure_plot_surface(plot, pg)
    _call_if_available(plot, 'setLabel', 'left', 'Temperature')
    _call_if_available(plot, 'setLabel', 'bottom', 'Time')


def _configure_plot_surface(plot: object, pg: Any) -> None:
    _call_if_available(plot, 'showGrid', x=True, y=True, alpha=0.32)
    _call_if_available(plot, 'setMenuEnabled', False)
    view_box = getattr(plot, 'getViewBox', lambda: None)()
    _call_if_available(view_box, 'setBackgroundColor', '#F8F7F1')
    _call_if_available(view_box, 'setDefaultPadding', 0.0)
    _call_if_available(plot, 'showAxis', 'right')
    _call_if_available(plot, 'hideAxis', 'top')
    _call_if_available(plot, 'setDownsampling', mode='peak')
    _call_if_available(plot, 'setClipToView', True)
    _call_if_available(plot, 'setMouseEnabled', x=True, y=True)
    _configure_axis_pen(plot, pg, '#C9D2D4', '#5E6B6E', 1)


def _configure_axis_pen(plot: object, pg: Any, axis_color: str, text_color: str, width: int) -> None:
    axis_pen = pg.mkPen('#C9D2D4', width=1)
    try:
        axis_pen = pg.mkPen(axis_color, width=max(1, width))
    except Exception: # pylint: disable=broad-exception-caught
        pass
    try:
        text_pen = pg.mkPen(text_color, width=1)
    except Exception: # pylint: disable=broad-exception-caught
        text_pen = pg.mkPen('#5E6B6E', width=1)
    for axis_name in ('left', 'bottom', 'right'):
        axis = getattr(plot, 'getAxis', lambda _: None)(axis_name)
        _call_if_available(axis, 'setPen', axis_pen)
        _call_if_available(axis, 'setTextPen', text_pen)


def _create_ror_overlay(temperature_plot: object, pg: Any) -> tuple[PyQtGraphLinkedAxisPlot, object]:
    view_box = pg.ViewBox()
    _call_if_available(view_box, 'setDefaultPadding', 0.0)
    _call_if_available(temperature_plot, 'showAxis', 'right')
    right_axis = getattr(temperature_plot, 'getAxis', lambda _: None)('right')
    _call_if_available(right_axis, 'setLabel', 'RoR')
    _call_if_available(right_axis, 'linkToView', view_box)
    _call_if_available(view_box, 'setXLink', temperature_plot)
    scene = getattr(temperature_plot, 'scene', lambda: None)()
    _call_if_available(scene, 'addItem', view_box)

    base_view_box = getattr(temperature_plot, 'getViewBox', lambda: None)()

    def update_views() -> None:
        scene_bounding_rect = getattr(base_view_box, 'sceneBoundingRect', lambda: None)()
        if scene_bounding_rect is not None:
            _call_if_available(view_box, 'setGeometry', scene_bounding_rect)
        x_axis = getattr(view_box, 'XAxis', None)
        if x_axis is not None:
            _call_if_available(view_box, 'linkedViewChanged', base_view_box, x_axis)

    signal = getattr(base_view_box, 'sigResized', None)
    connect = getattr(signal, 'connect', None)
    if callable(connect):
        connect(update_views)
    update_views()
    return PyQtGraphLinkedAxisPlot(view_box=view_box, _pyqtgraph=pg), right_axis


@dataclass(slots=True)
class PyQtGraphLinkedAxisPlot:
    view_box: object
    _pyqtgraph: Any

    def plot(
            self,
            x: tuple[float, ...],
            y: tuple[float, ...],
            *,
            pen: object,
            name: str) -> object:
        item = self._pyqtgraph.PlotDataItem(x, y, pen=pen, name=name)
        _call_if_available(self.view_box, 'addItem', item)
        return item

    def setXRange(self, minimum: float, maximum: float, *, padding: float = 0.0) -> None:  # noqa: N802
        _call_with_optional_padding(self.view_box, 'setXRange', minimum, maximum, padding=padding)

    def setYRange(self, minimum: float, maximum: float, *, padding: float = 0.0) -> None:  # noqa: N802
        _call_with_optional_padding(self.view_box, 'setYRange', minimum, maximum, padding=padding)

    def disableAutoRange(self) -> None:  # noqa: N802
        _call_if_available(self.view_box, 'disableAutoRange')

    def viewRange(self) -> list[list[float]] | None:  # noqa: N802
        view_range = getattr(self.view_box, 'viewRange', None)
        if callable(view_range):
            return view_range()
        return None

    def listDataItems(self) -> list[object]:  # noqa: N802
        items = getattr(self.view_box, 'addedItems', [])
        return [item for item in items if isinstance(item, self._pyqtgraph.PlotDataItem)]


def _create_time_axis(pg: Any) -> object:
    class TimeAxisItem(pg.AxisItem):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__(orientation='bottom')
            self._label_mode = 'minutes'
            self._start_time = 0.0

        def configure_label_mode(self, label_mode: str, start_time: float) -> None:
            self._label_mode = label_mode if label_mode == 'seconds' else 'minutes'
            self._start_time = float(start_time)

        def tickStrings(self, values: list[float], scale: float, spacing: float) -> list[str]:  # noqa: N802
            del scale, spacing
            return [
                _format_time_tick(value, self._start_time, self._label_mode)
                for value in values
            ]

    return TimeAxisItem()


def _format_time_tick(value: float, start_time: float, label_mode: str) -> str:
    seconds = int(round(value - start_time))
    if label_mode == 'seconds':
        return str(seconds)
    sign = '-' if seconds < 0 else ''
    minutes, remaining_seconds = divmod(abs(seconds), 60)
    return f'{sign}{minutes}:{remaining_seconds:02d}'


def _set_axis_tick_spacing(plot: object, axis_name: str, step: float) -> None:
    axis = getattr(plot, 'getAxis', lambda _: None)(axis_name)
    if step <= 0:
        _call_if_available(axis, 'setTickSpacing')
        return
    _call_if_available(axis, 'setTickSpacing', levels=[(float(step), 0.0)])


def _visible_grid_alpha(grid_alpha: float) -> float:
    return min(1.0, max(0.28, grid_alpha * 1.6))


def _call_with_optional_padding(
        target: object,
        method_name: str,
        minimum: float,
        maximum: float,
        *,
        padding: float) -> None:
    method = getattr(target, method_name, None)
    if not callable(method):
        return
    try:
        method(minimum, maximum, padding=padding)
    except TypeError:
        method(minimum, maximum)


def _call_if_available(target: object, method_name: str, *args: object, **kwargs: object) -> None:
    method = getattr(target, method_name, None)
    if callable(method):
        method(*args, **kwargs)


__all__ = [
    'PyQtGraphLinkedAxisPlot',
    'PyQtGraphPlotTarget',
    'create_pyqtgraph_plot_target',
]
