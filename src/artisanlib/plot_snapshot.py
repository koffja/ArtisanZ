from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
from typing import Literal, Protocol

YAxisName = Literal['temperature', 'ror']
EventMarkerKind = Literal['main', 'special', 'background']
GuideOrientation = Literal['vertical', 'horizontal']
GuideKind = Literal['auc', 'bbp', 'charge_target', 'time', 'analysis', 'custom']
AreaFillKind = Literal['auc', 'custom']
AnalysisMaskKind = Literal['curve_fit', 'analysis']
StatisticsBackgroundKind = Literal['analysis', 'segment', 'summary']
ChargeAnnotationColor = Literal['gray', 'blue', 'green', 'red']
RoRFlickSeverity = Literal['soft', 'moderate', 'hard']


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
    source_index: int | None = None


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
    marker: str = 'o'
    marker_size: float = 7.0
    line_width: float = 1.0


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
    bar_visible: bool = True
    label_visible: bool = True
    delta_visible: bool = True


@dataclass(frozen=True, slots=True)
class AnalysisMaskSnapshot:
    """Analysis interval mask expressed in plot data coordinates."""
    curvefit_start: float
    curvefit_end: float
    analysis_start: float
    analysis_end: float
    color: str
    opacity: float = 0.2
    kind: AnalysisMaskKind = 'analysis'
    y_axis: YAxisName = 'temperature'
    z_value: float = 20.0
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class StatisticsBackgroundSnapshot:
    """A renderer-neutral analysis/statistics result text box."""
    text: str
    position: tuple[float, float]
    color: str
    text_color: str
    opacity: float = 1.0
    kind: StatisticsBackgroundKind = 'analysis'
    z_value: float = 30.0
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ChargeTargetAnnotationSnapshot:
    enabled: bool
    is_charged: bool
    target_temp: float
    target_ror: float
    charged_temp: float
    charged_ror: float
    title: str
    reason: str
    prediction_seconds: float | None
    color: ChargeAnnotationColor
    current_rwt: float
    target_rwt: float
    anchor_time: float
    anchor_temp: float
    x_limit: float
    y_limit_top: float


@dataclass(frozen=True, slots=True)
class RoRFlickAnnotationSnapshot:
    """A single RoR flick/crash event for pyqtgraph rendering."""
    enabled: bool
    start_time: float
    end_time: float
    peak_time: float
    peak_value: float
    event_type: Literal['flick', 'crash']
    severity: RoRFlickSeverity
    peak_magnitude: float
    in_development: bool


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
    toggle_key: str = ''

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
            opacity: float = 1.0,
            toggle_key: str = '') -> CurveSnapshot:
        if len(x) != len(y):
            raise ValueError('x and y must have the same length')
        return cls(
            name=name,
            x=tuple(float(value) for value in x),
            y=tuple(None if value is None else float(value) for value in y),
            color=color,
            toggle_key=toggle_key,
            visible=visible,
            y_axis=y_axis,
            line_style=line_style,
            line_width=line_width,
            fill_to_zero=fill_to_zero,
            opacity=max(0.0, min(1.0, float(opacity))),
        )


@dataclass(frozen=True, slots=True)
class ProjectionBandSnapshot:
    """A translucent forecast corridor around a temperature projection."""

    x: tuple[float, ...]
    lower: tuple[float | None, ...]
    upper: tuple[float | None, ...]
    color: str
    y_axis: YAxisName = 'temperature'
    opacity: float = 0.18
    label: str = ''

    @classmethod
    def from_sequences(
            cls,
            *,
            x: Sequence[float],
            lower: Sequence[float | None],
            upper: Sequence[float | None],
            color: str,
            y_axis: YAxisName = 'temperature',
            opacity: float = 0.18,
            label: str = '') -> ProjectionBandSnapshot:
        if len(x) != len(lower) or len(x) != len(upper):
            raise ValueError('x, lower, and upper must have the same length')
        return cls(
            x=tuple(float(value) for value in x),
            lower=tuple(None if value is None else float(value) for value in lower),
            upper=tuple(None if value is None else float(value) for value in upper),
            color=color,
            y_axis=y_axis,
            opacity=max(0.0, min(1.0, float(opacity))),
            label=label,
        )


