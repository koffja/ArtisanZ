from __future__ import annotations

import math
from typing import Any

try:
    from PyQt6.QtCore import QSettings
    from PyQt6.QtWidgets import QApplication
except ImportError:  # pragma: no cover - PyQt6 is a runtime dependency in normal builds
    QApplication = None  # type: ignore[assignment]
    QSettings = None  # type: ignore[assignment]

from artisanlib.plot_snapshot import (
    AreaFillSnapshot,
    AxisSnapshot,
    ChargeTargetAnnotationSnapshot,
    CurveSnapshot,
    EventMarkerSnapshot,
    EventValueSnapshot,
    GuideLineSnapshot,
    PhaseBandSnapshot,
    PhaseSummarySnapshot,
    RoastPlotSnapshot,
    TimeRangeSnapshot,
    YAxisName,
)

_DEFAULT_COLORS = {
    'bt': '#4E7180',
    'et': '#B5644F',
    'deltabt': '#78905D',
    'deltaet': '#B98A4B',
    'backgroundbt': '#4E7180',
    'backgroundet': '#B5644F',
    'backgrounddeltabt': '#78905D',
    'backgrounddeltaet': '#B98A4B',
    'aucarea': '#767676',
    'grid': '#C9D2D4',
    'markers': '#5E6B6E',
    'rect1': '#E5E5E5',
    'rect2': '#B2B2B2',
    'rect3': '#E5E5E5',
    'specialeventtext': '#FFFFFF',
    'bgeventtext': '#5E6B6E',
}

_MAIN_EVENTS = (
    (0, 'CHARGE'),
    (1, 'DRY'),
    (2, 'FCs'),
    (3, 'FCe'),
    (4, 'SCs'),
    (5, 'SCe'),
    (6, 'DROP'),
    (7, 'COOL'),
)


def _settings_value(keys: tuple[str, ...], default: object) -> object:
    if QSettings is None:
        return default
    settings = QSettings()
    for key in keys:
        if settings.contains(key):
            return settings.value(key)
    return default


def _settings_float(keys: tuple[str, ...], default: float) -> float:
    try:
        return float(_settings_value(keys, default))
    except (TypeError, ValueError):
        return default


def _settings_bool(keys: tuple[str, ...], default: bool) -> bool:
    value = _settings_value(keys, default)
    if isinstance(value, str):
        return value.lower() in {'1', 'true', 'yes'}
    return bool(value)


def _background_line_style() -> str:
    return str(_settings_value(('backgroundLineStyle', 'background_line_style'), '--'))


def build_roast_plot_snapshot(source: object) -> RoastPlotSnapshot:
    events = _event_markers(source)
    curves = (
        _curve(source, name='BT', y_attr='temp2', color_key='bt', visible_attr='BTcurve'),
        _curve(source, name='ET', y_attr='temp1', color_key='et', visible_attr='ETcurve'),
        _delta_curve(
            source,
            name='Delta BT',
            y_attr='delta2',
            color_key='deltabt',
            visible_attr='DeltaBTflag',
        ),
        _delta_curve(
            source,
            name='Delta ET',
            y_attr='delta1',
            color_key='deltaet',
            visible_attr='DeltaETflag',
        ),
    ) + _background_curves(source) + _projection_curves(source)
    time_axis = _time_axis(source)
    temperature_axis = _temperature_axis(source)
    return RoastPlotSnapshot(
        curves=curves,
        time_axis=time_axis,
        temperature_axis=temperature_axis,
        ror_axis=_ror_axis(source, curves),
        events=events,
        event_values=_event_value_snapshots(events),
        phase_bands=_phase_bands(source),
        time_ranges=_time_ranges(source),
        phase_summaries=_phase_summaries(source),
        guides=_guide_lines(source),
        charge_target_annotations=_charge_target_annotations(
            source,
            time_axis=time_axis,
            temperature_axis=temperature_axis,
        ),
        areas=_area_fills(source),
    )


def build_roast_plot_static_overlay_snapshot(
        source: object,
        *,
        time_axis: AxisSnapshot,
        temperature_axis: AxisSnapshot,
        ror_axis: AxisSnapshot | None = None) -> RoastPlotSnapshot:
    events = _event_markers(source)
    return RoastPlotSnapshot(
        curves=(),
        time_axis=time_axis,
        temperature_axis=temperature_axis,
        ror_axis=ror_axis,
        events=events,
        event_values=_event_value_snapshots(events),
        phase_bands=_phase_bands(source),
        time_ranges=_time_ranges(source),
        phase_summaries=_phase_summaries(source),
        guides=_guide_lines(source),
        charge_target_annotations=_charge_target_annotations(
            source,
            time_axis=time_axis,
            temperature_axis=temperature_axis,
        ),
        areas=_area_fills(source),
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
        line_style=_line_style(source, _line_style_attr(name), '-'),
        line_width=_line_width(source, _line_width_attr(name), 1.0),
    )


def _delta_curve(
        source: object,
        *,
        name: str,
        y_attr: str,
        color_key: str,
        visible_attr: str) -> CurveSnapshot:
    return CurveSnapshot.from_sequences(
        name=name,
        x=_sequence(source, 'timex'),
        y=_foreground_delta_values(source, _sequence(source, y_attr)),
        color=_palette_color(source, color_key),
        visible=bool(getattr(source, visible_attr, False)),
        y_axis='ror',
        line_style=_line_style(source, _line_style_attr(name), '-'),
        line_width=_line_width(source, _line_width_attr(name), 1.0),
    )


