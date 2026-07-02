from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

YAxisName = Literal['temperature', 'ror']
EventMarkerKind = Literal['main', 'special', 'background']
GuideOrientation = Literal['vertical', 'horizontal']
GuideKind = Literal['auc', 'bbp', 'charge_target', 'time', 'custom']
AreaFillKind = Literal['auc', 'custom']


@dataclass(frozen=True, slots=True)
class AxisSnapshot:
    minimum: float
    maximum: float
    label: str = ''


@dataclass(frozen=True, slots=True)
class EventMarkerSnapshot:
    time: float
    label: str
    event_type: int
    color: str
    value: float | None = None
    temperature: float | None = None
    kind: EventMarkerKind = 'special'
    y_position: float | None = None


@dataclass(frozen=True, slots=True)
class EventValueSnapshot:
    time: float
    value: float
    event_type: int
    color: str
    label: str = ''
    kind: EventMarkerKind = 'special'
    baseline: float = 0.0
    opacity: float = 0.55


@dataclass(frozen=True, slots=True)
class GuideLineSnapshot:
    position: float
    label: str
    color: str
    orientation: GuideOrientation = 'vertical'
    y_axis: YAxisName = 'temperature'
    line_style: str = '--'
    line_width: float = 1.0
    opacity: float = 0.55
    kind: GuideKind = 'custom'


@dataclass(frozen=True, slots=True)
class PhaseBandSnapshot:
    minimum: float
    maximum: float
    color: str
    opacity: float = 0.15
    label: str = ''


@dataclass(frozen=True, slots=True)
class TimeRangeSnapshot:
    start: float
    end: float
    color: str
    opacity: float = 0.18
    label: str = ''
    kind: str = 'custom'


@dataclass(frozen=True, slots=True)
class PhaseSummarySnapshot:
    start: float
    end: float
    label: str
    duration_text: str
    percent_text: str
    delta_text: str
    color: str = '#C9D2D4'
    opacity: float = 0.38


@dataclass(frozen=True, slots=True)
class AreaFillSnapshot:
    x: tuple[float, ...]
    y: tuple[float | None, ...]
    baseline: float
    color: str
    label: str = ''
    y_axis: YAxisName = 'temperature'
    opacity: float = 0.25
    kind: AreaFillKind = 'custom'

    @classmethod
    def from_sequences(
            cls,
            *,
            x: Sequence[float],
            y: Sequence[float | None],
            baseline: float,
            color: str,
            label: str = '',
            y_axis: YAxisName = 'temperature',
            opacity: float = 0.25,
            kind: AreaFillKind = 'custom') -> AreaFillSnapshot:
        if len(x) != len(y):
            raise ValueError('x and y must have the same length')
        return cls(
            x=tuple(float(value) for value in x),
            y=tuple(None if value is None else float(value) for value in y),
            baseline=float(baseline),
            color=color,
            label=label,
            y_axis=y_axis,
            opacity=max(0.0, min(1.0, float(opacity))),
            kind=kind,
        )


@dataclass(frozen=True, slots=True)
class CurveSnapshot:
    name: str
    x: tuple[float, ...]
    y: tuple[float | None, ...]
    color: str
    visible: bool = True
    y_axis: YAxisName = 'temperature'
    line_style: str = '-'
    line_width: float = 1.0
    fill_to_zero: bool = False
    opacity: float = 1.0

    @classmethod
    def from_sequences(
            cls,
            *,
            name: str,
            x: Sequence[float],
            y: Sequence[float | None],
            color: str,
            visible: bool = True,
            y_axis: YAxisName = 'temperature',
            line_style: str = '-',
            line_width: float = 1.0,
            fill_to_zero: bool = False,
            opacity: float = 1.0) -> CurveSnapshot:
        if len(x) != len(y):
            raise ValueError('x and y must have the same length')
        return cls(
            name=name,
            x=tuple(float(value) for value in x),
            y=tuple(None if value is None else float(value) for value in y),
            color=color,
            visible=visible,
            y_axis=y_axis,
            line_style=line_style,
            line_width=line_width,
            fill_to_zero=fill_to_zero,
            opacity=max(0.0, min(1.0, float(opacity))),
        )


@dataclass(frozen=True, slots=True)
class RendererViewState:
    time_axis: AxisSnapshot
    temperature_axis: AxisSnapshot
    ror_axis: AxisSnapshot | None = None


@dataclass(frozen=True, slots=True)
class RoastPlotSnapshot:
    curves: tuple[CurveSnapshot, ...]
    temperature_axis: AxisSnapshot
    time_axis: AxisSnapshot
    ror_axis: AxisSnapshot | None = None
    events: tuple[EventMarkerSnapshot, ...] = ()
    event_values: tuple[EventValueSnapshot, ...] = ()
    phase_bands: tuple[PhaseBandSnapshot, ...] = ()
    time_ranges: tuple[TimeRangeSnapshot, ...] = ()
    phase_summaries: tuple[PhaseSummarySnapshot, ...] = ()
    guides: tuple[GuideLineSnapshot, ...] = ()
    areas: tuple[AreaFillSnapshot, ...] = ()

    def visible_curves(self) -> tuple[CurveSnapshot, ...]:
        return tuple(curve for curve in self.curves if curve.visible)

    def export_view_state(self) -> RendererViewState:
        return RendererViewState(
            time_axis=self.time_axis,
            temperature_axis=self.temperature_axis,
            ror_axis=self.ror_axis,
        )


class LivePlotRenderer(Protocol):
    def set_snapshot(self, snapshot: RoastPlotSnapshot) -> None:
        ...

    def update_live_frame(self, snapshot: RoastPlotSnapshot) -> None:
        ...

    def reset_view(self, view_state: RendererViewState) -> None:
        ...

    def export_view_state(self) -> RendererViewState:
        ...


__all__ = [
    'AreaFillKind',
    'AreaFillSnapshot',
    'AxisSnapshot',
    'CurveSnapshot',
    'EventMarkerKind',
    'EventMarkerSnapshot',
    'EventValueSnapshot',
    'GuideKind',
    'GuideLineSnapshot',
    'GuideOrientation',
    'LivePlotRenderer',
    'PhaseBandSnapshot',
    'PhaseSummarySnapshot',
    'RendererViewState',
    'RoastPlotSnapshot',
    'TimeRangeSnapshot',
    'YAxisName',
]
