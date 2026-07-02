from __future__ import annotations

from typing import Any

from artisanlib.plot_snapshot import (
    AreaFillSnapshot,
    AxisSnapshot,
    CurveSnapshot,
    EventMarkerSnapshot,
    EventValueSnapshot,
    GuideLineSnapshot,
    PhaseBandSnapshot,
    RendererViewState,
    RoastPlotSnapshot,
)


class MatplotlibSnapshotRenderer:
    def __init__(self, *, temperature_axis: object, ror_axis: object | None = None, draw_idle: bool = True) -> None:
        self._temperature_axis = temperature_axis
        self._ror_axis = ror_axis
        self._draw_idle = draw_idle
        self._lines: dict[str, object] = {}
        self._phase_artists: list[object] = []
        self._area_artists: list[object] = []
        self._event_artists: list[object] = []
        self._event_value_artists: list[object] = []
        self._guide_artists: list[object] = []
        self._last_view_state = RendererViewState(
            time_axis=AxisSnapshot(minimum=0.0, maximum=0.0, label='Time'),
            temperature_axis=AxisSnapshot(minimum=0.0, maximum=0.0, label='Temperature'),
        )

    def set_snapshot(self, snapshot: RoastPlotSnapshot) -> None:
        self._apply_phase_bands(snapshot)
        self._apply_areas(snapshot)
        self._apply_curves(snapshot)
        self._apply_event_values(snapshot)
        self._apply_events(snapshot)
        self._apply_guides(snapshot)
        self.reset_view(snapshot.export_view_state())
        self._request_draw_idle()

    def update_live_frame(self, snapshot: RoastPlotSnapshot) -> None:
        self._apply_curves(snapshot)
        self._request_draw_idle()

    def reset_view(self, view_state: RendererViewState) -> None:
        self._set_axis_limits(self._temperature_axis, view_state.time_axis, view_state.temperature_axis)
        if self._ror_axis is not None and view_state.ror_axis is not None:
            self._set_axis_limits(self._ror_axis, view_state.time_axis, view_state.ror_axis)
        self._last_view_state = view_state

    def export_view_state(self) -> RendererViewState:
        time_axis = _read_axis(self._temperature_axis, 'get_xlim', self._last_view_state.time_axis.label)
        temperature_axis = _read_axis(
            self._temperature_axis,
            'get_ylim',
            self._last_view_state.temperature_axis.label,
        )
        ror_axis = None
        if self._ror_axis is not None and self._last_view_state.ror_axis is not None:
            ror_axis = _read_axis(self._ror_axis, 'get_ylim', self._last_view_state.ror_axis.label)
        return RendererViewState(time_axis=time_axis, temperature_axis=temperature_axis, ror_axis=ror_axis)

    def line_for(self, curve_name: str) -> object | None:
        return self._lines.get(curve_name)

    def event_artist_count(self) -> int:
        return len(self._event_artists)

    def phase_artist_count(self) -> int:
        return len(self._phase_artists)

    def area_artist_count(self) -> int:
        return len(self._area_artists)

    def event_value_artist_count(self) -> int:
        return len(self._event_value_artists)

    def guide_artist_count(self) -> int:
        return len(self._guide_artists)

    def _apply_curves(self, snapshot: RoastPlotSnapshot) -> None:
        active_names = {curve.name for curve in snapshot.curves}
        for curve in snapshot.curves:
            line = self._lines.get(curve.name)
            if line is None:
                line = self._create_line(curve)
                self._lines[curve.name] = line
            _call_if_available(line, 'set_data', curve.x, curve.y)
            _call_if_available(line, 'set_color', curve.color)
            _call_if_available(line, 'set_linestyle', curve.line_style)
            _call_if_available(line, 'set_linewidth', curve.line_width)
            _call_if_available(line, 'set_alpha', curve.opacity)
            _call_if_available(line, 'set_visible', curve.visible)
        for name, line in self._lines.items():
            if name not in active_names:
                _call_if_available(line, 'set_visible', False)

    def _apply_phase_bands(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_phase_artists()
        for band in snapshot.phase_bands:
            artist = self._create_phase_artist(band)
            if artist is not None:
                self._phase_artists.append(artist)

    def _clear_phase_artists(self) -> None:
        _clear_artists(self._phase_artists)

    def _create_phase_artist(self, band: PhaseBandSnapshot) -> object | None:
        axhspan = getattr(self._temperature_axis, 'axhspan', None)
        if not callable(axhspan):
            return None
        return axhspan(
            band.minimum,
            band.maximum,
            facecolor=band.color,
            alpha=band.opacity,
            linewidth=0,
            zorder=-20,
        )

    def _apply_areas(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_area_artists()
        for area in snapshot.areas:
            artist = self._create_area_artist(area)
            if artist is not None:
                self._area_artists.append(artist)

    def _clear_area_artists(self) -> None:
        _clear_artists(self._area_artists)

    def _create_area_artist(self, area: AreaFillSnapshot) -> object | None:
        axis = self._axis_for_area(area)
        fill_between = getattr(axis, 'fill_between', None)
        if not callable(fill_between):
            return None
        return fill_between(
            area.x,
            area.baseline,
            _matplotlib_y_values(area.y),
            color=area.color,
            alpha=area.opacity,
            linewidth=0,
            zorder=-15,
        )

    def _apply_events(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_event_artists()
        for event in snapshot.events:
            self._event_artists.extend(self._create_event_artists(event, snapshot))

    def _clear_event_artists(self) -> None:
        _clear_artists(self._event_artists)

    def _create_event_artists(self, event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> list[object]:
        artists: list[object] = []
        axvline = getattr(self._temperature_axis, 'axvline', None)
        if callable(axvline):
            artists.append(axvline(
                event.time,
                color=event.color,
                linestyle=':',
                linewidth=0.9,
                alpha=0.75,
            ))
        annotate = getattr(self._temperature_axis, 'annotate', None)
        if callable(annotate):
            y_position = snapshot.temperature_axis.maximum
            artists.append(annotate(
                event.label,
                xy=(event.time, y_position),
                xytext=(event.time, y_position),
                color=event.color,
                ha='left',
                va='top',
                fontsize='x-small',
            ))
        return artists

    def _apply_event_values(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_event_value_artists()
        for event_value in snapshot.event_values:
            artist = self._create_event_value_artist(event_value, snapshot)
            if artist is not None:
                self._event_value_artists.append(artist)

    def _clear_event_value_artists(self) -> None:
        _clear_artists(self._event_value_artists)

    def _create_event_value_artist(
            self,
            event_value: EventValueSnapshot,
            snapshot: RoastPlotSnapshot) -> object | None:
        plot = getattr(self._temperature_axis, 'plot', None)
        if not callable(plot):
            return None
        y_value = _event_value_y_position(event_value, snapshot)
        baseline = _clamp(event_value.baseline, snapshot.temperature_axis.minimum, snapshot.temperature_axis.maximum)
        plotted = plot(
            [event_value.time, event_value.time],
            [baseline, y_value],
            color=event_value.color,
            linewidth=4,
            alpha=event_value.opacity,
            zorder=18,
        )
        if isinstance(plotted, (list, tuple)):
            return plotted[0]
        return plotted

    def _apply_guides(self, snapshot: RoastPlotSnapshot) -> None:
        self._clear_guide_artists()
        for guide in snapshot.guides:
            artist = self._create_guide_artist(guide)
            if artist is not None:
                self._guide_artists.append(artist)

    def _clear_guide_artists(self) -> None:
        _clear_artists(self._guide_artists)

    def _create_guide_artist(self, guide: GuideLineSnapshot) -> object | None:
        axis = self._axis_for_guide(guide)
        method_name = 'axvline' if guide.orientation == 'vertical' else 'axhline'
        method = getattr(axis, method_name, None)
        if not callable(method):
            return None
        return method(
            guide.position,
            color=guide.color,
            linestyle=guide.line_style,
            linewidth=guide.line_width,
            alpha=guide.opacity,
            zorder=22,
        )

    def _create_line(self, curve: CurveSnapshot) -> object:
        axis = self._axis_for_curve(curve)
        plotted = axis.plot(
            curve.x,
            curve.y,
            label=curve.name,
            color=curve.color,
            linestyle=curve.line_style,
            linewidth=curve.line_width,
        )
        if isinstance(plotted, (list, tuple)):
            return plotted[0]
        return plotted

    def _axis_for_curve(self, curve: CurveSnapshot) -> Any:
        if curve.y_axis == 'ror' and self._ror_axis is not None:
            return self._ror_axis
        return self._temperature_axis

    def _axis_for_area(self, area: AreaFillSnapshot) -> Any:
        if area.y_axis == 'ror' and self._ror_axis is not None:
            return self._ror_axis
        return self._temperature_axis

    def _axis_for_guide(self, guide: GuideLineSnapshot) -> Any:
        if guide.y_axis == 'ror' and self._ror_axis is not None:
            return self._ror_axis
        return self._temperature_axis

    def _set_axis_limits(self, axis: object, time_axis: AxisSnapshot, value_axis: AxisSnapshot) -> None:
        _call_if_available(axis, 'set_xlim', time_axis.minimum, time_axis.maximum)
        _call_if_available(axis, 'set_ylim', value_axis.minimum, value_axis.maximum)

    def _request_draw_idle(self) -> None:
        if not self._draw_idle:
            return
        for axis in (self._temperature_axis, self._ror_axis):
            if axis is None:
                continue
            figure = getattr(axis, 'figure', None)
            if figure is None:
                get_figure = getattr(axis, 'get_figure', None)
                if callable(get_figure):
                    figure = get_figure()
            canvas = getattr(figure, 'canvas', None)
            draw_idle = getattr(canvas, 'draw_idle', None)
            if callable(draw_idle):
                draw_idle()
                return


def _read_axis(axis: object, method_name: str, label: str) -> AxisSnapshot:
    method = getattr(axis, method_name)
    minimum, maximum = method()
    return AxisSnapshot(minimum=float(minimum), maximum=float(maximum), label=label)


def _matplotlib_y_values(values: tuple[float | None, ...]) -> tuple[float, ...]:
    return tuple(float('nan') if value is None else value for value in values)


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


def _clear_artists(artists: list[object]) -> None:
    for artist in artists:
        _call_if_available(artist, 'remove')
    artists.clear()


def _call_if_available(target: object, method_name: str, *args: object) -> None:
    method = getattr(target, method_name, None)
    if callable(method):
        method(*args)


__all__ = ['MatplotlibSnapshotRenderer']