def _background_curves(source: object) -> tuple[CurveSnapshot, ...]:
    if not _background_available(source):
        return ()
    background_line_style = _background_line_style()
    return tuple(curve for curve in (
        _background_curve(
            source,
            name='Background BT',
            y_attr='temp2B',
            smoothed_y_attr='stemp2B',
            color_attr='backgroundbtcolor',
            color_key='backgroundbt',
            visible_attr='backgroundBTcurve',
            line_style=background_line_style,
            line_width_attr='BTbacklinewidth'),
        _background_curve(
            source,
            name='Background ET',
            y_attr='temp1B',
            smoothed_y_attr='stemp1B',
            color_attr='backgroundmetcolor',
            color_key='backgroundet',
            visible_attr='backgroundETcurve',
            line_style=background_line_style,
            line_width_attr='ETbacklinewidth'),
        _curve_from_xy(
            source,
            name='Background Delta BT',
            x=_sequence(source, 'timeB'),
            y=_sequence(source, 'delta2B'),
            color=_color_attr(source, 'backgrounddeltabtcolor', 'backgrounddeltabt'),
            visible=bool(getattr(source, 'DeltaBTBflag', False)),
            y_axis='ror',
            line_style=background_line_style,
            line_width=_line_width(source, 'BTBdeltalinewidth', 1.0),
            opacity=_opacity(source, 'backgroundalpha', 0.35)),
        _curve_from_xy(
            source,
            name='Background Delta ET',
            x=_sequence(source, 'timeB'),
            y=_sequence(source, 'delta1B'),
            color=_color_attr(source, 'backgrounddeltaetcolor', 'backgrounddeltaet'),
            visible=bool(getattr(source, 'DeltaETBflag', False)),
            y_axis='ror',
            line_style=background_line_style,
            line_width=_line_width(source, 'ETBdeltalinewidth', 1.0),
            opacity=_opacity(source, 'backgroundalpha', 0.35)),
    ) if curve is not None)


def _background_curve(
        source: object,
        *,
        name: str,
        y_attr: str,
        smoothed_y_attr: str,
        color_attr: str,
        color_key: str,
        visible_attr: str,
        line_style: str,
        line_width_attr: str) -> CurveSnapshot | None:
    y_source = y_attr if bool(getattr(source, 'flagon', False)) else smoothed_y_attr
    y_values = _background_temperature_values(source, _sequence(source, y_source))
    return _curve_from_xy(
        source,
        name=name,
        x=_sequence(source, 'timeB'),
        y=y_values,
        color=_color_attr(source, color_attr, color_key),
        visible=bool(getattr(source, visible_attr, False)),
        line_style=line_style,
        line_width=_line_width(source, line_width_attr, 1.0),
        opacity=_opacity(source, 'backgroundalpha', 0.35),
    )


def _projection_curves(source: object) -> tuple[CurveSnapshot, ...]:
    return tuple(curve for curve in (
        _projection_curve(
            source,
            name='BT projection',
            x_attr='BTprojection_tx',
            y_attr='BTprojection_temp',
            color_key='bt',
            visible=bool(getattr(source, 'BTprojectFlag', False) and getattr(source, 'BTcurve', False))),
        _projection_curve(
            source,
            name='ET projection',
            x_attr='ETprojection_tx',
            y_attr='ETprojection_temp',
            color_key='et',
            visible=bool(getattr(source, 'ETprojectFlag', False) and getattr(source, 'ETcurve', False))),
        _projection_curve(
            source,
            name='Delta BT projection',
            x_attr='DeltaBTprojection_tx',
            y_attr='DeltaBTprojection_temp',
            color_key='deltabt',
            visible=bool(
                getattr(source, 'BTprojectFlag', False) and
                getattr(source, 'projectDeltaFlag', False) and
                getattr(source, 'DeltaBTflag', False)),
            y_axis='ror'),
        _projection_curve(
            source,
            name='Delta ET projection',
            x_attr='DeltaETprojection_tx',
            y_attr='DeltaETprojection_temp',
            color_key='deltaet',
            visible=bool(
                getattr(source, 'ETprojectFlag', False) and
                getattr(source, 'projectDeltaFlag', False) and
                getattr(source, 'DeltaETflag', False)),
            y_axis='ror'),
    ) if curve is not None)


def _projection_curve(
        source: object,
        *,
        name: str,
        x_attr: str,
        y_attr: str,
        color_key: str,
        visible: bool,
        y_axis: YAxisName = 'temperature') -> CurveSnapshot | None:
    x = _sequence(source, x_attr)
    y = _sequence(source, y_attr)
    if not visible or not x or not y:
        return None
    return _curve_from_xy(
        source,
        name=name,
        x=x,
        y=y,
        color=_palette_color(source, color_key),
        visible=visible,
        y_axis=y_axis,
        line_style='-.',
        line_width=4.0,
        opacity=0.35,
    )


