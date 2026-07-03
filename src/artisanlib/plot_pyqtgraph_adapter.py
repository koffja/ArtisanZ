from __future__ import annotations

from collections.abc import Callable
import math
from typing import Any

from artisanlib.plot_snapshot import (
    AreaFillSnapshot,
    AxisSnapshot,
    CurveSnapshot,
    EventMarkerSnapshot,
    EventValueSnapshot,
    GuideLineSnapshot,
    PhaseBandSnapshot,
    PhaseSummarySnapshot,
    RendererViewState,
    RoastPlotSnapshot,
    TimeRangeSnapshot,
)

EventItemFactory = Callable[[EventMarkerSnapshot, RoastPlotSnapshot], object | tuple[object, ...] | None]
EventValueItemFactory = Callable[[EventValueSnapshot, RoastPlotSnapshot], object | None]
GuideItemFactory = Callable[[GuideLineSnapshot, RoastPlotSnapshot], object | None]
PhaseItemFactory = Callable[[PhaseBandSnapshot, RoastPlotSnapshot], object | None]
TimeRangeItemFactory = Callable[[TimeRangeSnapshot, RoastPlotSnapshot], object | tuple[object, ...] | None]
PhaseSummaryItemFactory = Callable[[PhaseSummarySnapshot, RoastPlotSnapshot], object | tuple[object, ...] | None]
AreaItemFactory = Callable[[AreaFillSnapshot, RoastPlotSnapshot], object | None]
CurvePenFactory = Callable[[CurveSnapshot], object]


