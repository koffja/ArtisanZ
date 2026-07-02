from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artisanlib.plot_snapshot import RoastPlotSnapshot
from artisanlib.plot_snapshot_extractor import build_roast_plot_snapshot


@dataclass(frozen=True, slots=True)
class ProfileSnapshotLoadResult:
    path: str
    title: str
    sample_count: int
    event_count: int
    snapshot: RoastPlotSnapshot


@dataclass(frozen=True, slots=True)
class ProfileSnapshotAxis:
    xlim: tuple[float, float]
    ylim: tuple[float, float]

    def get_xlim(self) -> tuple[float, float]:
        return self.xlim

    def get_ylim(self) -> tuple[float, float]:
        return self.ylim


class ProfileSnapshotAw:
    def __init__(self, source: ProfileSnapshotSource) -> None:
        self._source = source

    def findTP(self) -> int:  # noqa: N802
        computed = self._source.profile.get('computed')
        if isinstance(computed, dict):
            tp_index = _integer_value(computed.get('TP_idx'))
            if tp_index is not None:
                return tp_index
        return _minimum_temperature_index(self._source.temp2)


class ProfileSnapshotSource:
    def __init__(self, profile: dict[str, Any]) -> None:
        self.profile = profile
        self.timex = _float_sequence(profile.get('timex'))
        self.temp1 = _temperature_sequence(profile.get('temp1'))
        self.temp2 = _temperature_sequence(profile.get('temp2'))
        self.stemp1 = _temperature_sequence(profile.get('stemp1')) or self.temp1
        self.stemp2 = _temperature_sequence(profile.get('stemp2')) or self.temp2
        self.delta1 = _temperature_sequence(profile.get('delta1')) or _ror_values(self.timex, self.temp1)
        self.delta2 = _temperature_sequence(profile.get('delta2')) or _ror_values(self.timex, self.temp2)
        self.ax = ProfileSnapshotAxis(
            xlim=_time_axis_range(profile, self.timex),
            ylim=_axis_range(profile, self.temp1 + self.temp2, 'ymin', 'ymax', fallback_padding=20.0),
        )
        self.delta_ax = ProfileSnapshotAxis(
            xlim=self.ax.xlim,
            ylim=_ror_axis_range(profile, self.delta1 + self.delta2),
        )
        self.palette = _profile_palette(profile)
        self.ETcurve = bool(profile.get('ETcurve', True))
        self.BTcurve = bool(profile.get('BTcurve', True))
        self.DeltaETflag = bool(profile.get('DeltaETflag', any(value is not None for value in self.delta1)))
        self.DeltaBTflag = bool(profile.get('DeltaBTflag', any(value is not None for value in self.delta2)))
        self.timeindex = _sequence(profile.get('timeindex'))
        self.specialevents = _sequence(profile.get('specialevents'))
        self.specialeventstype = _sequence(profile.get('specialeventstype'))
        self.specialeventsvalue = _sequence(profile.get('specialeventsvalue'))
        self.specialeventsStrings = _sequence(profile.get('specialeventsStrings'))
        self.etypes = _sequence(profile.get('etypes')) or ['Power', 'Fan', 'Damper', 'Drum', '--']
        self.showEtypes = _sequence(profile.get('showEtypes')) or [True] * max(12, len(self.etypes))
        self.EvalueColor = _sequence(profile.get('EvalueColor')) or [
            '#5E6B6E', '#B4685C', '#3C7A88', '#78905D', '#B98A4B',
        ]
        self.phases = _sequence(profile.get('phases'))
        self.watermarksflag = bool(profile.get('watermarksflag', len(self.phases) >= 4))
        self.AUCshowFlag = bool(profile.get('AUCshowFlag', _profile_has_auc(profile)))
        self.AUCbaseFlag = bool(profile.get('AUCbaseFlag', False))
        self.AUCbase = _profile_auc_base(profile)
        self.AUCguideFlag = bool(profile.get('AUCguideFlag', False))
        self.AUCguideTime = profile.get('AUCguideTime', 0)
        self.endofx = self.ax.xlim[1]
        self.compareBBP = bool(profile.get('compareBBP', False))
        self.flagon = False
        self.aw = ProfileSnapshotAw(self)

    def __getattr__(self, name: str) -> Any:
        try:
            return self.profile[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def load_profile_snapshot(profile_path: str | Path) -> ProfileSnapshotLoadResult:
    from artisanlib.util import deserialize

    path = Path(profile_path)
    if not path.is_file():
        raise FileNotFoundError(f'Profile file does not exist: {path}')
    profile = deserialize(str(path))
    if not isinstance(profile, dict):
        raise TypeError(f'Expected profile data dict from {path}, got {type(profile).__name__}')
    if not profile:
        raise ValueError(f'Profile file has no readable profile data: {path}')
    source = ProfileSnapshotSource(profile)
    if not source.timex:
        raise ValueError(f'Profile file has no usable time samples: {path}')
    if not any(value is not None for value in source.temp1 + source.temp2):
        raise ValueError(f'Profile file has no usable temperature samples: {path}')
    snapshot = build_roast_plot_snapshot(source)
    return ProfileSnapshotLoadResult(
        path=str(path),
        title=str(profile.get('title', '')),
        sample_count=len(source.timex),
        event_count=len(snapshot.events),
        snapshot=snapshot,
    )


def _profile_palette(profile: dict[str, Any]) -> dict[str, str]:
    palette = profile.get('palette')
    if isinstance(palette, dict):
        return {str(key): str(value) for key, value in palette.items() if isinstance(value, str)}
    return {
        'bt': '#4E7180',
        'et': '#B5644F',
        'deltabt': '#78905D',
        'deltaet': '#B98A4B',
        'markers': '#5E6B6E',
        'rect1': '#DDE8E0',
        'rect2': '#E7DEC9',
        'rect3': '#D9E4EA',
        'aucarea': '#767676',
        'specialeventtext': '#FFFFFF',
    }


def _profile_has_auc(profile: dict[str, Any]) -> bool:
    computed = profile.get('computed')
    if isinstance(computed, dict):
        auc = _numeric_value(computed.get('AUC'))
        return auc is not None and auc > 0
    return False


def _profile_auc_base(profile: dict[str, Any]) -> float | None:
    computed = profile.get('computed')
    if isinstance(computed, dict):
        auc_base = _numeric_value(computed.get('AUCbase'))
        if auc_base is not None:
            return auc_base
    return _numeric_value(profile.get('AUCbase'))


def _time_axis_range(profile: dict[str, Any], times: list[float]) -> tuple[float, float]:
    minimum = _numeric_value(profile.get('xmin'))
    duration = _numeric_value(profile.get('xmax'))
    if minimum is not None and duration is not None and duration > 0.0:
        return minimum, minimum + duration
    numeric_times = [time for time in times if time is not None]
    if not numeric_times:
        return 0.0, 1.0
    fallback_minimum = minimum if minimum is not None else min(numeric_times)
    return (
        fallback_minimum,
        max(numeric_times) + 30.0,
    )


def _axis_range(
        profile: dict[str, Any],
        values: list[float | None],
        minimum_key: str,
        maximum_key: str,
        *,
        fallback_padding: float) -> tuple[float, float]:
    minimum = _numeric_value(profile.get(minimum_key))
    maximum = _numeric_value(profile.get(maximum_key))
    if minimum is not None and maximum is not None and maximum > minimum:
        return minimum, maximum
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return 0.0, 1.0
    return (
        min(numeric_values),
        max(numeric_values) + fallback_padding,
    )


def _ror_axis_range(profile: dict[str, Any], values: list[float | None]) -> tuple[float, float]:
    zmin = _numeric_value(profile.get('zmin'))
    zmax = _numeric_value(profile.get('zmax'))
    if zmin is not None and zmax is not None and zmax > zmin:
        return zmin, zmax
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return -10.0, 25.0
    return (
        math.floor((min(numeric_values) - 5.0) / 5.0) * 5.0,
        max(25.0, math.ceil((max(numeric_values) + 5.0) / 5.0) * 5.0),
    )


def _ror_values(times: list[float], values: list[float | None]) -> list[float | None]:
    if not times or not values:
        return []
    result: list[float | None] = [None]
    limit = min(len(times), len(values))
    for index in range(1, limit):
        previous = values[index - 1]
        current = values[index]
        elapsed = times[index] - times[index - 1]
        if previous is None or current is None or elapsed <= 0.0:
            result.append(None)
        else:
            result.append((current - previous) * 60.0 / elapsed)
    return result


def _minimum_temperature_index(values: list[float | None]) -> int:
    numeric_indexes = [(index, value) for index, value in enumerate(values) if value is not None]
    if not numeric_indexes:
        return 0
    return min(numeric_indexes, key=lambda item: item[1])[0]


def _float_sequence(value: object) -> list[float]:
    result: list[float] = []
    for item in _sequence(value):
        numeric = _numeric_value(item)
        if numeric is not None:
            result.append(numeric)
    return result


def _temperature_sequence(value: object) -> list[float | None]:
    result: list[float | None] = []
    for item in _sequence(value):
        numeric = _numeric_value(item)
        result.append(None if numeric is None or numeric == -1 else numeric)
    return result


def _sequence(value: object) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _integer_value(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _numeric_value(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


__all__ = [
    'ProfileSnapshotAxis',
    'ProfileSnapshotLoadResult',
    'ProfileSnapshotSource',
    'load_profile_snapshot',
]
