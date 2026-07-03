from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math
from typing import Any

from artisanlib.plot_pyqtgraph_adapter import PyQtGraphSnapshotRenderer

CursorPositionCallback = Callable[[float, float, float | None], None]


@dataclass(slots=True)
class PyQtGraphPlotTarget:
    widget: object
    temperature_plot: object
    ror_plot: object | None
    time_axis: object
    ror_axis: object | None
    grid_item: object | None
    renderer: PyQtGraphSnapshotRenderer
    opengl_requested: bool
    _previous_opengl: bool
    _pyqtgraph: Any
    _cursor_callback: CursorPositionCallback | None = None
    _cursor_mouse_move_handler: object | None = None

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
            grid_line_style: str = '-',
            axis_color: str) -> None:
        # A dedicated GridItem gives consistent visible gridlines across Qt
        # styles; PlotItem.showGrid can be too faint on the light roast canvas.
        _call_if_available(self.temperature_plot, 'showGrid', x=False, y=False, alpha=0.0)
        _configure_grid_overlay(
            self.grid_item,
            self._pyqtgraph,
            x_visible=time_grid,
            y_visible=temperature_grid,
            x_tick_step=time_tick_step,
            y_tick_step=temperature_tick_step,
            grid_alpha=grid_alpha,
            grid_width=grid_width,
            grid_color=grid_color,
            grid_line_style=grid_line_style,
        )
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

    def set_cursor_callback(self, callback: CursorPositionCallback | None) -> None:
        self._cursor_callback = callback

    def emit_cursor_position(self, time: float, temperature: float, ror: float | None) -> None:
        if self._cursor_callback is not None:
            self._cursor_callback(float(time), float(temperature), None if ror is None else float(ror))


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
    grid_item = _create_grid_overlay(temperature_plot, pg)
    legend_item = _create_legend(temperature_plot, pg)
    ror_plot = None
    ror_axis = None
    if include_ror:
        ror_plot, ror_axis = _create_ror_overlay(temperature_plot, pg)

    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        legend_item=legend_item,
    )
    target = PyQtGraphPlotTarget(
        widget=widget,
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        time_axis=time_axis,
        ror_axis=ror_axis,
        grid_item=grid_item,
        renderer=renderer,
        opengl_requested=use_opengl,
        _previous_opengl=previous_opengl,
        _pyqtgraph=pg,
    )
    _connect_cursor_tracking(target)
    return target


def _configure_temperature_plot(plot: object, pg: Any) -> None:
    _configure_plot_surface(plot, pg)
    _call_if_available(plot, 'setLabel', 'left', 'Temperature')
    _call_if_available(plot, 'setLabel', 'bottom', 'Time')


def _configure_plot_surface(plot: object, pg: Any) -> None:
    _call_if_available(plot, 'showGrid', x=False, y=False, alpha=0.0)
    _call_if_available(plot, 'setMenuEnabled', False)
    _remove_auto_range_button(plot)
    view_box = getattr(plot, 'getViewBox', lambda: None)()
    _call_if_available(view_box, 'setBackgroundColor', '#F8F7F1')
    _call_if_available(view_box, 'setDefaultPadding', 0.0)
    _call_if_available(plot, 'showAxis', 'right')
    _call_if_available(plot, 'hideAxis', 'top')
    _call_if_available(plot, 'setDownsampling', mode='peak')
    _call_if_available(plot, 'setClipToView', True)
    _call_if_available(plot, 'setMouseEnabled', x=True, y=True)
    _configure_axis_pen(plot, pg, '#C9D2D4', '#5E6B6E', 1)


def _remove_auto_range_button(plot: object) -> None:
    auto_button = getattr(plot, 'autoBtn', None)
    if auto_button is None:
        return
    _call_if_available(auto_button, 'hide')
    _call_if_available(auto_button, 'setEnabled', False)
    set_parent_item = getattr(auto_button, 'setParentItem', None)
    if callable(set_parent_item):
        set_parent_item(None)