def projection_band_for_curve(
        curve: CurveSnapshot,
        temperature_axis: AxisSnapshot,
        *,
        max_axis_fraction: float = 0.035,
        opacity: float = 0.18) -> ProjectionBandSnapshot | None:
    """Build a restrained forecast corridor for BT/ET projection curves.

    The corridor starts at the latest measured point and expands with forecast
    distance. It is a visual uncertainty cue, not a statistical confidence
    interval.
    """
    if curve.name not in {'BT projection', 'ET projection'} or curve.y_axis != 'temperature':
        return None
    if len(curve.x) < 2 or len(curve.x) != len(curve.y):
        return None
    finite_points = [
        (x_value, y_value)
        for x_value, y_value in zip(curve.x, curve.y, strict=True)
        if math.isfinite(x_value) and y_value is not None and math.isfinite(y_value)
    ]
    if len(finite_points) < 2:
        return None
    start_x = finite_points[0][0]
    end_x = finite_points[-1][0]
    if math.isclose(start_x, end_x):
        return None
    axis_span = max(abs(float(temperature_axis.maximum) - float(temperature_axis.minimum)), 1.0)
    max_half_width = max(axis_span * max(0.0, float(max_axis_fraction)), 1.5)
    max_half_width = min(max_half_width, 8.0)
    x_span = end_x - start_x
    lower: list[float | None] = []
    upper: list[float | None] = []
    for x_value, y_value in zip(curve.x, curve.y, strict=True):
        if y_value is None or not math.isfinite(y_value) or not math.isfinite(x_value):
            lower.append(None)
            upper.append(None)
            continue
        progress = max(0.0, min(1.0, (x_value - start_x) / x_span))
        half_width = max_half_width * progress ** 1.2
        lower.append(y_value - half_width)
        upper.append(y_value + half_width)
    return ProjectionBandSnapshot.from_sequences(
        x=curve.x,
        lower=lower,
        upper=upper,
        color=curve.color,
        y_axis=curve.y_axis,
        opacity=opacity,
        label=f'{curve.name} range',
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
    projection_bands: tuple[ProjectionBandSnapshot, ...] = ()
    events: tuple[EventMarkerSnapshot, ...] = ()
    event_values: tuple[EventValueSnapshot, ...] = ()
    phase_bands: tuple[PhaseBandSnapshot, ...] = ()
    time_ranges: tuple[TimeRangeSnapshot, ...] = ()
    phase_summaries: tuple[PhaseSummarySnapshot, ...] = ()
    guides: tuple[GuideLineSnapshot, ...] = ()
    areas: tuple[AreaFillSnapshot, ...] = ()
    analysis_masks: tuple[AnalysisMaskSnapshot, ...] = ()
    statistics_backgrounds: tuple[StatisticsBackgroundSnapshot, ...] = ()
    charge_target_annotations: tuple[ChargeTargetAnnotationSnapshot, ...] = ()
    rorflick_annotations: tuple[RoRFlickAnnotationSnapshot, ...] = ()

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
    'AnalysisMaskKind',
    'AnalysisMaskSnapshot',
    'AreaFillKind',
    'AreaFillSnapshot',
    'AxisSnapshot',
    'ChargeAnnotationColor',
    'ChargeTargetAnnotationSnapshot',
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
    'ProjectionBandSnapshot',
    'projection_band_for_curve',
    'RendererViewState',
    'RoastPlotSnapshot',
    'RoRFlickAnnotationSnapshot',
    'RoRFlickSeverity',
    'StatisticsBackgroundKind',
    'StatisticsBackgroundSnapshot',
    'TimeRangeSnapshot',
    'YAxisName',
]
