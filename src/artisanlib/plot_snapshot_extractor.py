from __future__ import annotations

from typing import Any

from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, RoastPlotSnapshot, YAxisName

_DEFAULT_COLORS = {
    'bt': '#4E7180',
    'et': '#B5644F',
    'deltabt': '#78905D',
    'deltaet': '#B98A4B',
}


def build_roast_plot_snapshot(source: object) -> RoastPlotSnapshot:
    curves = (
        _curve(source, name='BT', y_attr='temp2', color_key='bt', visible_attr='BTcurve'),
        _curve(source, name='ET', y_attr='temp1', color_key='et', visible_attr='ETcurve'),
        _curve(
            source,
            name='Delta BT',
            y_attr='delta2',
            color_key='deltabt',
            visible_attr='DeltaBTflag',
            y_axis='ror'),
        _curve(
            source,
            name='Delta ET',
            y_attr='delta1',
            color_key='deltaet',
            visible_attr='DeltaETflag',
            y_axis='ror'),
    )
    return RoastPlotSnapshot(
        curves=curves,
        time_axis=_time_axis(source),
        temperature_axis=_temperature_axis(source),
        ror_axis=_ror_axis(source),
    )


def _curve(
        source: object,
        *,
        name: str,
        y_attr: str,
        color_key: str,
        visible_attr: str,
        y_axis: YAxisName = 'temperature') -> CurveSnapshot:
    return CurveSnapshot.from_sequences(
        name=name,
        x=_sequence(source, 'timex'),
        y=_sequence(source, y_attr),
        color=_palette_color(source, color_key),
        visible=bool(getattr(source, visible_attr, False)),
        y_axis=y_axis,
    )


def _time_axis(source: object) -> AxisSnapshot:
    minimum, maximum = _axis_limits(getattr(source, 'ax', None), 'get_xlim', 0.0, 0.0)
    return AxisSnapshot(minimum=minimum, maximum=maximum, label='Time')


def _temperature_axis(source: object) -> AxisSnapshot:
    minimum, maximum = _axis_limits(getattr(source, 'ax', None), 'get_ylim', 0.0, 0.0)
    return AxisSnapshot(minimum=minimum, maximum=maximum, label='Temperature')


def _ror_axis(source: object) -> AxisSnapshot | None:
    axis = getattr(source, 'delta_ax', None)
    if axis is None:
        return None
    minimum, maximum = _axis_limits(axis, 'get_ylim', 0.0, 0.0)
    return AxisSnapshot(minimum=minimum, maximum=maximum, label='RoR')


def _axis_limits(axis: object, method_name: str, default_minimum: float, default_maximum: float) -> tuple[float, float]:
    method = getattr(axis, method_name, None)
    if method is None:
        return default_minimum, default_maximum
    minimum, maximum = method()
    return float(minimum), float(maximum)


def _palette_color(source: object, color_key: str) -> str:
    palette = getattr(source, 'palette', {})
    if isinstance(palette, dict):
        color = palette.get(color_key)
        if isinstance(color, str):
            return color
    return _DEFAULT_COLORS[color_key]


def _sequence(source: object, attr_name: str) -> list[Any]:
    value = getattr(source, attr_name, [])
    if isinstance(value, list):
        return value
    return list(value)
