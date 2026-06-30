from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import warnings

import numpy

TemperatureValue = float | None


@dataclass(frozen=True)
class ConnectedCurvePoint:
    should_append: bool
    value: TemperatureValue


@dataclass(frozen=True)
class BackfillUpdate:
    index: int
    value: float


@dataclass(frozen=True)
class PreviousReadings:
    latest: float | None
    previous: float | None


@dataclass(frozen=True)
class AlarmTrigger:
    alarm_index: int
    state_index: int


@dataclass(frozen=True)
class AutoEventDecisions:
    charge_candidate: bool
    turning_point_timeout_index: int | None
    turning_point_check_candidate: bool
    drop_candidate: bool


@dataclass(frozen=True)
class PhaseEventDecisions:
    dry_candidate: bool
    fcs_candidate: bool


@dataclass(frozen=True)
class ProcessedSampleFrame:
    timestamp: float
    sample_count: int
    latest_et: float
    latest_bt: float
    smoothed_et: TemperatureValue
    smoothed_bt: TemperatureValue
    pid_process_value: TemperatureValue
    displayed_delta_et: TemperatureValue
    displayed_delta_bt: TemperatureValue
    delta_et_window: tuple[int, int] | None
    delta_bt_window: tuple[int, int] | None
    live_x_axis_extension_end: float | None
    events: AutoEventDecisions


@dataclass(frozen=True)
class PostSampleUpdateDecisions:
    update_auc: bool
    update_auc_guide: bool
    update_bbp_metrics: bool


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


def decay_weighted_average(
        sample_times: Sequence[float],
        temperatures: Sequence[TemperatureValue],
        decay_weights: Sequence[int] | None,
        sample_interval_seconds: float) -> float:
    if decay_weights is None or len(decay_weights) < 2 or len(sample_times) != len(temperatures):
        if temperatures and temperatures[-1] is not None:
            return temperatures[-1]
        return -1
    window_size = min(len(decay_weights), len(temperatures))
    time_trail: list[float] = []
    temperature_trail: list[float] = []
    for sample_time, temperature in zip(
            sample_times[-window_size:],
            temperatures[-window_size:],
            strict=True):
        if temperature is not None and temperature != -1:
            time_trail.append(sample_time)
            temperature_trail.append(temperature)
    if not temperature_trail:
        return -1
    valid_window_size = len(temperature_trail)
    linear_times = numpy.flip(
        numpy.arange(
            time_trail[-1],
            time_trail[-1] - valid_window_size * sample_interval_seconds,
            -sample_interval_seconds,
        ),
        axis=0,
    )
    resampled_temperatures = numpy.interp(linear_times, time_trail, temperature_trail)
    try:
        return float(numpy.average(
            resampled_temperatures[-len(decay_weights):],
            axis=0,
            weights=decay_weights[-valid_window_size:],
        ))
    except Exception: # pylint: disable=broad-except
        return float(numpy.average(numpy.array(temperature_trail)))


def post_sample_update_decisions(
        recording: bool,
        auc_guide_enabled: bool,
        charge_index: int,
        sample_count: int) -> PostSampleUpdateDecisions:
    update_auc = recording
    return PostSampleUpdateDecisions(
        update_auc=update_auc,
        update_auc_guide=update_auc and auc_guide_enabled,
        update_bbp_metrics=recording and charge_index > -1 and sample_count == charge_index + 5,
    )


def external_program_background_lookup_time(
        background_enabled: bool,
        charge_index: int,
        current_time: float,
        sample_times: Sequence[float]) -> float | None:
    if not background_enabled:
        return None
    if charge_index != -1:
        return current_time - sample_times[charge_index]
    return current_time


def external_program_output_command(
        program: str,
        latest_et: float,
        latest_bt: float,
        background_et: float,
        background_bt: float) -> str:
    return f'{program} {latest_et:.1f} {latest_bt:.1f} {background_et:.1f} {background_bt:.1f}'


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


def input_filter_previous_values(
        readings: Sequence[float],
        input_filters_enabled: bool) -> PreviousReadings:
    if not input_filters_enabled:
        return PreviousReadings(None, None)
    latest = readings[-1] if len(readings) > 0 else None
    previous = readings[-2] if len(readings) > 1 else None
    return PreviousReadings(latest, previous)