def _curve_from_xy(
        source: object,
        *,
        name: str,
        x: list[Any],
        y: list[Any],
        color: str,
        visible: bool,
        y_axis: YAxisName = 'temperature',
        line_style: str = '-',
        line_width: float = 1.0,
        opacity: float = 1.0) -> CurveSnapshot | None:
    limit = min(len(x), len(y))
    if limit == 0:
        return CurveSnapshot.from_sequences(
            name=name,
            x=(),
            y=(),
            color=color,
            visible=False,
            y_axis=y_axis,
            line_style=line_style,
            line_width=line_width,
            opacity=opacity,
        )
    del source
    return CurveSnapshot.from_sequences(
        name=name,
        x=x[:limit],
        y=[_temperature_value(value) for value in y[:limit]],
        color=color,
        visible=visible,
        y_axis=y_axis,
        line_style=line_style,
        line_width=line_width,
        opacity=opacity,
    )


def _time_axis(source: object) -> AxisSnapshot:
    minimum, maximum = _axis_limits(getattr(source, 'ax', None), 'get_xlim', 0.0, 0.0)
    return AxisSnapshot(minimum=minimum, maximum=maximum, label='Time')


def _temperature_axis(source: object) -> AxisSnapshot:
    minimum, maximum = _axis_limits(getattr(source, 'ax', None), 'get_ylim', 0.0, 0.0)
    return AxisSnapshot(minimum=minimum, maximum=maximum, label='Temperature')


def _ror_axis(source: object, curves: tuple[CurveSnapshot, ...] = ()) -> AxisSnapshot | None:
    axis = getattr(source, 'delta_ax', None)
    if axis is None:
        return None
    minimum, maximum = _axis_limits(axis, 'get_ylim', 0.0, 0.0)
    return _expanded_ror_axis(
        AxisSnapshot(minimum=minimum, maximum=maximum, label='RoR'),
        _visible_ror_values(source, curves),
    )


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


def _palette_color_with_default(source: object, color_key: str, default: str) -> str:
    palette = getattr(source, 'palette', {})
    if isinstance(palette, dict):
        color = palette.get(color_key)
        if isinstance(color, str) and color:
            return color
    return default


def _event_markers(source: object) -> tuple[EventMarkerSnapshot, ...]:
    return _main_event_markers(source) + _foreground_event_markers(source) + _background_event_markers(source)


def _event_value_snapshots(events: tuple[EventMarkerSnapshot, ...]) -> tuple[EventValueSnapshot, ...]:
    values: list[EventValueSnapshot] = []
    for event in events:
        if event.value is None or event.kind == 'main':
            continue
        values.append(EventValueSnapshot(
            time=event.time,
            value=event.value,
            event_type=event.event_type,
            color=event.color,
            label=event.label,
            kind=event.kind,
            opacity=0.55 if event.kind == 'special' else 0.34,
        ))
    return tuple(values)


def _main_event_markers(source: object) -> tuple[EventMarkerSnapshot, ...]:
    timex = _sequence(source, 'timex')
    timeindex = _sequence(source, 'timeindex')
    markers: list[EventMarkerSnapshot] = []
    for index, label in _MAIN_EVENTS:
        if index >= len(timeindex):
            continue
        event_index = int(timeindex[index])
        is_set = event_index >= 0 if index == 0 else event_index > 0
        if not is_set or event_index >= len(timex):
            continue
        markers.append(EventMarkerSnapshot(
            time=float(timex[event_index]),
            label=_main_event_label(timex, timeindex, index, label),
            event_type=100 + index,
            color=_palette_color(source, 'markers'),
            temperature=_temperature_at(source, 'temp2', event_index),
            kind='main',
        ))
    tp_marker = _turning_point_marker(source, timex, timeindex)
    if tp_marker is not None:
        markers.append(tp_marker)
        markers.sort(key=lambda event: (event.time, event.event_type))
    return tuple(markers)


def _turning_point_marker(
        source: object,
        timex: list[Any],
        timeindex: list[Any]) -> EventMarkerSnapshot | None:
    if not bool(getattr(source, 'markTPflag', False)):
        return None
    tp_index = _tp_index(source)
    if tp_index is None or tp_index <= 0 or tp_index >= len(timex):
        return None
    label = f'{_translate_label("TP")} {_event_elapsed_label(timex, timeindex, tp_index)}'
    return EventMarkerSnapshot(
        time=float(timex[tp_index]),
        label=label,
        event_type=99,
        color=_palette_color(source, 'markers'),
        temperature=_temperature_at(source, 'temp2', tp_index),
        kind='main',
    )


def _main_event_label(timex: list[Any], timeindex: list[Any], event_number: int, fallback: str) -> str:
    label = _translate_label(fallback)
    if event_number == 0:
        return label
    if event_number >= len(timeindex):
        return label
    try:
        event_index = int(timeindex[event_number])
    except (TypeError, ValueError):
        return label
    return f'{label} {_event_elapsed_label(timex, timeindex, event_index)}'


def _translate_label(text: str) -> str:
    translate = getattr(QApplication, 'translate', None)
    if not callable(translate):
        return text
    try:
        return str(translate('Label', text))
    except Exception:  # pylint: disable=broad-exception-caught
        return text


def _event_elapsed_label(timex: list[Any], timeindex: list[Any], event_index: int) -> str:
    try:
        charge_index = int(timeindex[0])
    except (IndexError, TypeError, ValueError):
        charge_index = -1
    charge_time = 0.0
    if charge_index >= 0 and charge_index < len(timex):
        charge_time = float(timex[charge_index])
    try:
        return _format_seconds_as_minsec(float(timex[event_index]) - charge_time)
    except (IndexError, TypeError, ValueError):
        return '0:00'