def _connect_cursor_tracking(target: PyQtGraphPlotTarget) -> None:
    scene = getattr(target.temperature_plot, 'scene', lambda: None)()
    signal = getattr(scene, 'sigMouseMoved', None)
    connect = getattr(signal, 'connect', None)
    if not callable(connect):
        return

    def on_mouse_moved(scene_pos: object) -> None:
        if not _plot_scene_contains(target.temperature_plot, scene_pos):
            return
        view_box = getattr(target.temperature_plot, 'getViewBox', lambda: None)()
        map_scene_to_view = getattr(view_box, 'mapSceneToView', None)
        if not callable(map_scene_to_view):
            return
        point = map_scene_to_view(scene_pos)
        ror_value = _mapped_ror_value(target.ror_plot, scene_pos)
        target.emit_cursor_position(float(point.x()), float(point.y()), ror_value)

    target._cursor_mouse_move_handler = on_mouse_moved
    connect(on_mouse_moved)


def _plot_scene_contains(plot: object, scene_pos: object) -> bool:
    scene_rect = getattr(plot, 'sceneBoundingRect', lambda: None)()
    contains = getattr(scene_rect, 'contains', None)
    if callable(contains):
        return bool(contains(scene_pos))
    return True


def _mapped_ror_value(ror_plot: object | None, scene_pos: object) -> float | None:
    if ror_plot is None:
        return None
    view_box = getattr(ror_plot, 'view_box', None)
    if view_box is None:
        view_box = getattr(ror_plot, 'getViewBox', lambda: None)()
    map_scene_to_view = getattr(view_box, 'mapSceneToView', None)
    if not callable(map_scene_to_view):
        return None
    try:
        point = map_scene_to_view(scene_pos)
        return float(point.y())
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def _create_grid_overlay(plot: object, pg: Any) -> object | None:
    try:
        grid_item = PyQtGraphMajorGridItem(pg=pg, pen=pg.mkPen(_color_with_alpha(pg, '#96A6A0', 0.82), width=1))
    except Exception: # pylint: disable=broad-exception-caught
        return None
    _call_if_available(grid_item, 'setZValue', -5)
    view_box = getattr(plot, 'getViewBox', lambda: None)()
    _call_if_available(view_box, 'addItem', grid_item)
    return grid_item


def _create_legend(plot: object, pg: Any) -> object | None:
    try:
        legend = plot.addLegend(
            offset=(-12, -12),
            labelTextColor='#5E6B6E',
            brush=pg.mkBrush(_color_with_alpha(pg, '#FCFBF7', 0.82)),
            pen=pg.mkPen(_color_with_alpha(pg, '#CAD5D0', 0.88), width=1),
        )
    except Exception: # pylint: disable=broad-exception-caught
        return None
    _call_if_available(legend, 'setZValue', 40)
    return legend


def _configure_grid_overlay(
        grid_item: object | None,
        pg: Any,
        *,
        x_visible: bool,
        y_visible: bool,
        x_tick_step: float,
        y_tick_step: float,
        grid_alpha: float,
        grid_width: int,
        grid_color: str,
        grid_line_style: str) -> None:
    if grid_item is None:
        return
    visible = x_visible or y_visible
    _call_if_available(grid_item, 'setVisible', visible)
    if not visible:
        return
    pen = pg.mkPen(
        _color_with_alpha(pg, _grid_display_color(grid_color), _visible_grid_alpha(grid_alpha)),
        width=max(1, grid_width),
        style=_qt_pen_style(grid_line_style),
    )
    _call_if_available(grid_item, 'setPen', pen)
    _call_if_available(grid_item, 'setLineStyle', grid_line_style)
    x_spacing = [float(x_tick_step)] if x_visible and x_tick_step > 0 else [None]
    y_spacing = [float(y_tick_step)] if y_visible and y_tick_step > 0 else [None]
    _call_if_available(grid_item, 'setTickSpacing', x=x_spacing, y=y_spacing)


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
    base_z_value = getattr(base_view_box, 'zValue', lambda: -100.0)()
    _call_if_available(view_box, 'setZValue', base_z_value + 200.0)

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