def live_x_axis_extension_end(
        fix_max_time: bool,
        lock_time_x: bool,
        charge_index: int,
        sample_times: Sequence[float],
        start_of_x: float,
        end_of_x: float) -> float | None:
    if fix_max_time or lock_time_x:
        return None
    charge_offset = 0 if charge_index == -1 else sample_times[charge_index]
    now = sample_times[-1] - charge_offset
    trigger_period = (end_of_x - start_of_x - charge_offset) / 14
    if now > (end_of_x - trigger_period):
        return now + trigger_period * 4
    return None


def manual_x_axis_extension_end(
        fix_max_time: bool,
        lock_time_x: bool,
        tx: float,
        charge_index: int,
        sample_times: Sequence[float],
        end_of_x: float) -> float | None:
    if fix_max_time or lock_time_x:
        return None
    now = tx if charge_index == -1 else tx - sample_times[charge_index]
    if now > (end_of_x - 45):
        return now + 180
    return None


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


def evaluate_alarm_triggers(
        alarm_flags: Sequence[int | bool],
        alarm_states: Sequence[int],
        alarm_guards: Sequence[int],
        alarm_negative_guards: Sequence[int],
        alarm_times: Sequence[int],
        alarm_offsets: Sequence[float],
        alarm_sources: Sequence[int],
        alarm_conditions: Sequence[int],
        alarm_temperatures: Sequence[float],
        local_flagstart: bool,
        timeindex: Sequence[int],
        tp_alarm_timeindex: int | None,
        elapsed_time: float,
        sample_timex: Sequence[float],
        sample_delta1: Sequence[TemperatureValue],
        sample_delta2: Sequence[TemperatureValue],
        sample_temp1: Sequence[float],
        sample_temp2: Sequence[float],
        sample_extratemp1: Sequence[Sequence[float]],
        sample_extratemp2: Sequence[Sequence[float]],
        extra_device_count: int,
        trigger_state_index: int) -> tuple[AlarmTrigger, ...]:
    current_states = list(alarm_states)
    state_index = max(0, trigger_state_index)
    triggers: list[AlarmTrigger] = []

    for i, aflag in enumerate(alarm_flags):
        if not _alarm_row_is_complete(
                i,
                current_states,
                alarm_guards,
                alarm_negative_guards,
                alarm_times,
                alarm_offsets,
                alarm_sources,
                alarm_conditions,
                alarm_temperatures):
            continue
        alarm_ready = False
        if alarm_is_eligible_for_evaluation(
                aflag,
                current_states[i],
                alarm_guards[i],
                alarm_negative_guards[i],
                current_states,
                alarm_times[i],
                local_flagstart,
                timeindex,
                tp_alarm_timeindex):
            if alarm_time_offset_reached(
                    alarm_offsets[i],
                    elapsed_time,
                    alarm_times[i],
                    local_flagstart,
                    sample_timex,
                    timeindex,
                    tp_alarm_timeindex,
                    current_states,
                    alarm_guards[i]):
                alarm_ready = True

            alarm_idx: int | None = None
            if alarm_times[i] == 10:
                if_alarm_state = current_states[alarm_guards[i]]
                alarm_idx = relative_alarm_index(alarm_times[i], if_alarm_state, len(sample_timex))

            alarm_temp = alarm_source_value(
                alarm_sources[i],
                alarm_index=alarm_idx,
                sample_delta1=sample_delta1,
                sample_delta2=sample_delta2,
                sample_temp1=sample_temp1,
                sample_temp2=sample_temp2,
                sample_extratemp1=sample_extratemp1,
                sample_extratemp2=sample_extratemp2,
                extra_device_count=extra_device_count,
            )
            if alarm_temperature_reaches_limit(
                    alarm_temp,
                    alarm_conditions[i],
                    alarm_temperatures[i],
                    alarm_idx):
                alarm_ready = True

        if alarm_ready:
            current_states[i] = state_index
            triggers.append(AlarmTrigger(i, state_index))

    return tuple(triggers)