def _foreground_event_markers(source: object) -> tuple[EventMarkerSnapshot, ...]:
    timex = _sequence(source, 'timex')
    specialevents = _sequence(source, 'specialevents')
    event_types = _sequence(source, 'specialeventstype')
    event_values = _sequence(source, 'specialeventsvalue')
    event_labels = _sequence(source, 'specialeventsStrings')
    limit = min(len(specialevents), len(event_types), len(event_values))
    markers: list[EventMarkerSnapshot] = []
    for i in range(limit):
        event_type = int(event_types[i])
        if not _event_type_visible(source, event_type):
            continue
        event_index = int(specialevents[i])
        if event_index < 0 or event_index >= len(timex):
            continue
        markers.append(EventMarkerSnapshot(
            time=float(timex[event_index]),
            label=_event_label(source, event_type, event_labels, i),
            event_type=event_type,
            color=_event_color(source, event_type),
            value=None if event_values[i] is None else float(event_values[i]),
            kind='special',
        ))
    return tuple(markers)


def _background_event_markers(source: object) -> tuple[EventMarkerSnapshot, ...]:
    if not bool(getattr(source, 'backgroundeventsflag', False)):
        return ()
    timex = _sequence(source, 'timeB')
    background_events = _sequence(source, 'backgroundEvents')
    event_types = _sequence(source, 'backgroundEtypes')
    event_values = _sequence(source, 'backgroundEvalues')
    event_labels = _sequence(source, 'backgroundEStrings')
    limit = min(len(background_events), len(event_types), len(event_values))
    markers: list[EventMarkerSnapshot] = []
    for i in range(limit):
        event_type = int(event_types[i])
        if not _event_type_visible(source, event_type):
            continue
        event_index = int(background_events[i])
        if event_index < 0 or event_index >= len(timex):
            continue
        markers.append(EventMarkerSnapshot(
            time=float(timex[event_index]),
            label=_event_label(source, event_type, event_labels, i),
            event_type=event_type,
            color=_event_color(source, event_type),
            value=None if event_values[i] is None else float(event_values[i]),
            kind='background',
        ))
    return tuple(markers)


def _phase_bands(source: object) -> tuple[PhaseBandSnapshot, ...]:
    phases = _sequence(source, 'phases')
    if len(phases) < 4:
        return ()
    bands: list[PhaseBandSnapshot] = []
    opacity = _settings_float(('phaseBandOpacity', 'phase_band_opacity'), 0.30)
    for index, color_key in enumerate(('rect1', 'rect2', 'rect3')):
        try:
            minimum = float(phases[index])
            maximum = float(phases[index + 1])
        except (TypeError, ValueError):
            continue
        if maximum <= minimum:
            continue
        bands.append(PhaseBandSnapshot(
            minimum=minimum,
            maximum=maximum,
            color=_phase_band_color(source, color_key, index),
            opacity=opacity,
        ))
    return tuple(bands)


def _time_ranges(source: object) -> tuple[TimeRangeSnapshot, ...]:
    phase_times = _phase_event_times(source)
    if phase_times is None:
        return ()
    _, _, first_crack_start, drop = phase_times
    if drop <= first_crack_start:
        return ()
    return (
        TimeRangeSnapshot(
            start=first_crack_start,
            end=drop,
            color='#F4F2EC',  # Morandi light cream (was #FFF6A8 yellow)
            opacity=0.28,
            label='Development',
            kind='development',
        ),
    )


def _phase_summaries(source: object) -> tuple[PhaseSummarySnapshot, ...]:
    phase_times = _phase_event_times(source)
    phase_indexes = _phase_event_indexes(source)
    if phase_times is None or phase_indexes is None:
        return ()
    charge, dry, first_crack_start, drop = phase_times
    charge_index, dry_index, first_crack_index, drop_index = phase_indexes
    if not (charge < dry < first_crack_start < drop):
        return ()
    total_duration = drop - charge
    if total_duration <= 0:
        return ()
    tp_index = _tp_index(source)
    drying_delta_start_index = (
        tp_index
        if tp_index is not None and charge_index < tp_index < dry_index
        else charge_index
    )
    phase_specs = (
        ('Drying', charge, dry, drying_delta_start_index, dry_index, 'roastphase1', '#F5F5F0'),
        ('Maillard', dry, first_crack_start, dry_index, first_crack_index, 'roastphase2', '#F5F0E1'),
        ('Development', first_crack_start, drop, first_crack_index, drop_index, 'roastphase3', '#F4F2EC'),
    )
    summaries: list[PhaseSummarySnapshot] = []
    for label, start, end, start_index, end_index, color_key, default_color in phase_specs:
        duration = end - start
        summaries.append(PhaseSummarySnapshot(
            start=start,
            end=end,
            label=label,
            duration_text=_format_seconds_as_minsec(duration),
            percent_text=f'{duration / total_duration * 100.0:.1f}%',
            delta_text=_temperature_delta_text(source, start_index, end_index),
            color=_palette_color_with_default(source, color_key, default_color),
        ))
    return tuple(summaries)