class PyQtGraphMajorGridItem:
    def __new__(cls, *, pg: Any, pen: object) -> object:
        class MajorGridItem(pg.GraphicsObject):  # type: ignore[misc]
            def __init__(self) -> None:
                super().__init__()
                self.opts: dict[str, object] = {'tickSpacing': ([None], [None])}
                self._pen = pen

            def setPen(self, new_pen: object) -> None:  # noqa: N802
                self._pen = new_pen
                self.update()

            def setLineStyle(self, line_style: str) -> None:  # noqa: N802
                self.opts['lineStyle'] = line_style
                self.update()

            def setTickSpacing(self, *, x: list[float | None], y: list[float | None]) -> None:  # noqa: N802
                self.opts['tickSpacing'] = (x, y)
                self.update()

            def boundingRect(self) -> object:  # noqa: N802
                from PyQt6.QtCore import QRectF

                x_range, y_range = _grid_view_range(self)
                if x_range is None or y_range is None:
                    return QRectF()
                return QRectF(
                    x_range[0],
                    y_range[0],
                    x_range[1] - x_range[0],
                    y_range[1] - y_range[0],
                )

            def paint(self, painter: object, _option: object, _widget: object | None = None) -> None:
                from PyQt6.QtCore import QPointF

                x_range, y_range = _grid_view_range(self)
                if x_range is None or y_range is None:
                    return
                set_pen = getattr(painter, 'setPen', None)
                draw_line = getattr(painter, 'drawLine', None)
                if not callable(set_pen) or not callable(draw_line):
                    return
                set_pen(self._pen)
                x_spacing, y_spacing = self.opts['tickSpacing']
                for x_value in _major_grid_values(x_range[0], x_range[1], _grid_spacing_value(x_spacing)):
                    draw_line(QPointF(x_value, y_range[0]), QPointF(x_value, y_range[1]))
                for y_value in _major_grid_values(y_range[0], y_range[1], _grid_spacing_value(y_spacing)):
                    draw_line(QPointF(x_range[0], y_value), QPointF(x_range[1], y_value))

        MajorGridItem.__name__ = 'PyQtGraphMajorGridItem'
        return MajorGridItem()


def _grid_view_range(grid_item: object) -> tuple[tuple[float, float] | None, tuple[float, float] | None]:
    view_box = getattr(grid_item, 'getViewBox', lambda: None)()
    view_range = getattr(view_box, 'viewRange', None)
    if not callable(view_range):
        return None, None
    ranges = view_range()
    if len(ranges) != 2 or len(ranges[0]) != 2 or len(ranges[1]) != 2:
        return None, None
    return (float(ranges[0][0]), float(ranges[0][1])), (float(ranges[1][0]), float(ranges[1][1]))


def _grid_spacing_value(spacing: object) -> float | None:
    if not isinstance(spacing, list) or not spacing:
        return None
    value = spacing[0]
    if value is None:
        return None
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None
    if numeric_value <= 0:
        return None
    return numeric_value


def _major_grid_values(minimum: float, maximum: float, spacing: float | None) -> tuple[float, ...]:
    if spacing is None or maximum < minimum:
        return ()
    first = math.ceil(minimum / spacing) * spacing
    values: list[float] = []
    value = first
    while value <= maximum:
        values.append(value)
        value += spacing
    return tuple(values)


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


def _qt_pen_style(line_style: str) -> object:
    from PyQt6.QtCore import Qt

    return {
        '-': Qt.PenStyle.SolidLine,
        '--': Qt.PenStyle.DashLine,
        ':': Qt.PenStyle.DotLine,
        '-.': Qt.PenStyle.DashDotLine,
    }.get(line_style, Qt.PenStyle.SolidLine)


def _visible_grid_alpha(grid_alpha: float) -> float:
    return min(1.0, max(0.78, grid_alpha * 3.2))


def _grid_display_color(color: str) -> str:
    normalized = color.strip().lstrip('#')
    if len(normalized) != 6:
        return color
    try:
        red = int(normalized[0:2], 16)
        green = int(normalized[2:4], 16)
        blue = int(normalized[4:6], 16)
    except ValueError:
        return color
    luminance = ((0.2126 * red) + (0.7152 * green) + (0.0722 * blue)) / 255
    if luminance > 0.72:
        return '#8FA09A'
    return color


def _color_with_alpha(pg: Any, color: str, opacity: float) -> object:
    qcolor = pg.mkColor(color)
    set_alpha = getattr(qcolor, 'setAlphaF', None)
    if callable(set_alpha):
        set_alpha(max(0.0, min(1.0, float(opacity))))
    return qcolor


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