def _alarm_row_is_complete(
        index: int,
        alarm_states: Sequence[int],
        alarm_guards: Sequence[int],
        alarm_negative_guards: Sequence[int],
        alarm_times: Sequence[int],
        alarm_offsets: Sequence[float],
        alarm_sources: Sequence[int],
        alarm_conditions: Sequence[int],
        alarm_temperatures: Sequence[float]) -> bool:
    return (
        index < len(alarm_states) and
        index < len(alarm_guards) and
        index < len(alarm_negative_guards) and
        index < len(alarm_times) and
        index < len(alarm_offsets) and
        index < len(alarm_sources) and
        index < len(alarm_conditions) and
        index < len(alarm_temperatures)
    )


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


def simple_rate_of_rise_per_minute(
        sample_times: Sequence[float],
        temperatures: Sequence[float],
        left_index: int,
        previous_rates: Sequence[float]) -> float:
    timed = sample_times[-1] - sample_times[-left_index]
    if temperatures[-1] != -1 and temperatures[-left_index] != -1:
        if (
                len(temperatures) >= left_index + 2 and
                2 - left_index < 0 and
                1 - left_index < 0 and
                temperatures[-left_index - 1] != -1 and
                temperatures[-left_index + 1] != -1 and
                temperatures[-left_index - 2] != -1 and
                temperatures[-left_index + 2] != -1):
            left_temperature = (
                temperatures[-left_index - 2] +
                temperatures[-left_index - 1] +
                temperatures[-left_index] +
                temperatures[-left_index + 1] +
                temperatures[-left_index + 2]
            ) / 5.
            return ((temperatures[-1] - left_temperature) / timed) * 60.
        if (
                len(temperatures) >= left_index + 1 and
                1 - left_index < 0 and
                temperatures[-left_index - 1] != -1 and
                temperatures[-left_index + 1] != -1):
            left_temperature = (
                temperatures[-left_index - 1] +
                temperatures[-left_index] +
                temperatures[-left_index + 1]
            ) / 3.
            return ((temperatures[-1] - left_temperature) / timed) * 60.
        return ((temperatures[-1] - temperatures[-left_index]) / timed) * 60.
    if previous_rates:
        return previous_rates[-1]
    return 0.


def rate_of_rise_per_minute(
        latest_temperature: float,
        sample_times: Sequence[float],
        temperatures: Sequence[float],
        previous_rates: Sequence[float],
        delta_samples: int,
        use_polyfit: bool) -> float:
    if latest_temperature == -1 or len(sample_times) < 2:
        if previous_rates:
            return previous_rates[-1]
        return 0.
    left_index = min(len(sample_times), len(temperatures), max(2, delta_samples + 1))
    if use_polyfit:
        try:
            time_vec = sample_times[-left_index:]
            temp_samples = temperatures[-left_index:]
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                ls_fit = numpy.polynomial.polynomial.polyfit(time_vec, temp_samples, 1)
                return float(ls_fit[1] * 60.)
        except Exception: # pylint: disable=broad-except
            pass
    return simple_rate_of_rise_per_minute(sample_times, temperatures, left_index, previous_rates)


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