def _phase_event_times(source: object) -> tuple[float, float, float, float] | None:
    indexes = _phase_event_indexes(source)
    if indexes is None:
        return None
    timex = _sequence(source, 'timex')
    charge_index, dry_index, first_crack_index, drop_index = indexes
    if drop_index >= len(timex):
        return None
    return (
        float(timex[charge_index]),
        float(timex[dry_index]),
        float(timex[first_crack_index]),
        float(timex[drop_index]),
    )


def _phase_event_indexes(source: object) -> tuple[int, int, int, int] | None:
    timeindex = _sequence(source, 'timeindex')
    if len(timeindex) <= 6:
        return None
    try:
        charge_index = int(timeindex[0])
        dry_index = int(timeindex[1])
        first_crack_index = int(timeindex[2])
        drop_index = int(timeindex[6])
    except (TypeError, ValueError):
        return None
    if charge_index < 0 or dry_index <= 0 or first_crack_index <= 0 or drop_index <= 0:
        return None
    return charge_index, dry_index, first_crack_index, drop_index


def _format_seconds_as_minsec(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    return f'{minutes}:{remaining_seconds:02d}'


def _temperature_delta_text(source: object, start_index: int, end_index: int) -> str:
    start_temperature = _temperature_at(source, 'temp2', start_index)
    end_temperature = _temperature_at(source, 'temp2', end_index)
    if start_temperature is None or end_temperature is None:
        return ''
    return f'{end_temperature - start_temperature:.1f}{_temperature_unit_suffix(source)}'


def _temperature_unit_suffix(source: object) -> str:
    mode = str(getattr(source, 'mode', '')).strip()
    return mode if mode in {'C', 'F'} else ''


def _guide_lines(source: object) -> tuple[GuideLineSnapshot, ...]:
    guides: list[GuideLineSnapshot] = []
    guides.extend(_auc_guides(source))
    bbp_guide = _bbp_guide(source)
    if bbp_guide is not None:
        guides.append(bbp_guide)
    charge_target_guide = _charge_target_guide(source)
    if charge_target_guide is not None:
        guides.append(charge_target_guide)
    return tuple(guides)


def _area_fills(source: object) -> tuple[AreaFillSnapshot, ...]:
    auc_area = _auc_area_fill(source)
    if auc_area is None:
        return ()
    return (auc_area,)


def _auc_area_fill(source: object) -> AreaFillSnapshot | None:
    if bool(getattr(source, 'flagon', False)) or not bool(getattr(source, 'AUCshowFlag', False)):
        return None
    timex = _sequence(source, 'timex')
    stemp2 = _sequence(source, 'stemp2')
    timeindex = _sequence(source, 'timeindex')
    if len(timeindex) <= 6 or not timeindex[6]:
        return None
    try:
        drop_index = int(timeindex[6])
    except (TypeError, ValueError):
        return None
    if drop_index <= 0 or drop_index >= min(len(timex), len(stemp2)):
        return None

    tp_index = _tp_index(source)
    if tp_index is None or tp_index < 0 or tp_index >= drop_index:
        return None
    base_index = _auc_base_index(source, tp_index, drop_index, stemp2)
    if base_index is None or base_index < 0 or base_index > drop_index:
        return None
    baseline = _temperature_value(stemp2[base_index])
    if baseline is None or baseline <= 0:
        return None
    x_values = timex[base_index:drop_index + 1]
    y_values = [_temperature_value(value) for value in stemp2[base_index:drop_index + 1]]
    if len(x_values) <= 1 or not any(value is not None and value > 0 for value in y_values):
        return None
    return AreaFillSnapshot.from_sequences(
        x=x_values,
        y=y_values,
        baseline=baseline,
        color=_palette_color(source, 'aucarea'),
        label='AUC area',
        opacity=0.28,
        kind='auc',
    )


def _tp_index(source: object) -> int | None:
    aw = getattr(source, 'aw', None)
    find_tp = getattr(aw, 'findTP', None)
    if callable(find_tp):
        try:
            return int(find_tp())
        except (TypeError, ValueError):
            return None
    return _first_index(source, ('TP_index', 'TPindex', 'TPalarmtimeindex'))


def _auc_base_index(source: object, tp_index: int, drop_index: int, stemp2: list[Any]) -> int | None:
    if bool(getattr(source, 'AUCbaseFlag', False)):
        aw = getattr(source, 'aw', None)
        ts = getattr(aw, 'ts', None)
        if callable(ts):
            try:
                result = ts()
                if len(result) >= 4:
                    return int(result[3])
            except (TypeError, ValueError):
                return None
    auc_base = _numeric_attr(source, 'AUCbase')
    if auc_base is None:
        return tp_index
    numeric_segment = [_numeric_value(value) for value in stemp2[tp_index:drop_index]]
    if not numeric_segment or any(value is None for value in numeric_segment):
        return None
    return tp_index + _bisection([value for value in numeric_segment if value is not None], auc_base)


def _bisection(values: list[float], value: float) -> int:
    if not values:
        return -1
    if value < values[0]:
        return -1
    if value > values[-1]:
        return len(values)
    if value == values[0]:
        return 0
    if value == values[-1]:
        return len(values) - 1
    lower = 0
    upper = len(values) - 1
    while upper - lower > 1:
        middle = (upper + lower) >> 1
        if value >= values[middle]:
            lower = middle
        else:
            upper = middle
    if abs(value - values[lower]) > abs(values[upper] - value):
        return upper
    return lower


def _auc_guides(source: object) -> tuple[GuideLineSnapshot, ...]:
    if not bool(getattr(source, 'AUCguideFlag', False)):
        return ()
    guide_time = _numeric_attr(source, 'AUCguideTime')
    if guide_time is None or guide_time <= 0:
        return ()
    maximum_time = _numeric_attr(source, 'endofx')
    if maximum_time is not None and guide_time >= maximum_time:
        return ()
    return (
        GuideLineSnapshot(
            position=guide_time,
            label='AUC guide',
            color=_palette_color_with_default(source, 'aucguide', '#8FA39C'),
            orientation='vertical',
            line_style='-',
            opacity=0.5,
            kind='auc',
        ),
    )


def _bbp_guide(source: object) -> GuideLineSnapshot | None:
    autotimex_mode = _integer_attr(source, 'autotimexMode', 0)
    if not bool(getattr(source, 'compareBBP', False)) and autotimex_mode == 0:
        return None
    index = _first_index(source, ('BBPindex', 'bbp_index', 'bbpIndex'))
    timex = _sequence(source, 'timex')
    if index is None:
        timeindex = _sequence(source, 'timeindex')
        if len(timeindex) > 0:
            try:
                index = int(timeindex[0])
            except (TypeError, ValueError):
                index = None
    if index is None or index < 0 or index >= len(timex):
        return None
    return GuideLineSnapshot(
        position=float(timex[index]),
        label='BBP',
        color=_palette_color_with_default(source, 'timeguide', '#53756F'),
        orientation='vertical',
        line_style='--',
        opacity=0.45,
        kind='bbp',
    )


def _charge_target_guide(source: object) -> GuideLineSnapshot | None:
    manager = getattr(source, 'charge_manager', None)
    if manager is not None:
        enabled = bool(getattr(manager, 'enabled', False))
        target_temp = _numeric_value(getattr(manager, 'target_temp', None))
    else:
        enabled = bool(getattr(source, 'chargeTargetEnabled', False))
        target_temp = _first_numeric_attr(source, ('target_charge_temp', 'TargetChargeTemp', 'charge_target_temp'))
    if not enabled or target_temp is None or target_temp <= 0:
        return None
    return GuideLineSnapshot(
        position=target_temp,
        label='Charge target',
        color='#B4685C',
        orientation='horizontal',
        y_axis='temperature',
        line_style='--',
        opacity=0.42,
        kind='charge_target',
    )


# Valid readiness color keywords (render-layer hex mapping lives in plot_pyqtgraph_adapter._CHARGE_BG_COLOR_HEX)
_VALID_READINESS_COLORS: frozenset[str] = frozenset({'red', 'blue', 'green', 'gray'})


def _charge_target_annotations(
        source: object,
        *,
        time_axis: AxisSnapshot | None = None,
        temperature_axis: AxisSnapshot | None = None,
) -> tuple[ChargeTargetAnnotationSnapshot, ...]:
    """Extract a single charge-target annotation snapshot, or empty tuple when disabled.

    Mirrors the visual states of canvas.draw_charge_target_annotation:
    - is_charged=True:  static top-left card showing target/actual temp/RoR/RWT
    - is_charged=False: dynamic arrow callout showing readiness title/reason/prediction
    """
    manager = getattr(source, 'charge_manager', None)
    if manager is None:
        return ()
    enabled = bool(getattr(manager, 'enabled', False))
    if not enabled:
        return ()
    target_temp = _numeric_value(getattr(manager, 'target_temp', None)) or 0.0
    target_ror = _numeric_value(getattr(manager, 'target_ror', None)) or 0.0
    charged_temp = _numeric_value(getattr(manager, 'charged_temp', None)) or 0.0
    charged_ror = _numeric_value(getattr(manager, 'charged_ror', None)) or 0.0
    is_charged = not bool(getattr(manager, 'active', True))

    timex = _sequence(source, 'timex')
    temp2 = _sequence(source, 'temp2')
    delta2 = _sequence(source, 'delta2')
    current_time = _finite_numeric_value(timex[-1], 0.0) if timex else 0.0
    current_temp = _finite_numeric_value(temp2[-1], 0.0) if temp2 else 0.0
    current_ror = _finite_numeric_value(delta2[-1] if delta2 else None, 0.0)

    if time_axis is not None and time_axis.maximum > time_axis.minimum:
        x_limit = float(time_axis.maximum)
    elif timex:
        x_limit = _finite_numeric_value(timex[-1], 0.0) * 1.05
    else:
        x_limit = 600.0
    if temperature_axis is not None and temperature_axis.maximum > temperature_axis.minimum:
        y_limit_top = float(temperature_axis.maximum)
    elif temp2:
        y_limit_top = _finite_numeric_value(max(temp2), 0.0) * 1.05
    else:
        y_limit_top = 250.0

    calculate_rwt = getattr(manager, 'calculate_rwt', lambda _ror: 0.0)
    target_rwt = _safe_charge_rwt(calculate_rwt, target_ror)

    if is_charged:
        current_rwt = _safe_charge_rwt(calculate_rwt, charged_ror)
        return (ChargeTargetAnnotationSnapshot(
            enabled=True,
            is_charged=True,
            target_temp=target_temp,
            target_ror=target_ror,
            charged_temp=charged_temp,
            charged_ror=charged_ror,
            title='',
            reason='',
            prediction_seconds=None,
            color='gray',
            current_rwt=current_rwt,
            target_rwt=target_rwt,
            anchor_time=0.0,
            anchor_temp=0.0,
            x_limit=x_limit,
            y_limit_top=y_limit_top,
        ),)

    # Active state: call evaluate_readiness
    evaluate = getattr(manager, 'evaluate_readiness', None)
    if evaluate is None:
        return (ChargeTargetAnnotationSnapshot(
            enabled=True,
            is_charged=False,
            target_temp=target_temp,
            target_ror=target_ror,
            charged_temp=charged_temp,
            charged_ror=charged_ror,
            title='等待数据',
            reason='升温数据不足',
            prediction_seconds=None,
            color='gray',
            current_rwt=0.0,
            target_rwt=target_rwt,
            anchor_time=current_time,
            anchor_temp=current_temp,
            x_limit=x_limit,
            y_limit_top=y_limit_top,
        ),)

    try:
        readiness = evaluate(
            current_temp=current_temp,
            current_ror=current_ror,
        )
    except (ArithmeticError, TypeError, ValueError, AttributeError):
        return (ChargeTargetAnnotationSnapshot(
            enabled=True,
            is_charged=False,
            target_temp=target_temp,
            target_ror=target_ror,
            charged_temp=charged_temp,
            charged_ror=charged_ror,
            title='等待数据',
            reason='升温数据不足',
            prediction_seconds=None,
            color='gray',
            current_rwt=0.0,
            target_rwt=target_rwt,
            anchor_time=current_time,
            anchor_temp=current_temp,
            x_limit=x_limit,
            y_limit_top=y_limit_top,
        ),)
    current_rwt = _safe_charge_rwt(calculate_rwt, current_ror)
    color_value = readiness.color if readiness.color in _VALID_READINESS_COLORS else 'gray'
    return (ChargeTargetAnnotationSnapshot(
        enabled=True,
        is_charged=False,
        target_temp=target_temp,
        target_ror=target_ror,
        charged_temp=charged_temp,
        charged_ror=charged_ror,
        title=readiness.title,
        reason=readiness.reason,
        prediction_seconds=readiness.prediction_seconds,
        color=color_value,
        current_rwt=current_rwt,
        target_rwt=target_rwt,
        anchor_time=current_time,
        anchor_temp=current_temp,
        x_limit=x_limit,
        y_limit_top=y_limit_top,
    ),)


def _event_type_visible(source: object, event_type: int) -> bool:
    show_types = _sequence(source, 'showEtypes')
    if 0 <= event_type < len(show_types):
        return bool(show_types[event_type])
    return True


def _event_label(source: object, event_type: int, event_labels: list[Any], event_index: int) -> str:
    if event_index < len(event_labels):
        label = event_labels[event_index]
        if isinstance(label, str) and label.strip():
            return label.strip()
    etypes = _sequence(source, 'etypes')
    if 0 <= event_type < len(etypes):
        label = etypes[event_type]
        if isinstance(label, str) and label.strip():
            return label.strip()
    return f'Event {event_type}'


def _event_color(source: object, event_type: int) -> str:
    event_colors = _sequence(source, 'EvalueColor')
    if 0 <= event_type < len(event_colors):
        color = event_colors[event_type]
        if isinstance(color, str):
            return color
    palette = getattr(source, 'palette', {})
    if isinstance(palette, dict):
        color = palette.get('specialeventtext')
        if isinstance(color, str):
            return color
    return '#ffffff'


def _phase_band_color(source: object, color_key: str, index: int) -> str:
    # Force Morandi light palette for phase bands — ignore saved palette overrides
    # from .aset/QSettings to maintain the ArtisanZ visual design language.
    return ('#F5F5F0', '#F5F0E1', '#F4F2EC')[index]


def _background_available(source: object) -> bool:
    return (
        bool(getattr(source, 'background', False)) or
        getattr(source, 'backgroundprofile', None) is not None or
        len(_sequence(source, 'timeB')) > 0
    )


def _background_temperature_values(source: object, values: list[Any]) -> list[float | None]:
    if bool(getattr(source, 'backgroundShowFullflag', False)):
        return [_temperature_value(value) for value in values]
    length = len(values)
    if length == 0:
        return []
    timeindex = _sequence(source, 'timeindexB')
    charge_index = int(timeindex[0]) if len(timeindex) > 0 and int(timeindex[0]) > -1 else 0
    drop_index = int(timeindex[6]) if len(timeindex) > 6 and int(timeindex[6]) > 0 else length - 1
    if bool(getattr(source, 'autotimex', False)) and int(getattr(source, 'autotimexMode', 0)) != 0:
        start_index = 0
    else:
        start_index = charge_index
    return [
        _temperature_value(value) if start_index <= index <= drop_index else None
        for index, value in enumerate(values)
    ]


def _foreground_delta_values(source: object, values: list[Any]) -> list[float | None]:
    converted_values = [_temperature_value(value) for value in values]
    if not converted_values:
        return []
    if bool(getattr(source, 'flagstart', False)) or bool(getattr(source, 'foregroundShowFullflag', False)):
        return converted_values
    timeindex = _sequence(source, 'timeindex')
    if len(timeindex) <= 6:
        return converted_values
    try:
        charge_index = int(timeindex[0])
        drop_index = int(timeindex[6])
    except (TypeError, ValueError):
        return converted_values
    if charge_index < 0:
        return converted_values
    if drop_index <= 0 or drop_index >= len(converted_values):
        drop_index = len(converted_values) - 1
    delay = _positive_numeric_attr(source, 'delay', 1000.0)
    skip = max(2, min(20, int(round(5000 / delay))))
    skip_after_drop = max(2, int(round(skip / 2)))
    start_index = charge_index + skip
    end_index = drop_index - skip_after_drop
    if not (0 <= start_index < end_index <= len(converted_values)):
        return [None for _ in converted_values]
    return [
        value if start_index <= index < end_index else None
        for index, value in enumerate(converted_values)
    ]


def _visible_ror_values(source: object, curves: tuple[CurveSnapshot, ...]) -> tuple[float, ...]:
    values: list[float] = []
    if curves:
        for curve in curves:
            if curve.y_axis != 'ror' or not curve.visible:
                continue
            values.extend(value for value in curve.y if value is not None and math.isfinite(value))
    else:
        for attr_name, visible_attr in (('delta2', 'DeltaBTflag'), ('delta1', 'DeltaETflag')):
            if not bool(getattr(source, visible_attr, False)):
                continue
            values.extend(
                value
                for value in _foreground_delta_values(source, _sequence(source, attr_name))
                if value is not None and math.isfinite(value)
            )
    return tuple(values)


def _expanded_ror_axis(axis: AxisSnapshot, values: tuple[float, ...]) -> AxisSnapshot:
    if not values:
        return axis
    data_minimum = min(values)
    data_maximum = max(values)
    if axis.minimum <= data_minimum and data_maximum <= axis.maximum:
        return axis
    axis_span = axis.maximum - axis.minimum
    data_span = data_maximum - data_minimum
    padding = max(1.0, abs(axis_span) * 0.05, abs(data_span) * 0.1)
    return AxisSnapshot(
        minimum=min(axis.minimum, data_minimum - padding),
        maximum=max(axis.maximum, data_maximum + padding),
        label=axis.label,
    )


def _temperature_value(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number == -1 or math.isnan(number):
        return None
    return number


def _temperature_at(source: object, attr_name: str, index: int) -> float | None:
    values = _sequence(source, attr_name)
    if index < 0 or index >= len(values):
        return None
    return _temperature_value(values[index])


def _color_attr(source: object, attr_name: str, color_key: str) -> str:
    color = getattr(source, attr_name, None)
    if isinstance(color, str) and color:
        return color
    return _palette_color(source, color_key)


def _opacity(source: object, attr_name: str, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(getattr(source, attr_name, default))))
    except (TypeError, ValueError):
        return default


def _line_style(source: object, attr_name: str, default: str) -> str:
    value = getattr(source, attr_name, default)
    if isinstance(value, str) and value:
        return value
    return default


def _line_width(source: object, attr_name: str, default: float) -> float:
    try:
        return float(getattr(source, attr_name, default))
    except (TypeError, ValueError):
        return default


def _line_style_attr(name: str) -> str:
    return {
        'BT': 'BTlinestyle',
        'ET': 'ETlinestyle',
        'Delta BT': 'BTdeltalinestyle',
        'Delta ET': 'ETdeltalinestyle',
    }.get(name, '')


def _line_width_attr(name: str) -> str:
    return {
        'BT': 'BTlinewidth',
        'ET': 'ETlinewidth',
        'Delta BT': 'BTdeltalinewidth',
        'Delta ET': 'ETdeltalinewidth',
    }.get(name, '')


def _sequence(source: object, attr_name: str) -> list[Any]:
    value = getattr(source, attr_name, [])
    if isinstance(value, list):
        return value
    return list(value)


def _first_index(source: object, attr_names: tuple[str, ...]) -> int | None:
    for attr_name in attr_names:
        value = getattr(source, attr_name, None)
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _first_numeric_attr(source: object, attr_names: tuple[str, ...]) -> float | None:
    for attr_name in attr_names:
        value = _numeric_attr(source, attr_name)
        if value is not None:
            return value
    return None


def _numeric_attr(source: object, attr_name: str) -> float | None:
    return _numeric_value(getattr(source, attr_name, None))


def _positive_numeric_attr(source: object, attr_name: str, default: float) -> float:
    value = _numeric_attr(source, attr_name)
    if value is None or value <= 0:
        return default
    return value


def _numeric_value(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _finite_numeric_value(value: object, default: float = 0.0) -> float:
    """Like _numeric_value but also rejects Inf and returns a default."""
    number = _numeric_value(value)
    if number is None or not math.isfinite(number):
        return default
    return number


def _safe_charge_rwt(calculate_rwt: object, ror: float | None) -> float:
    """Call calculate_rwt defensively; return 0.0 on any failure or non-finite result."""
    if not callable(calculate_rwt):
        return 0.0
    try:
        value = float(calculate_rwt(ror) or 0.0)
    except (ArithmeticError, TypeError, ValueError):
        return 0.0
    return value if math.isfinite(value) else 0.0


def _integer_attr(source: object, attr_name: str, default: int) -> int:
    try:
        return int(getattr(source, attr_name, default))
    except (TypeError, ValueError):
        return default
