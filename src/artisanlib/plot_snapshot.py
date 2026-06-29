from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

YAxisName = Literal['temperature', 'ror']


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
            fill_to_zero: bool = False) -> CurveSnapshot:
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
    'AxisSnapshot',
    'CurveSnapshot',
    'EventMarkerSnapshot',
    'LivePlotRenderer',
    'RendererViewState',
    'RoastPlotSnapshot',
    'YAxisName',
]
