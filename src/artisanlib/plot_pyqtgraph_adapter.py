from __future__ import annotations

from collections.abc import Callable
import math
from typing import Any

from artisanlib.plot_snapshot import (
    AxisSnapshot,
    CurveSnapshot,
    EventMarkerSnapshot,
    PhaseBandSnapshot,
    RendererViewState,
    RoastPlotSnapshot,
)

EventItemFactory = Callable[[EventMarkerSnapshot, RoastPlotSnapshot], object | None]
PhaseItemFactory = Callable[[PhaseBandSnapshot, RoastPlotSnapshot], object | None]
CurvePenFactory = Callable[[CurveSnapshot], object]


class PyQtGraphSnapshotRenderer:
    def __init__(
            self,
            *,
            temperature_plot: object,
            ror_plot: object | None = None,
            event_line_factory: EventItemFactory | None = None,
            event_label_factory: EventItemFactory | None = None,
            phase_item_factory: PhaseItemFactory | None = None,
            pen_factory: CurvePenFactory | None = None) -> None:
        self._temperature_plot = temperature_plot
        self._ror_plot = ror_plot
        self._event_line_factory = event_line_factory or _default_event_line_factory
        self._event_label_factory = event_label_factory or _default_event_label_factory
        self._phase_item_factory = phase_item_factory or _default_phase_item_factory
        self._pen_factory = pen_factory or _default_pen_factory
        self._items: dict[str, object] = {}
        self._phase_items: list[object] = []
        self._event_items: list[object] = []
        self._last_view_state = RendererViewState(
            time_axis=AxisSnapshot(minimum=0.0, maximum=0.0, label='Time'),
            temperature_axis=AxisSnapshot(minimum=0.0, maximum=0.0, label='Temperature'),
        )

    def set_snapshot(self, snapshot: RoastPlotSnapshot) -> None:
        self._apply_phase_bands(snapshot)
        self._apply_curves(snapshot)
        self._apply_events(snapshot)
        self.reset_view(snapshot.export_view_state())

    def update_live_frame(self, snapshot: RoastPlotSnapshot) -> None:
        self._apply_curves(snapshot)

    def reset_view(self, view_state: RendererViewState) -> None:
        _set_plot_ranges(self._temperature_plot, view_state.time_axis, view_state.temperature_axis)
        if self._ror_plot is not None and view_state.ror_axis is not None:
            _set_plot_ranges(self._ror_plot, view_state.time_axis, view_state.ror_axis)
        self._last_view_state = view_state

    def export_view_state(self) -> RendererViewState:
        time_axis = _read_x_axis(self._temperature_plot, self._last_view_state.time_axis)
        temperature_axis = _read_y_axis(self._temperature_plot, self._last_view_state.temperature_axis)
        ror_axis = None
        if self._ror_plot is not None and self._last_view_state.ror_axis is not None:
            ror_axis = _read_y_axis(self._ror_plot, self._last_view_state.ror_axis)
        return RendererViewState(time_axis=time_axis, temperature_axis=temperature_axis, ror_axis=ror_axis)

    def item_for(self, curve_name: str) -> object | None:
        return self._items.get(curve_name)

    def event_item_count(self) -> int:
        return len(self._event_items)

    def phase_item_count(self) -> int:
        return len(self._phase_items)

    def _apply_curves(self, snapshot: RoastPlotSnapshot) -> None:
        active_names = {curve.name for curve in snapshot.curves}
        for curve in snapshot.curves:
            item = self._items.get(curve.name)
            if item is None:
                item = self._create_item(curve)
                self._items[curve.name] = item
            _call_if_available(item, 'setData', curve.x, _pyqtgraph_y_values(curve.y))
            _call_if_available(item, 'setPen', self._pen_factory(curve))
            _call_if_available(item, 'setVisible', curve.visible)
        for name, item in self._items.items():
            if name not in active_names:
                _call_if_available(item, 'setVisible', False)

    def _create_item(self, curve: CurveSnapshot) -> object:
        plot = self._plot_for_curve(curve)
        return plot.plot(curve.x, _pyqtgraph_y_values(curve.y), pen=self._pen_factory(curve), name=curve.name)

    def _plot_for_curve(self, curve: CurveSnapshot) -> Any:
        if curve.y_axis == 'ror' and self._ror_plot is not None:
            return self._ror_plot
        return self._temperature_plot

    def _apply_phase_bands(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_phase_items()
        for band in snapshot.phase_bands:
            item = self._phase_item_factory(band, snapshot)
            if item is None:
                continue
            _call_if_available(self._temperature_plot, 'addItem', item)
            self._phase_items.append(item)

    def _clear_phase_items(self) -> None:
        for item in self._phase_items:
            _call_if_available(self._temperature_plot, 'removeItem', item)
        self._phase_items.clear()

    def _apply_events(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_event_items()
        for event in snapshot.events:
            for item in self._create_event_items(event, snapshot):
                _call_if_available(self._temperature_plot, 'addItem', item)
                self._event_items.append(item)

    def _clear_event_items(self) -> None:
        for item in self._event_items:
            _call_if_available(self._temperature_plot, 'removeItem', item)
        self._event_items.clear()

    def _create_event_items(self, event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> list[object]:
        items: list[object] = []
        line_item = self._event_line_factory(event, snapshot)
        if line_item is not None:
            items.append(line_item)
        label_item = self._event_label_factory(event, snapshot)
        if label_item is not None:
            items.append(label_item)
        return items


def _pen_for_curve(curve: CurveSnapshot) -> dict[str, object]:
    return {
        'color': curve.color,
        'width': curve.line_width,
        'style': curve.line_style,
        'opacity': curve.opacity,
    }


def _pyqtgraph_y_values(values: tuple[float | None, ...]) -> tuple[float, ...]:
    return tuple(math.nan if value is None else value for value in values)


def _default_pen_factory(curve: CurveSnapshot) -> object:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return _pen_for_curve(curve)
    return pg.mkPen(color=_color_with_alpha(pg, curve.color, curve.opacity), width=curve.line_width, style=_qt_pen_style(curve.line_style))


def _qt_pen_style(line_style: str) -> object:
    from PyQt6.QtCore import Qt

    return {
        '-': Qt.PenStyle.SolidLine,
        '--': Qt.PenStyle.DashLine,
        ':': Qt.PenStyle.DotLine,
        '-.': Qt.PenStyle.DashDotLine,
    }.get(line_style, Qt.PenStyle.SolidLine)


def _set_plot_ranges(plot: object, time_axis: AxisSnapshot, value_axis: AxisSnapshot) -> None:
    _call_if_available(plot, 'disableAutoRange')
    _call_with_optional_padding(plot, 'setXRange', time_axis.minimum, time_axis.maximum)
    _call_with_optional_padding(plot, 'setYRange', value_axis.minimum, value_axis.maximum)


def _call_with_optional_padding(target: object, method_name: str, minimum: float, maximum: float) -> None:
    method = getattr(target, method_name, None)
    if not callable(method):
        return
    try:
        method(minimum, maximum, padding=0.0)
    except TypeError:
        method(minimum, maximum)


def _read_x_axis(plot: object, fallback: AxisSnapshot) -> AxisSnapshot:
    ranges = _view_range(plot)
    if ranges is None:
        return fallback
    return AxisSnapshot(minimum=float(ranges[0][0]), maximum=float(ranges[0][1]), label=fallback.label)


def _read_y_axis(plot: object, fallback: AxisSnapshot) -> AxisSnapshot:
    ranges = _view_range(plot)
    if ranges is None:
        return fallback
    return AxisSnapshot(minimum=float(ranges[1][0]), maximum=float(ranges[1][1]), label=fallback.label)


def _view_range(plot: object) -> list[list[float]] | None:
    view_range = getattr(plot, 'viewRange', None)
    if not callable(view_range):
        return None
    ranges = view_range()
    if len(ranges) != 2 or len(ranges[0]) != 2 or len(ranges[1]) != 2:
        return None
    return ranges


def _call_if_available(target: object, method_name: str, *args: object) -> None:
    method = getattr(target, method_name, None)
    if callable(method):
        method(*args)


def _default_event_line_factory(event: EventMarkerSnapshot, _: RoastPlotSnapshot) -> object | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    width = 2 if event.kind == 'main' else 1
    opacity = 0.65 if event.kind == 'main' else 0.45
    item = pg.InfiniteLine(
        pos=event.time,
        angle=90,
        pen=pg.mkPen(color=_color_with_alpha(pg, event.color, opacity), width=width),
        movable=False,
    )
    _call_if_available(item, 'setZValue', 20)
    return item


def _default_event_label_factory(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> object | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    text_color = '#FFFFFF' if event.kind in {'special', 'background'} else event.color
    fill_opacity = 0.78 if event.kind == 'special' else 0.28
    if event.kind == 'background':
        fill_opacity = 0.36
    item = pg.TextItem(
        text=event.label,
        color=text_color,
        anchor=(0.5, 1),
        fill=pg.mkBrush(_color_with_alpha(pg, event.color, fill_opacity)),
        border=pg.mkPen(color=_color_with_alpha(pg, event.color, 0.65), width=1),
    )
    item.setPos(event.time, _event_label_y_position(event, snapshot))
    _call_if_available(item, 'setZValue', 30)
    return item


def _default_phase_item_factory(band: PhaseBandSnapshot, _: RoastPlotSnapshot) -> object | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    try:
        item = pg.LinearRegionItem(
            values=(band.minimum, band.maximum),
            orientation='horizontal',
            movable=False,
            brush=pg.mkBrush(_color_with_alpha(pg, band.color, band.opacity)),
        )
    except TypeError:
        return None
    _call_if_available(item, 'setZValue', -20)
    for line in getattr(item, 'lines', []):
        _call_if_available(line, 'setPen', pg.mkPen(color=_color_with_alpha(pg, band.color, 0.0), width=0))
    return item


def _event_label_y_position(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> float:
    if event.y_position is not None:
        return event.y_position
    span = max(1.0, snapshot.temperature_axis.maximum - snapshot.temperature_axis.minimum)
    if event.kind == 'main':
        row = max(0, event.event_type - 100) % 3
        return snapshot.temperature_axis.maximum - span * (0.035 + row * 0.045)
    row = event.event_type % 4
    return snapshot.temperature_axis.maximum - span * (0.06 + row * 0.05)


def _color_with_alpha(pg: object, color: str, opacity: float) -> object:
    qcolor = pg.mkColor(color)
    set_alpha = getattr(qcolor, 'setAlphaF', None)
    if callable(set_alpha):
        set_alpha(max(0.0, min(1.0, float(opacity))))
    return qcolor


__all__ = ['PyQtGraphSnapshotRenderer']
