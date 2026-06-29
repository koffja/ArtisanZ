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


def relative_alarm_index(alarm_time: int, if_alarm_state: int, sample_count: int) -> int | None:
    if alarm_time != 10 or if_alarm_state == -1:
        return None
    if if_alarm_state < sample_count:
        return if_alarm_state
    return -1


def _relative_latest_value(values: Sequence[TemperatureValue], alarm_index: int | None) -> TemperatureValue:
    if not values:
        return None
    latest_value = values[-1]
    if latest_value is None:
        return None
    if alarm_index is None:
        return latest_value
    try:
        baseline_value = values[alarm_index]
    except IndexError:
        return None
    if baseline_value is not None:
        latest_value -= baseline_value
    return latest_value


def alarm_source_value(
        alarm_source: int,
        alarm_index: int | None,
        sample_delta1: Sequence[TemperatureValue],
        sample_delta2: Sequence[TemperatureValue],
        sample_temp1: Sequence[float],
        sample_temp2: Sequence[float],
        sample_extratemp1: Sequence[Sequence[float]],
        sample_extratemp2: Sequence[Sequence[float]],
        extra_device_count: int) -> TemperatureValue:
    if alarm_source == -2:
        return _relative_latest_value(sample_delta1, alarm_index)
    if alarm_source == -1:
        return _relative_latest_value(sample_delta2, alarm_index)
    if alarm_source == 0:
        return _relative_latest_value(sample_temp1, alarm_index)
    if alarm_source == 1:
        return _relative_latest_value(sample_temp2, alarm_index)
    if alarm_source <= 1 or (alarm_source - 2) >= 2 * extra_device_count:
        return None

    device_index = (alarm_source - 2) // 2
    if alarm_source % 2 == 0 and len(sample_extratemp1) > device_index:
        return _relative_latest_value(sample_extratemp1[device_index], alarm_index)
    if alarm_source % 2 == 1 and len(sample_extratemp2) > device_index:
        return _relative_latest_value(sample_extratemp2[device_index], alarm_index)
    return None


def alarm_temperature_reaches_limit(
        alarm_temp: TemperatureValue,
        alarm_cond: int,
        alarm_limit: float,
        alarm_index: int | None) -> bool:
    if alarm_temp is None or alarm_temp == -1:
        return False
    return (
        (alarm_cond == 1 and alarm_temp > alarm_limit) or
        (alarm_cond == 0 and alarm_temp < alarm_limit) or
        (alarm_cond == 2 and alarm_temp == alarm_limit) or
        (alarm_cond == 3 and alarm_temp != alarm_limit) or
        (alarm_index is not None and alarm_temp == alarm_limit)
    )


def alarm_is_eligible_for_evaluation(
        aflag: bool,
        alarm_state: int,
        alarm_guard: int,
        alarm_negative_guard: int,
        alarm_states: Sequence[int],
        alarm_time: int,
        local_flagstart: bool,
        timeindex: Sequence[int],
        tp_alarm_timeindex: int | None) -> bool:
    if not aflag or alarm_state != -1:
        return False
    if not (alarm_guard < 0 or (0 <= alarm_guard < len(alarm_states) and alarm_states[alarm_guard] != -1)):
        return False
    if not (
            alarm_negative_guard < 0 or
            (0 <= alarm_negative_guard < len(alarm_states) and alarm_states[alarm_negative_guard] == -1)):
        return False

    return (
        alarm_time == 9 or
        (alarm_time < 0 and local_flagstart) or
        (local_flagstart and alarm_time == 0 and timeindex[0] > -1) or
        (local_flagstart and 0 < alarm_time < 8 and timeindex[alarm_time] > 0) or
        (alarm_time == 10 and alarm_guard != -1) or
        (local_flagstart and alarm_time == 8 and timeindex[0] > -1 and bool(tp_alarm_timeindex))
    )


def alarm_time_offset_reached(
        alarm_offset: float,
        elapsed_time: float,
        alarm_time: int,
        local_flagstart: bool,
        sample_timex: Sequence[float],
        timeindex: Sequence[int],
        tp_alarm_timeindex: int | None,
        alarm_states: Sequence[int],
        alarm_guard: int) -> bool:
    if alarm_offset <= 0:
        return False
    alarm_time_value = elapsed_time
    if alarm_time < 0:
        pass
    elif local_flagstart and alarm_time == 0 and timeindex[0] > -1:
        alarm_time_value -= sample_timex[timeindex[0]]
    elif local_flagstart and alarm_time == 8 and tp_alarm_timeindex:
        alarm_time_value -= sample_timex[tp_alarm_timeindex]
    elif local_flagstart and alarm_time < 8 and timeindex[alarm_time] > 0:
        alarm_time_value -= sample_timex[timeindex[alarm_time]]
    elif local_flagstart and alarm_time == 10:
        alarm_time_value -= sample_timex[alarm_states[alarm_guard]]
    return alarm_time_value >= alarm_offset


__all__ = [
    'alarm_is_eligible_for_evaluation',
    'alarm_source_value',
    'alarm_temperature_reaches_limit',
    'alarm_time_offset_reached',
    'decay_weight_sequence',
    'pid_process_value',
    'relative_alarm_index',
    'smoothing_weights_for_recent_readings',
]
