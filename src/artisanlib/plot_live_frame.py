from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Literal

import numpy

from artisanlib.plot_snapshot import YAxisName
from artisanlib.plot_renderer_registry import RendererSurface
from artisanlib.plot_renderer_settings import DEFAULT_RENDERER_ID, RendererSelection

type LiveFrameFallbackReason = Literal['pyqtgraph_targets_unavailable']


@dataclass(frozen=True, slots=True)
class LiveAxisRange:
    minimum: float
    maximum: float

    @classmethod
    def from_values(cls, minimum: float, maximum: float) -> LiveAxisRange:
        minimum_value = float(minimum)
        maximum_value = float(maximum)
        if maximum_value < minimum_value:
            raise ValueError('maximum must be greater than or equal to minimum')
        return cls(minimum=minimum_value, maximum=maximum_value)


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


@dataclass(frozen=True, slots=True)
class LiveFrameApplyResult:
    requested_renderer_id: str
    renderer_id: str
    surface: RendererSurface
    applied_curves: tuple[str, ...]
    fallback_reason: LiveFrameFallbackReason | None = None

    @property
    def used_fallback(self) -> bool:
        return self.fallback_reason is not None


def apply_matplotlib_live_curve_data(line: object | None, curve: LiveCurveData) -> bool:
    if line is None:
        return False
    set_data = getattr(line, 'set_data', None)
    if not callable(set_data):
        return False
    set_data(curve.x, numpy.array(curve.y))
    return True


def apply_matplotlib_live_curve_sequences(
        line: object | None,
        *,
        name: str,
        x: Sequence[float],
        y: Sequence[float | None],
        y_axis: YAxisName = 'temperature') -> bool:
    if line is None:
        return False
    return apply_matplotlib_live_curve_data(
        line,
        LiveCurveData.from_sequences(name=name, x=x, y=y, y_axis=y_axis),
    )


def apply_matplotlib_live_frame(
        lines_by_name: Mapping[str, object | None],
        frame: LivePlotFrame) -> tuple[str, ...]:
    applied: list[str] = []
    for curve in frame.curves:
        if apply_matplotlib_live_curve_data(lines_by_name.get(curve.name), curve):
            applied.append(curve.name)
    return tuple(applied)


def apply_matplotlib_live_axis_range(axis: object | None, axis_range: LiveAxisRange) -> bool:
    if axis is None:
        return False
    set_xlim = getattr(axis, 'set_xlim', None)
    if not callable(set_xlim):
        return False
    set_xlim(axis_range.minimum, axis_range.maximum)
    return True


def apply_pyqtgraph_live_curve_data(item: object | None, curve: LiveCurveData) -> bool:
    if item is None:
        return False
    set_data = getattr(item, 'setData', None)
    if not callable(set_data):
        return False
    set_data(curve.x, _pyqtgraph_y_values(curve.y))
    return True


def apply_pyqtgraph_live_frame(
        items_by_name: Mapping[str, object | None],
        frame: LivePlotFrame) -> tuple[str, ...]:
    applied: list[str] = []
    for curve in frame.curves:
        if apply_pyqtgraph_live_curve_data(items_by_name.get(curve.name), curve):
            applied.append(curve.name)
    return tuple(applied)


def apply_selected_live_frame(
        selection: RendererSelection,
        frame: LivePlotFrame,
        *,
        matplotlib_lines: Mapping[str, object | None],
        pyqtgraph_items: Mapping[str, object | None] | None = None) -> LiveFrameApplyResult:
    if selection.plugin.surface == 'pyqtgraph-plot':
        if pyqtgraph_items:
            return LiveFrameApplyResult(
                requested_renderer_id=selection.requested_renderer_id,
                renderer_id=selection.renderer_id,
                surface='pyqtgraph-plot',
                applied_curves=apply_pyqtgraph_live_frame(pyqtgraph_items, frame),
            )
        return LiveFrameApplyResult(
            requested_renderer_id=selection.requested_renderer_id,
            renderer_id=DEFAULT_RENDERER_ID,
            surface='matplotlib-axis',
            applied_curves=apply_matplotlib_live_frame(matplotlib_lines, frame),
            fallback_reason='pyqtgraph_targets_unavailable',
        )
    return LiveFrameApplyResult(
        requested_renderer_id=selection.requested_renderer_id,
        renderer_id=selection.renderer_id,
        surface='matplotlib-axis',
        applied_curves=apply_matplotlib_live_frame(matplotlib_lines, frame),
    )


def _pyqtgraph_y_values(values: tuple[float | None, ...]) -> tuple[float, ...]:
    return tuple(math.nan if value is None else value for value in values)


__all__ = [
    'LiveAxisRange',
    'LiveCurveData',
    'LiveFrameApplyResult',
    'LiveFrameFallbackReason',
    'LivePlotFrame',
    'apply_matplotlib_live_axis_range',
    'apply_matplotlib_live_curve_data',
    'apply_matplotlib_live_curve_sequences',
    'apply_matplotlib_live_frame',
    'apply_pyqtgraph_live_curve_data',
    'apply_pyqtgraph_live_frame',
    'apply_selected_live_frame',
]
