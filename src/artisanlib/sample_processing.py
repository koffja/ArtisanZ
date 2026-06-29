from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

TemperatureValue = float | None


@dataclass(frozen=True)
class ConnectedCurvePoint:
    should_append: bool
    value: TemperatureValue


@dataclass(frozen=True)
class BackfillUpdate:
    index: int
    value: float


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


def connected_curve_point(
        reading: float,
        readings: Sequence[float],
        interpolate_max: int) -> ConnectedCurvePoint:
    if reading != -1:
        return ConnectedCurvePoint(True, reading)
    dropout_window = interpolate_max + 1
    if len(readings) > dropout_window and all(value == -1 for value in readings[-dropout_window:]):
        return ConnectedCurvePoint(True, None)
    return ConnectedCurvePoint(False, None)


def input_filter_backfill_updates(
        connected_times: Sequence[float],
        raw_times: Sequence[float],
        raw_values: Sequence[float],
        previous_latest: float | None,
        previous_previous: float | None) -> tuple[BackfillUpdate, ...]:
    updates: list[BackfillUpdate] = []
    if (
            len(connected_times) > 0 and
            len(raw_times) > 0 and
            len(raw_values) > 0 and
            previous_latest is not None and
            connected_times[-1] == raw_times[-1] and
            previous_latest != raw_values[-1]):
        updates.append(BackfillUpdate(-1, raw_values[-1]))
    if (
            len(connected_times) > 1 and
            len(raw_times) > 1 and
            len(raw_values) > 1 and
            previous_previous is not None and
            connected_times[-2] == raw_times[-2] and
            previous_previous != raw_values[-2]):
        updates.append(BackfillUpdate(-2, raw_values[-2]))
    return tuple(updates)


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


def _bt_above_event_threshold(mode: str, latest_bt: float, celsius_threshold: float, fahrenheit_threshold: float) -> bool:
    return (
        (mode == 'C' and latest_bt > celsius_threshold) or
        (mode == 'F' and latest_bt > fahrenheit_threshold)
    )


def auto_charge_event_candidate(
        auto_charge_idx: int,
        auto_charge_flag: bool,
        auto_charge_enabled: bool,
        charge_index: int,
        sample_count: int,
        mode: str,
        latest_bt: float) -> bool:
    return (
        auto_charge_idx == 0 and
        auto_charge_flag and
        auto_charge_enabled and
        charge_index < 0 and
        sample_count >= 5 and
        _bt_above_event_threshold(mode, latest_bt, 77, 170)
    )


def turning_point_timeout_index(
        tp_alarm_timeindex: int | None,
        charge_index: int,
        sample_times: Sequence[float],
        tp_max_roast_time: float,
        sample_count: int) -> int | None:
    if (
            tp_alarm_timeindex is None and
            charge_index > -1 and
            len(sample_times) > 0 and
            (sample_times[-1] - sample_times[charge_index]) > tp_max_roast_time):
        return sample_count - 1
    return None


def turning_point_check_candidate(
        tp_alarm_timeindex: int | None,
        charge_index: int,
        dry_index: int,
        bt_sample_count: int) -> bool:
    return (
        tp_alarm_timeindex is None and
        charge_index > -1 and
        not dry_index and
        charge_index + 8 < bt_sample_count
    )


def turning_point_temperature_is_valid(mode: str, bt_at_turning_point: float) -> bool:
    return (
        (mode == 'C' and 50 < bt_at_turning_point < 150) or
        (mode == 'F' and 100 < bt_at_turning_point < 300)
    )


def auto_drop_event_candidate(
        auto_drop_idx: int,
        auto_drop_flag: bool,
        auto_drop_enabled: bool,
        charge_index: int,
        drop_index: int,
        sample_count: int,
        mode: str,
        latest_bt: float,
        sample_times: Sequence[float]) -> bool:
    if not (
            auto_drop_idx == 0 and
            auto_drop_flag and
            auto_drop_enabled and
            charge_index > -1 and
            drop_index == 0 and
            sample_count >= 5 and
            _bt_above_event_threshold(mode, latest_bt, 160, 320)):
        return False
    return (sample_times[-1] - sample_times[charge_index]) > 7 * 60


def auto_dry_event_candidate(
        auto_dry_flag: bool,
        auto_dry_enabled: bool,
        tp_alarm_timeindex: int | None,
        charge_index: int,
        dry_index: int,
        fcs_index: int,
        latest_bt: float,
        dry_phase_temperature: float) -> bool:
    return (
        auto_dry_flag and
        auto_dry_enabled and
        bool(tp_alarm_timeindex) and
        charge_index > -1 and
        not dry_index and
        not fcs_index and
        latest_bt >= dry_phase_temperature
    )


def auto_fcs_event_candidate(
        auto_fcs_flag: bool,
        auto_fcs_enabled: bool,
        tp_alarm_timeindex: int | None,
        charge_index: int,
        fcs_index: int,
        fce_index: int,
        latest_bt: float,
        fcs_phase_temperature: float) -> bool:
    return (
        auto_fcs_flag and
        auto_fcs_enabled and
        bool(tp_alarm_timeindex) and
        charge_index > -1 and
        not fcs_index and
        not fce_index and
        latest_bt >= fcs_phase_temperature
    )


def delta_smoothing_filter_size(delta_filter: float, sample_count: int, unfiltered_count: int) -> int | None:
    if not delta_filter:
        return None
    user_filter = int(round(delta_filter / 2.))
    if user_filter and sample_count > user_filter and unfiltered_count > user_filter:
        return user_filter
    return None


def displayed_ror_value(
        rate_of_change: TemperatureValue,
        ror_limit_enabled: bool,
        max_ror_limit: float,
        ror_limit: float,
        ror_limit_min: float) -> TemperatureValue:
    if rate_of_change is None or not ror_limit_enabled:
        return rate_of_change
    lower_limit = max(-max_ror_limit, ror_limit_min)
    upper_limit = min(max_ror_limit, ror_limit)
    if not lower_limit < rate_of_change < upper_limit:
        return None
    return rate_of_change


def ror_curve_window(
        charge_index: int,
        drop_index: int,
        sample_count: int,
        delta_filter: float,
        delta_samples: int) -> tuple[int, int] | None:
    if charge_index <= -1:
        return None
    ror_end = drop_index + 1 if drop_index > 0 else sample_count
    filter_warmup = int(round(delta_filter / 2.))
    sample_warmup = max(2, delta_samples + 1)
    ror_start = max(charge_index, charge_index + filter_warmup + sample_warmup)
    return ror_start, ror_end


__all__ = [
    'alarm_is_eligible_for_evaluation',
    'alarm_source_value',
    'alarm_temperature_reaches_limit',
    'alarm_time_offset_reached',
    'auto_charge_event_candidate',
    'auto_drop_event_candidate',
    'auto_dry_event_candidate',
    'auto_fcs_event_candidate',
    'BackfillUpdate',
    'connected_curve_point',
    'ConnectedCurvePoint',
    'decay_weight_sequence',
    'delta_smoothing_filter_size',
    'displayed_ror_value',
    'input_filter_backfill_updates',
    'pid_process_value',
    'relative_alarm_index',
    'ror_curve_window',
    'smoothing_weights_for_recent_readings',
    'turning_point_check_candidate',
    'turning_point_temperature_is_valid',
    'turning_point_timeout_index',
]
