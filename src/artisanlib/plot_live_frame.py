from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy

from artisanlib.plot_snapshot import YAxisName


@dataclass(frozen=True, slots=True)
class LiveCurveData:
    name: str
    x: tuple[float, ...]
    y: tuple[float | None, ...]
    y_axis: YAxisName = 'temperature'

    @classmethod
    def from_sequences(
            cls,
            *,
            name: str,
            x: Sequence[float],
            y: Sequence[float | None],
            y_axis: YAxisName = 'temperature') -> LiveCurveData:
        if len(x) != len(y):
            raise ValueError('x and y must have the same length')
        return cls(
            name=name,
            x=tuple(float(value) for value in x),
            y=tuple(None if value is None else float(value) for value in y),
            y_axis=y_axis,
        )


@dataclass(frozen=True, slots=True)
class LivePlotFrame:
    curves: tuple[LiveCurveData, ...]

    def curve_names(self) -> tuple[str, ...]:
        return tuple(curve.name for curve in self.curves)


def apply_matplotlib_live_curve_data(line: object | None, curve: LiveCurveData) -> bool:
    if line is None:
        return False
    set_data = getattr(line, 'set_data', None)
    if not callable(set_data):
        return False
    set_data(curve.x, numpy.array(curve.y))
    return True


def apply_matplotlib_live_frame(
        lines_by_name: Mapping[str, object | None],
        frame: LivePlotFrame) -> tuple[str, ...]:
    applied: list[str] = []
    for curve in frame.curves:
        if apply_matplotlib_live_curve_data(lines_by_name.get(curve.name), curve):
            applied.append(curve.name)
    return tuple(applied)


__all__ = [
    'LiveCurveData',
    'LivePlotFrame',
    'apply_matplotlib_live_curve_data',
    'apply_matplotlib_live_frame',
]