class PyQtGraphSnapshotRenderer:
    def __init__(
            self,
            *,
            temperature_plot: object,
            ror_plot: object | None = None,
            legend_item: object | None = None,
            event_line_factory: EventItemFactory | None = None,
            event_label_factory: EventItemFactory | None = None,
            event_value_factory: EventValueItemFactory | None = None,
            guide_item_factory: GuideItemFactory | None = None,
            phase_item_factory: PhaseItemFactory | None = None,
            time_range_factory: TimeRangeItemFactory | None = None,
            phase_summary_factory: PhaseSummaryItemFactory | None = None,
            area_item_factory: AreaItemFactory | None = None,
            pen_factory: CurvePenFactory | None = None) -> None:
        self._temperature_plot = temperature_plot
        self._ror_plot = ror_plot
        self._legend_item = legend_item
        self._event_line_factory = event_line_factory or _default_event_line_factory
        self._event_label_factory = event_label_factory or _default_event_label_factory
        self._event_value_factory = event_value_factory or _default_event_value_factory
        self._guide_item_factory = guide_item_factory or _default_guide_item_factory
        self._phase_item_factory = phase_item_factory or _default_phase_item_factory
        self._time_range_factory = time_range_factory or _default_time_range_item_factory
        self._phase_summary_factory = phase_summary_factory or _default_phase_summary_item_factory
        self._area_item_factory = area_item_factory or _default_area_item_factory
        self._pen_factory = pen_factory or _default_pen_factory
        self._items: dict[str, object] = {}
        self._phase_items: list[object] = []
        self._time_range_items: list[object] = []
        self._phase_summary_items: list[object] = []
        self._area_items: list[tuple[object, object]] = []
        self._event_items: list[object] = []
        self._event_value_items: list[tuple[object, object]] = []
        self._guide_items: list[tuple[object, object]] = []
        self._static_overlay_signature: tuple[object, ...] | None = None
        self._last_view_state = RendererViewState(
            time_axis=AxisSnapshot(minimum=0.0, maximum=0.0, label='Time'),
            temperature_axis=AxisSnapshot(minimum=0.0, maximum=0.0, label='Temperature'),
        )

    def set_snapshot(self, snapshot: RoastPlotSnapshot) -> None:
        self._apply_static_overlays(snapshot, force=True)
        self._apply_curves(snapshot)
        self.reset_view(snapshot.export_view_state())

    def update_live_frame(self, snapshot: RoastPlotSnapshot) -> None:
        self._apply_static_overlays(snapshot, force=False)
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

    def time_range_item_count(self) -> int:
        return len(self._time_range_items)

    def phase_summary_item_count(self) -> int:
        return len(self._phase_summary_items)

    def event_value_item_count(self) -> int:
        return len(self._event_value_items)

    def guide_item_count(self) -> int:
        return len(self._guide_items)

    def area_item_count(self) -> int:
        return len(self._area_items)

    def _apply_static_overlays(self, snapshot: RoastPlotSnapshot, *, force: bool) -> None:
        signature = _static_overlay_signature(snapshot)
        if not force and signature == self._static_overlay_signature:
            return
        self._apply_phase_bands(snapshot)
        self._apply_time_ranges(snapshot)
        self._apply_phase_summaries(snapshot)
        self._apply_areas(snapshot)
        self._apply_event_values(snapshot)
        self._apply_events(snapshot)
        self._apply_guides(snapshot)
        self._static_overlay_signature = signature

    def _apply_curves(self, snapshot: RoastPlotSnapshot) -> None:
        active_names = {curve.name for curve in snapshot.curves}
        for curve in snapshot.curves:
            item = self._items.get(curve.name)
            if item is None:
                item = self._create_item(curve)
                self._items[curve.name] = item
            _call_if_available(item, 'setData', curve.x, _pyqtgraph_y_values(curve.y))
            pen = self._pen_factory(curve)
            _call_if_available(item, 'setPen', pen)
            self._apply_shadow_pen(item, pen)
            _call_if_available(item, 'setVisible', curve.visible)
        for name, item in self._items.items():
            if name not in active_names:
                _call_if_available(item, 'setVisible', False)
        self._apply_legend(snapshot)

    @staticmethod
    def _apply_shadow_pen(item: object, pen: object) -> None:
        """Apply a subtle black shadow pen behind each curve for visibility."""
        try:
            import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
            pen_width = 2
            width_fn = getattr(pen, 'width', None)
            if callable(width_fn):
                pen_width = max(2, int(width_fn()))
            shadow_width = max(pen_width + 2, int(pen_width * 2))
            shadow_pen = pg.mkPen(0, 0, 0, 80, width=shadow_width)
            _call_if_available(item, 'setShadowPen', shadow_pen)
        except Exception:
            pass

    def _apply_legend(self, snapshot: RoastPlotSnapshot) -> None:
        if self._legend_item is None:
            return
        clear = getattr(self._legend_item, 'clear', None)
        if callable(clear):
            clear()
        for curve in snapshot.curves:
            if not curve.visible or _legend_should_skip(curve):
                continue
            item = self._items.get(curve.name)
            if item is not None:
                _call_if_available(self._legend_item, 'addItem', item, _legend_label(curve.name))

    def _create_item(self, curve: CurveSnapshot) -> object:
        plot = self._plot_for_curve(curve)
        item = plot.plot(curve.x, _pyqtgraph_y_values(curve.y), pen=self._pen_factory(curve), name=curve.name)
        _call_if_available(item, 'setZValue', 45 if curve.y_axis == 'ror' else 10)
        return item

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

    def _apply_time_ranges(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_time_range_items()
        for time_range in snapshot.time_ranges:
            for item in _as_items(self._time_range_factory(time_range, snapshot)):
                _call_if_available(self._temperature_plot, 'addItem', item)
                self._time_range_items.append(item)

    def _clear_time_range_items(self) -> None:
        for item in self._time_range_items:
            _call_if_available(self._temperature_plot, 'removeItem', item)
        self._time_range_items.clear()

    def _apply_phase_summaries(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_phase_summary_items()
        for summary in snapshot.phase_summaries:
            for item in _as_items(self._phase_summary_factory(summary, snapshot)):
                _call_if_available(self._temperature_plot, 'addItem', item)
                self._phase_summary_items.append(item)

    def _clear_phase_summary_items(self) -> None:
        for item in self._phase_summary_items:
            _call_if_available(self._temperature_plot, 'removeItem', item)
        self._phase_summary_items.clear()

    def _apply_areas(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_area_items()
        for area in snapshot.areas:
            item = self._area_item_factory(area, snapshot)
            if item is None:
                continue
            plot = self._plot_for_area(area)
            _call_if_available(plot, 'addItem', item)
            self._area_items.append((plot, item))

    def _clear_area_items(self) -> None:
        _clear_item_pairs(self._area_items)

    def _plot_for_area(self, area: AreaFillSnapshot) -> object:
        if area.y_axis == 'ror' and self._ror_plot is not None:
            return self._ror_plot
        return self._temperature_plot

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
        items.extend(_as_items(self._event_line_factory(event, snapshot)))
        items.extend(_as_items(self._event_label_factory(event, snapshot)))
        return items

    def _apply_event_values(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_event_value_items()
        for event_value in snapshot.event_values:
            item = self._event_value_factory(event_value, snapshot)
            if item is None:
                continue
            _call_if_available(self._temperature_plot, 'addItem', item)
            self._event_value_items.append((self._temperature_plot, item))

    def _clear_event_value_items(self) -> None:
        _clear_item_pairs(self._event_value_items)

    def _apply_guides(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_guide_items()
        for guide in snapshot.guides:
            item = self._guide_item_factory(guide, snapshot)
            if item is None:
                continue
            plot = self._plot_for_guide(guide)
            _call_if_available(plot, 'addItem', item)
            self._guide_items.append((plot, item))

    def _clear_guide_items(self) -> None:
        _clear_item_pairs(self._guide_items)

    def _plot_for_guide(self, guide: GuideLineSnapshot) -> object:
        if guide.y_axis == 'ror' and self._ror_plot is not None:
            return self._ror_plot
        return self._temperature_plot


def _pen_for_curve(curve: CurveSnapshot) -> dict[str, object]:
    return {
        'color': curve.color,
        'width': curve.line_width,
        'style': curve.line_style,
        'opacity': curve.opacity,
    }


def _static_overlay_signature(snapshot: RoastPlotSnapshot) -> tuple[object, ...]:
    return (
        snapshot.time_axis,
        snapshot.temperature_axis,
        snapshot.ror_axis,
        snapshot.phase_bands,
        snapshot.time_ranges,
        snapshot.phase_summaries,
        snapshot.areas,
        snapshot.event_values,
        snapshot.events,
        snapshot.guides,
    )


def _pyqtgraph_y_values(values: tuple[float | None, ...]) -> tuple[float, ...]:
    return tuple(math.nan if value is None else value for value in values)


def _legend_should_skip(curve: CurveSnapshot) -> bool:
    return 'projection' in curve.name.lower() or curve.name.startswith('Background ')


def _legend_label(curve_name: str) -> str:
    return {
        'Delta BT': 'ΔBT',
        'Delta ET': 'ΔET',
        'Background BT': 'BT bg',
        'Background ET': 'ET bg',
        'Background Delta BT': 'ΔBT bg',
        'Background Delta ET': 'ΔET bg',
    }.get(curve_name, curve_name)


def _default_pen_factory(curve: CurveSnapshot) -> object:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return _pen_for_curve(curve)
    if curve.name == 'BT' and curve.y_axis == 'temperature':
        line_width = max(2.2, curve.line_width)
    elif curve.y_axis == 'ror':
        line_width = max(2.4, curve.line_width)
    else:
        line_width = curve.line_width
    # BT curve: try gradient pen for temperature-coded coloring
    if curve.name == 'BT' and curve.y_axis == 'temperature':
        try:
            cached = globals().get('_cached_bt_gradient_cm')
            if cached is None:
                cached = pg.colormap.get('CET-L17')
                cached.reverse()
                globals()['_cached_bt_gradient_cm'] = cached
            return cached.getPen(span=(150.0, 250.0), width=int(line_width), orientation='vertical')
        except Exception:
            pass
    return pg.mkPen(color=_color_with_alpha(pg, curve.color, curve.opacity), width=line_width, style=_qt_pen_style(curve.line_style))


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


def _clear_item_pairs(items: list[tuple[object, object]]) -> None:
    for plot, item in items:
        _call_if_available(plot, 'removeItem', item)
    items.clear()


def _as_items(factory_result: object | tuple[object, ...] | None) -> tuple[object, ...]:
    if factory_result is None:
        return ()
    if isinstance(factory_result, tuple):
        return factory_result
    return (factory_result,)


def _default_event_line_factory(
        event: EventMarkerSnapshot,
        snapshot: RoastPlotSnapshot) -> object | tuple[object, ...] | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    if event.kind == 'main' and event.temperature is not None:
        temperature_position, label_position = _main_event_annotation_positions(event, snapshot)
        point = pg.ScatterPlotItem(
            [event.time],
            [event.temperature],
            symbol='o',
            size=7,
            pen=pg.mkPen(color=_color_with_alpha(pg, event.color, 0.88), width=1.4),
            brush=pg.mkBrush(_color_with_alpha(pg, '#FCFBF7', 0.94)),
        )
        temperature_leader = pg.PlotDataItem(
            [event.time, temperature_position[0]],
            [event.temperature, temperature_position[1]],
            pen=pg.mkPen(color=_color_with_alpha(pg, event.color, 0.68), width=1.1),
        )
        label_leader = pg.PlotDataItem(
            [event.time, label_position[0]],
            [event.temperature, label_position[1]],
            pen=pg.mkPen(color=_color_with_alpha(pg, event.color, 0.55), width=1.0),
        )
        for item, z_value in ((temperature_leader, 24), (label_leader, 23), (point, 32)):
            _call_if_available(item, 'setZValue', z_value)
        return temperature_leader, label_leader, point
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


def _default_event_value_factory(event_value: EventValueSnapshot, snapshot: RoastPlotSnapshot) -> object | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    y_value = _event_value_y_position(event_value, snapshot)
    baseline = _clamp(event_value.baseline, snapshot.temperature_axis.minimum, snapshot.temperature_axis.maximum)
    item = pg.PlotDataItem(
        [event_value.time, event_value.time],
        [baseline, y_value],
        pen=pg.mkPen(color=_color_with_alpha(pg, event_value.color, event_value.opacity), width=4),
    )
    _call_if_available(item, 'setZValue', 18)
    return item


def _default_event_label_factory(
        event: EventMarkerSnapshot,
        snapshot: RoastPlotSnapshot) -> object | tuple[object, ...] | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    if event.kind == 'main' and event.temperature is not None:
        temperature_position, label_position = _main_event_annotation_positions(event, snapshot)
        anchor = _main_event_text_anchor(event, snapshot)
        temperature_label = pg.TextItem(
            text=f'{event.temperature:.1f}',
            color='#20272B',
            anchor=anchor,
        )
        temperature_label.setPos(*temperature_position)
        event_label = pg.TextItem(
            text=event.label,
            color='#20272B',
            anchor=anchor,
        )
        event_label.setPos(*label_position)
        for item in (temperature_label, event_label):
            _call_if_available(item, 'setZValue', 35)
        return temperature_label, event_label
    text_color = '#FFFFFF' if event.kind in {'special', 'background'} else event.color
    fill_opacity = 0.78 if event.kind == 'special' else 0.28
    if event.kind == 'background':
        fill_opacity = 0.36
    item = pg.TextItem(
        text=_event_label_text(event),
        color=text_color,
        anchor=_event_label_anchor(event, snapshot),
        fill=pg.mkBrush(_color_with_alpha(pg, event.color, fill_opacity)),
        border=pg.mkPen(color=_color_with_alpha(pg, event.color, 0.65), width=1),
    )
    item.setPos(event.time, _event_label_y_position(event, snapshot))
    _call_if_available(item, 'setZValue', 30)
    return item


def _event_label_text(event: EventMarkerSnapshot) -> str:
    if event.temperature is not None:
        return f'{event.temperature:.1f}\n{event.label}'
    if event.value is not None and event.kind != 'main':
        return f'{event.label}\n{event.value:.0f}'
    return event.label


def _main_event_annotation_positions(
        event: EventMarkerSnapshot,
        snapshot: RoastPlotSnapshot) -> tuple[tuple[float, float], tuple[float, float]]:
    event_temperature = event.temperature
    if event_temperature is None:
        y_position = _event_label_y_position(event, snapshot)
        return (event.time, y_position), (event.time, y_position)
    x_span = max(1.0, snapshot.time_axis.maximum - snapshot.time_axis.minimum)
    y_span = max(1.0, snapshot.temperature_axis.maximum - snapshot.temperature_axis.minimum)
    direction = _main_event_text_direction(event, snapshot)
    row = _event_label_row(event, snapshot)
    x_offset = direction * max(10.0, x_span * 0.025)
    y_offset = y_span * (0.07 + row * 0.025)
    temperature_y = _clamp(
        event_temperature + y_offset,
        snapshot.temperature_axis.minimum + y_span * 0.04,
        snapshot.temperature_axis.maximum - y_span * 0.035,
    )
    label_y = _clamp(
        event_temperature - (y_offset * 0.72),
        snapshot.temperature_axis.minimum + y_span * 0.035,
        snapshot.temperature_axis.maximum - y_span * 0.06,
    )
    x = _clamp(
        event.time + x_offset,
        snapshot.time_axis.minimum + x_span * 0.015,
        snapshot.time_axis.maximum - x_span * 0.015,
    )
    return (x, temperature_y), (x, label_y)


def _main_event_text_anchor(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> tuple[float, float]:
    return (0.0, 0.5) if _main_event_text_direction(event, snapshot) > 0 else (1.0, 0.5)


def _main_event_text_direction(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> float:
    midpoint = (snapshot.time_axis.minimum + snapshot.time_axis.maximum) / 2.0
    return -1.0 if event.time > midpoint else 1.0


def _default_area_item_factory(area: AreaFillSnapshot, _: RoastPlotSnapshot) -> object | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    item = pg.PlotDataItem(
        area.x,
        _pyqtgraph_y_values(area.y),
        pen=pg.mkPen(color=_color_with_alpha(pg, area.color, min(0.6, area.opacity + 0.15)), width=1),
        fillLevel=area.baseline,
        brush=pg.mkBrush(_color_with_alpha(pg, area.color, area.opacity)),
        name=area.label,
    )
    _call_if_available(item, 'setZValue', -15)
    return item


def _default_guide_item_factory(guide: GuideLineSnapshot, _: RoastPlotSnapshot) -> object | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    angle = 90 if guide.orientation == 'vertical' else 0
    item = pg.InfiniteLine(
        pos=guide.position,
        angle=angle,
        pen=pg.mkPen(
            color=_color_with_alpha(pg, guide.color, guide.opacity),
            width=guide.line_width,
            style=_qt_pen_style(guide.line_style)),
        movable=False,
    )
    _call_if_available(item, 'setZValue', 22)
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
            brush=pg.mkBrush(_color_with_alpha(pg, band.color, _visible_phase_band_opacity(band.opacity))),
        )
    except TypeError:
        return None
    _call_if_available(item, 'setZValue', -20)
    for line in getattr(item, 'lines', []):
        _call_if_available(line, 'setPen', pg.mkPen(color=_color_with_alpha(pg, band.color, 0.0), width=0))
    return item


def _default_time_range_item_factory(time_range: TimeRangeSnapshot, _: RoastPlotSnapshot) -> object | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    try:
        item = pg.LinearRegionItem(
            values=(time_range.start, time_range.end),
            orientation='vertical',
            movable=False,
            brush=pg.mkBrush(_color_with_alpha(pg, time_range.color, time_range.opacity)),
        )
    except TypeError:
        return None
    _call_if_available(item, 'setZValue', -17)
    for line in getattr(item, 'lines', []):
        _call_if_available(line, 'setPen', pg.mkPen(color=_color_with_alpha(pg, time_range.color, 0.0), width=0))
    return item


def _default_phase_summary_item_factory(
        summary: PhaseSummarySnapshot,
        snapshot: RoastPlotSnapshot) -> tuple[object, ...] | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None
    y_top = snapshot.temperature_axis.maximum
    span = max(1.0, snapshot.temperature_axis.maximum - snapshot.temperature_axis.minimum)
    y_bar = y_top - span * 0.07
    y_text = y_top - span * 0.035
    x_mid = (summary.start + summary.end) / 2.0
    bar = pg.PlotDataItem(
        [summary.start, summary.end],
        [y_bar, y_bar],
        pen=pg.mkPen(color=_color_with_alpha(pg, summary.color, min(0.72, summary.opacity + 0.18)), width=14),
    )
    _call_if_available(bar, 'setZValue', 12)
    label = pg.TextItem(
        text=f'{summary.duration_text}  {summary.percent_text}',
        color='#20272B',
        anchor=(0.5, 0.5),
    )
    label.setPos(x_mid, y_text)
    _call_if_available(label, 'setZValue', 34)
    delta = pg.TextItem(
        text=summary.delta_text,
        color='#20272B',
        anchor=(0.5, 0.5),
    )
    delta.setPos(x_mid, y_top - span * 0.105)
    _call_if_available(delta, 'setZValue', 34)
    return bar, label, delta


def _visible_phase_band_opacity(opacity: float) -> float:
    return min(0.38, max(0.24, float(opacity) * 1.5))


def _event_label_y_position(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> float:
    if event.y_position is not None:
        return event.y_position
    span = max(1.0, snapshot.temperature_axis.maximum - snapshot.temperature_axis.minimum)
    if event.temperature is not None:
        return _clamp(event.temperature + span * 0.075, snapshot.temperature_axis.minimum, snapshot.temperature_axis.maximum - span * 0.04)
    row = _event_label_row(event, snapshot)
    if event.kind == 'main':
        return snapshot.temperature_axis.maximum - span * (0.035 + row * 0.045)
    return snapshot.temperature_axis.maximum - span * (0.06 + row * 0.05)


def _event_label_anchor(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> tuple[float, float]:
    span = max(1.0, snapshot.time_axis.maximum - snapshot.time_axis.minimum)
    edge_margin = span * 0.035
    if event.time <= snapshot.time_axis.minimum + edge_margin:
        return (0.0, 1.0)
    if event.time >= snapshot.time_axis.maximum - edge_margin:
        return (1.0, 1.0)
    return (0.5, 1.0)


def _event_label_row(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> int:
    events = list(snapshot.events)
    if not events:
        return 0
    target_index = _event_index(event, events)
    ordered_events = sorted(enumerate(events), key=lambda item: (item[1].time, item[0]))
    row_by_index: dict[int, int] = {}
    threshold = _event_cluster_threshold(snapshot)
    for original_index, candidate in ordered_events:
        occupied_rows = {
            row
            for other_index, row in row_by_index.items()
            if abs(candidate.time - events[other_index].time) <= threshold
        }
        row = 0
        while row in occupied_rows:
            row += 1
        row_by_index[original_index] = row
        if original_index == target_index:
            return row
    return 0


def _event_index(event: EventMarkerSnapshot, events: list[EventMarkerSnapshot]) -> int:
    for index, candidate in enumerate(events):
        if candidate is event:
            return index
    for index, candidate in enumerate(events):
        if candidate == event:
            return index
    return 0


def _event_cluster_threshold(snapshot: RoastPlotSnapshot) -> float:
    span = max(1.0, snapshot.time_axis.maximum - snapshot.time_axis.minimum)
    return max(6.0, min(45.0, span * 0.045))


def _event_value_y_position(event_value: EventValueSnapshot, snapshot: RoastPlotSnapshot) -> float:
    minimum = snapshot.temperature_axis.minimum
    maximum = snapshot.temperature_axis.maximum
    if minimum <= event_value.value <= maximum:
        return event_value.value
    span = max(1.0, maximum - minimum)
    if 0.0 <= event_value.value <= 100.0:
        return minimum + span * (event_value.value / 100.0)
    return _clamp(event_value.value, minimum, maximum)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _color_with_alpha(pg: object, color: str, opacity: float) -> object:
    qcolor = pg.mkColor(color)
    set_alpha = getattr(qcolor, 'setAlphaF', None)
    if callable(set_alpha):
        set_alpha(max(0.0, min(1.0, float(opacity))))
    return qcolor


__all__ = ['PyQtGraphSnapshotRenderer']