def build_live_processed_sample_frame(
        timestamp: float,
        sample_count: int,
        latest_et: float,
        latest_bt: float,
        smoothed_et: TemperatureValue,
        smoothed_bt: TemperatureValue,
        pid_process_value: TemperatureValue,
        raw_delta_et: TemperatureValue,
        raw_delta_bt: TemperatureValue,
        ror_limit_enabled: bool,
        max_ror_limit: float,
        ror_limit: float,
        ror_limit_min: float,
        charge_index: int,
        dry_index: int,
        drop_index: int,
        delta_et_filter: float,
        delta_bt_filter: float,
        delta_et_samples: int,
        delta_bt_samples: int,
        fix_max_time: bool,
        lock_time_x: bool,
        sample_times: Sequence[float],
        start_of_x: float,
        end_of_x: float,
        tp_alarm_timeindex: int | None,
        tp_max_roast_time: float,
        auto_charge_idx: int,
        auto_charge_flag: bool,
        auto_charge_enabled: bool,
        auto_drop_idx: int,
        auto_drop_flag: bool,
        auto_drop_enabled: bool,
        mode: str,
        ) -> ProcessedSampleFrame:
    events = AutoEventDecisions(
        charge_candidate=auto_charge_event_candidate(
            auto_charge_idx,
            auto_charge_flag,
            auto_charge_enabled,
            charge_index,
            sample_count,
            mode,
            latest_bt,
        ),
        turning_point_timeout_index=turning_point_timeout_index(
            tp_alarm_timeindex,
            charge_index,
            sample_times,
            tp_max_roast_time,
            sample_count,
        ),
        turning_point_check_candidate=turning_point_check_candidate(
            tp_alarm_timeindex,
            charge_index,
            dry_index,
            sample_count,
        ),
        drop_candidate=auto_drop_event_candidate(
            auto_drop_idx,
            auto_drop_flag,
            auto_drop_enabled,
            charge_index,
            drop_index,
            sample_count,
            mode,
            latest_bt,
            sample_times,
        ),
    )
    return ProcessedSampleFrame(
        timestamp=timestamp,
        sample_count=sample_count,
        latest_et=latest_et,
        latest_bt=latest_bt,
        smoothed_et=smoothed_et,
        smoothed_bt=smoothed_bt,
        pid_process_value=pid_process_value,
        displayed_delta_et=displayed_ror_value(
            raw_delta_et,
            ror_limit_enabled,
            max_ror_limit,
            ror_limit,
            ror_limit_min,
        ),
        displayed_delta_bt=displayed_ror_value(
            raw_delta_bt,
            ror_limit_enabled,
            max_ror_limit,
            ror_limit,
            ror_limit_min,
        ),
        delta_et_window=ror_curve_window(
            charge_index,
            drop_index,
            sample_count,
            delta_et_filter,
            delta_et_samples,
        ),
        delta_bt_window=ror_curve_window(
            charge_index,
            drop_index,
            sample_count,
            delta_bt_filter,
            delta_bt_samples,
        ),
        live_x_axis_extension_end=live_x_axis_extension_end(
            fix_max_time,
            lock_time_x,
            charge_index,
            sample_times,
            start_of_x,
            end_of_x,
        ),
        events=events,
    )


def phase_event_candidates_after_turning_point(
        auto_dry_flag: bool,
        auto_dry_enabled: bool,
        auto_fcs_flag: bool,
        auto_fcs_enabled: bool,
        tp_alarm_timeindex: int | None,
        charge_index: int,
        dry_index: int,
        fcs_index: int,
        fce_index: int,
        latest_bt: float,
        dry_phase_temperature: float,
        fcs_phase_temperature: float) -> PhaseEventDecisions:
    return PhaseEventDecisions(
        dry_candidate=auto_dry_event_candidate(
            auto_dry_flag,
            auto_dry_enabled,
            tp_alarm_timeindex,
            charge_index,
            dry_index,
            fcs_index,
            latest_bt,
            dry_phase_temperature,
        ),
        fcs_candidate=auto_fcs_event_candidate(
            auto_fcs_flag,
            auto_fcs_enabled,
            tp_alarm_timeindex,
            charge_index,
            fcs_index,
            fce_index,
            latest_bt,
            fcs_phase_temperature,
        ),
    )


__all__ = [
    'alarm_is_eligible_for_evaluation',
    'alarm_source_value',
    'alarm_temperature_reaches_limit',
    'alarm_time_offset_reached',
    'AlarmTrigger',
    'AutoEventDecisions',
    'auto_charge_event_candidate',
    'auto_drop_event_candidate',
    'auto_dry_event_candidate',
    'auto_fcs_event_candidate',
    'BackfillUpdate',
    'build_live_processed_sample_frame',
    'connected_curve_point',
    'ConnectedCurvePoint',
    'decay_weight_sequence',
    'decay_weighted_average',
    'delta_smoothing_filter_size',
    'displayed_ror_value',
    'evaluate_alarm_triggers',
    'external_program_background_lookup_time',
    'external_program_output_command',
    'input_filter_backfill_updates',
    'input_filter_previous_values',
    'live_x_axis_extension_end',
    'manual_x_axis_extension_end',
    'PhaseEventDecisions',
    'phase_event_candidates_after_turning_point',
    'pid_process_value',
    'post_sample_update_decisions',
    'PostSampleUpdateDecisions',
    'PreviousReadings',
    'ProcessedSampleFrame',
    'rate_of_rise_per_minute',
    'relative_alarm_index',
    'ror_curve_window',
    'simple_rate_of_rise_per_minute',
    'smoothing_weights_for_recent_readings',
    'turning_point_check_candidate',
    'turning_point_temperature_is_valid',
    'turning_point_timeout_index',
]
