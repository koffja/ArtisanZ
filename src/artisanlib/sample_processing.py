from __future__ import annotations

from collections.abc import Sequence

TemperatureValue = float | None


def decay_weight_sequence(curve_filter: int) -> tuple[int, ...]:
    if curve_filter <= 0:
        return (1,)
    return tuple(range(1, curve_filter + 1))


def smoothing_weights_for_recent_readings(
        readings: Sequence[float],
        decay_weights: Sequence[int],
        curve_filter: int) -> tuple[int, ...]:
    if curve_filter <= 0:
        return (1,)
    recent_readings = readings[-(curve_filter + 1):]
    if -1 in recent_readings:
        return (1,)
    if len(decay_weights) == curve_filter:
        return tuple(int(weight) for weight in decay_weights)
    return decay_weight_sequence(curve_filter)


def pid_process_value(
        pid_source: int,
        smoothed_et: TemperatureValue,
        smoothed_bt: TemperatureValue,
        extra_temps_1: Sequence[Sequence[float]],
        extra_temps_2: Sequence[Sequence[float]]) -> TemperatureValue:
    if pid_source in {0, 1}:
        return smoothed_bt
    if pid_source == 2:
        return smoothed_et

    source_offset = pid_source - 3
    if source_offset < 0:
        return 0.0

    device_index = source_offset // 2
    if source_offset % 2 == 0:
        if len(extra_temps_1) > device_index and extra_temps_1[device_index]:
            return extra_temps_1[device_index][-1]
    elif len(extra_temps_2) > device_index and extra_temps_2[device_index]:
        return extra_temps_2[device_index][-1]
    return 0.0


__all__ = [
    'decay_weight_sequence',
    'pid_process_value',
    'smoothing_weights_for_recent_readings',
]
