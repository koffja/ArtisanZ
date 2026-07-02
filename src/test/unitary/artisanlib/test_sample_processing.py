from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import FrozenInstanceError

import pytest
import numpy

from artisanlib.sample_processing import (
    _alarm_row_is_complete,
    _bt_above_event_threshold,
    _relative_latest_value,
    alarm_is_eligible_for_evaluation,
    alarm_source_value,
    alarm_temperature_reaches_limit,
    alarm_time_offset_reached,
    evaluate_alarm_triggers,
    auto_charge_event_candidate,
    auto_drop_event_candidate,
    auto_dry_event_candidate,
    auto_fcs_event_candidate,
    build_live_processed_sample_frame,
    connected_curve_point,
    decay_weight_sequence,
    decay_weighted_average,
    delta_smoothing_filter_size,
    displayed_ror_value,
    extra_device_length_error_message,
    external_program_background_lookup_time,
    external_program_output_command,
    full_curve_data,
    input_filter_backfill_updates,
    input_filter_previous_values,
    input_filter_result,
    live_x_axis_extension_end,
    manual_turning_point_check_candidate,
    manual_x_axis_extension_end,
    phase_event_candidates_after_turning_point,
    pid_process_value,
    pid_process_value_update_enabled,
    pid_set_value_update,
    pid_sv_update_target,
    post_sample_update_decisions,
    relative_alarm_index,
    ror_curve_window,
    rate_of_rise_per_minute,
    smoothed_rate_of_change_value,
    smoothed_temperature_value,
    smoothing_weights_for_recent_readings,
    simple_rate_of_rise_per_minute,
    turning_point_check_candidate,
    turning_point_temperature_is_valid,
    turning_point_timeout_index,
    windowed_curve_data,
    AlarmTrigger,
    AutoEventDecisions,
    BackfillUpdate,
    ConnectedCurvePoint,
    CurveWindowData,
    InputFilterResult,
    PhaseEventDecisions,
    PidSvUpdateTarget,
    PostSampleUpdateDecisions,
    PreviousReadings,
    ProcessedSampleFrame,
)


class ExplodingSequence(Sequence[float]):
    def __getitem__(self, index: int) -> float:
        raise AssertionError(f'unexpected sample time access at {index}')

    def __len__(self) -> int:
        return 10

    def __iter__(self) -> Iterator[float]:
        raise AssertionError('unexpected sample time iteration')


class NoAccessSequence(Sequence[float]):
    def __getitem__(self, index: int) -> float:
        raise AssertionError(f'unexpected sequence item access at {index}')

    def __len__(self) -> int:
        raise AssertionError('unexpected sequence length access')

    def __iter__(self) -> Iterator[float]:
        raise AssertionError('unexpected sequence iteration')


def test_decay_weight_sequence_uses_one_based_linear_weights() -> None:
    assert decay_weight_sequence(4) == (1, 2, 3, 4)


def test_decay_weight_sequence_falls_back_for_invalid_curve_filter() -> None:
    assert decay_weight_sequence(0) == (1,)
    assert decay_weight_sequence(-3) == (1,)


def test_smoothing_weights_use_decay_weights_when_recent_window_has_no_dropout() -> None:
    assert smoothing_weights_for_recent_readings([100.0, 101.0, 102.0], (1, 2), 2) == (1, 2)


def test_smoothing_weights_disable_smoothing_when_recent_window_has_dropout() -> None:
    assert smoothing_weights_for_recent_readings([100.0, -1.0, 102.0], (1, 2), 2) == (1,)


def test_smoothing_weights_keep_decay_weights_for_empty_readings() -> None:
    assert smoothing_weights_for_recent_readings([], (1, 2), 2) == (1, 2)


def test_decay_weighted_average_falls_back_to_latest_without_usable_weights() -> None:
    assert decay_weighted_average(
        sample_times=[0.0, 1.0],
        temperatures=[10.0, 12.0],
        decay_weights=None,
        sample_interval_seconds=1.0,
    ) == 12.0
    assert decay_weighted_average(
        sample_times=[0.0, 1.0],
        temperatures=[10.0, None],
        decay_weights=None,
        sample_interval_seconds=1.0,
    ) == -1


def test_decay_weighted_average_skips_dropouts_and_uses_legacy_resampling() -> None:
    assert decay_weighted_average(
        sample_times=[0.0, 1.0, 2.0],
        temperatures=[10.0, None, 30.0],
        decay_weights=[1, 2, 3],
        sample_interval_seconds=1.0,
    ) == pytest.approx(26.0)


def test_decay_weighted_average_returns_negative_one_without_valid_values() -> None:
    assert decay_weighted_average(
        sample_times=[0.0, 1.0],
        temperatures=[None, -1.0],
        decay_weights=[1, 2],
        sample_interval_seconds=1.0,
    ) == -1


def test_smoothed_temperature_value_returns_negative_one_without_connected_values() -> None:
    assert smoothed_temperature_value(
        sample_times=[],
        connected_temperatures=[],
        decay_weights=[1, 2],
        sample_interval_seconds=1.0,
    ) == -1


def test_smoothed_temperature_value_falls_back_to_latest_without_usable_weights() -> None:
    assert smoothed_temperature_value(
        sample_times=[0.0, 1.0],
        connected_temperatures=[10.0, 12.0],
        decay_weights=None,
        sample_interval_seconds=1.0,
    ) == 12.0


def test_smoothed_temperature_value_uses_decay_weighted_average_for_connected_values() -> None:
    assert smoothed_temperature_value(
        sample_times=[0.0, 1.0, 2.0],
        connected_temperatures=[10.0, None, 30.0],
        decay_weights=[1, 2, 3],
        sample_interval_seconds=1.0,
    ) == pytest.approx(26.0)


def test_post_sample_update_decisions_skip_all_work_outside_recording() -> None:
    decisions = post_sample_update_decisions(
        recording=False,
        auc_guide_enabled=True,
        charge_index=2,
        sample_count=7,
    )

    assert not decisions.update_auc
    assert not decisions.update_auc_guide
    assert not decisions.update_bbp_metrics


def test_post_sample_update_decisions_follow_auc_guide_flag_during_recording() -> None:
    decisions = post_sample_update_decisions(
        recording=True,
        auc_guide_enabled=True,
        charge_index=-1,
        sample_count=4,
    )

    assert decisions.update_auc
    assert decisions.update_auc_guide
    assert not decisions.update_bbp_metrics

    decisions = post_sample_update_decisions(
        recording=True,
        auc_guide_enabled=False,
        charge_index=-1,
        sample_count=4,
    )

    assert decisions.update_auc
    assert not decisions.update_auc_guide
    assert not decisions.update_bbp_metrics


def test_post_sample_update_decisions_trigger_bbp_at_fifth_sample_after_charge() -> None:
    assert post_sample_update_decisions(
        recording=True,
        auc_guide_enabled=False,
        charge_index=3,
        sample_count=8,
    ).update_bbp_metrics
    assert not post_sample_update_decisions(
        recording=True,
        auc_guide_enabled=False,
        charge_index=3,
        sample_count=7,
    ).update_bbp_metrics
    assert not post_sample_update_decisions(
        recording=True,
        auc_guide_enabled=False,
        charge_index=-1,
        sample_count=4,
    ).update_bbp_metrics


def test_pid_set_value_update_skips_none_or_unchanged_values() -> None:
    assert pid_set_value_update(calculated_sv=None, current_sv=120.0) is None
    assert pid_set_value_update(calculated_sv=120.0, current_sv=120.0) is None


def test_pid_set_value_update_returns_changed_positive_value() -> None:
    assert pid_set_value_update(calculated_sv=125.5, current_sv=120.0) == 125.5
    assert pid_set_value_update(calculated_sv=125.5, current_sv=None) == 125.5


def test_pid_set_value_update_clamps_negative_value_after_raw_comparison() -> None:
    assert pid_set_value_update(calculated_sv=-2.5, current_sv=120.0) == 0.0
    assert pid_set_value_update(calculated_sv=-2.5, current_sv=0.0) == 0.0


def test_pid_sv_update_target_skips_when_sampling_is_off() -> None:
    assert pid_sv_update_target(
        sampling=False,
        device=0,
        fuji_follow_background=True,
        recording=True,
        pid_active=True,
        sv_mode=2,
    ) is None


def test_pid_sv_update_target_selects_fuji_only_for_recording_fuji_background_follow() -> None:
    assert pid_sv_update_target(
        sampling=True,
        device=0,
        fuji_follow_background=True,
        recording=True,
        pid_active=False,
        sv_mode=0,
    ) is PidSvUpdateTarget.FUJI

    assert pid_sv_update_target(
        sampling=True,
        device=0,
        fuji_follow_background=True,
        recording=False,
        pid_active=False,
        sv_mode=0,
    ) is None


def test_pid_sv_update_target_preserves_fuji_priority_over_software_pid() -> None:
    assert pid_sv_update_target(
        sampling=True,
        device=0,
        fuji_follow_background=True,
        recording=True,
        pid_active=True,
        sv_mode=2,
    ) is PidSvUpdateTarget.FUJI


def test_pid_sv_update_target_can_select_fuji_without_software_pid_state() -> None:
    assert pid_sv_update_target(
        sampling=True,
        device=0,
        fuji_follow_background=True,
        recording=True,
    ) is PidSvUpdateTarget.FUJI

    assert pid_sv_update_target(
        sampling=True,
        device=11,
        fuji_follow_background=False,
        recording=True,
    ) is None


def test_pid_sv_update_target_selects_software_pid_for_active_ramp_or_background_follow() -> None:
    assert pid_sv_update_target(
        sampling=True,
        device=11,
        fuji_follow_background=False,
        recording=True,
        pid_active=True,
        sv_mode=1,
    ) is PidSvUpdateTarget.SOFTWARE

    assert pid_sv_update_target(
        sampling=True,
        device=11,
        fuji_follow_background=False,
        recording=False,
        pid_active=False,
        sv_mode=2,
    ) is PidSvUpdateTarget.SOFTWARE


def test_pid_sv_update_target_rejects_inactive_ramp_mode_and_manual_mode() -> None:
    assert pid_sv_update_target(
        sampling=True,
        device=11,
        fuji_follow_background=False,
        recording=True,
        pid_active=False,
        sv_mode=1,
    ) is None

    assert pid_sv_update_target(
        sampling=True,
        device=11,
        fuji_follow_background=False,
        recording=True,
        pid_active=True,
        sv_mode=0,
    ) is None


def test_external_program_background_lookup_time_skips_when_background_disabled() -> None:
    assert external_program_background_lookup_time(
        background_enabled=False,
        charge_index=2,
        current_time=240.0,
        sample_times=[0.0, 60.0, 120.0],
    ) is None


def test_external_program_background_lookup_time_uses_current_time_before_charge() -> None:
    assert external_program_background_lookup_time(
        background_enabled=True,
        charge_index=-1,
        current_time=240.0,
        sample_times=[0.0, 60.0, 120.0],
    ) == 240.0


def test_external_program_background_lookup_time_subtracts_charge_time_after_charge() -> None:
    assert external_program_background_lookup_time(
        background_enabled=True,
        charge_index=2,
        current_time=300.0,
        sample_times=[0.0, 60.0, 120.0],
    ) == 180.0


def test_external_program_output_command_formats_live_and_background_values() -> None:
    assert external_program_output_command(
        program='log-temperatures',
        latest_et=181.24,
        latest_bt=202.86,
        background_et=150.04,
        background_bt=160.05,
    ) == 'log-temperatures 181.2 202.9 150.0 160.1'
    assert external_program_output_command(
        program='log-temperatures',
        latest_et=181.24,
        latest_bt=202.86,
        background_et=-1.0,
        background_bt=-1.0,
    ) == 'log-temperatures 181.2 202.9 -1.0 -1.0'


def test_extra_device_length_error_message_returns_none_for_matching_buffers() -> None:
    assert extra_device_length_error_message(
        extra_serial_count=2,
        extra_device_count=2,
        extra_temp_count=2,
    ) is None


def test_extra_device_length_error_message_identifies_near_mismatch_location() -> None:
    assert extra_device_length_error_message(
        extra_serial_count=1,
        extra_device_count=2,
        extra_temp_count=2,
    ) == 'ERROR: length of Extra-Serial (=1) does not have the necessary length (=2)\nPlease Reset: Extra devices'

    assert extra_device_length_error_message(
        extra_serial_count=2,
        extra_device_count=2,
        extra_temp_count=3,
    ) == 'ERROR: length of Extra-Temp (=3) does not have the necessary length (=2)\nPlease Reset: Extra devices'


def test_extra_device_length_error_message_prefers_minus_one_mismatch_before_plus_one() -> None:
    assert extra_device_length_error_message(
        extra_serial_count=3,
        extra_device_count=2,
        extra_temp_count=1,
    ) == 'ERROR: length of Extra-Temp (=1) does not have the necessary length (=2)\nPlease Reset: Extra devices'


def test_extra_device_length_error_message_reports_general_mismatch_when_location_is_unclear() -> None:
    assert extra_device_length_error_message(
        extra_serial_count=0,
        extra_device_count=2,
        extra_temp_count=4,
    ) == "ERROR: extra devices lengths don't match: Extra-Serial= 0 Extra-Devices= 2 Extra-Temp= 4\nPlease Reset: Extra devices"


def test_connected_curve_point_appends_valid_reading() -> None:
    point = connected_curve_point(181.5, [178.0, 181.5], interpolate_max=2)

    assert point.should_append
    assert point.value == 181.5


def test_connected_curve_point_skips_short_dropout_gap() -> None:
    point = connected_curve_point(-1.0, [178.0, -1.0, -1.0], interpolate_max=2)

    assert not point.should_append
    assert point.value is None


def test_connected_curve_point_appends_disconnect_marker_after_long_dropout_gap() -> None:
    point = connected_curve_point(-1.0, [178.0, -1.0, -1.0, -1.0], interpolate_max=2)

    assert point.should_append
    assert point.value is None


def test_connected_curve_point_matches_post_append_readings_semantics() -> None:
    assert connected_curve_point(-1.0, [100.0, -1.0, -1.0], interpolate_max=1).should_append
    assert not connected_curve_point(-1.0, [-1.0, -1.0], interpolate_max=1).should_append


def test_input_filter_backfill_updates_latest_matching_connected_sample() -> None:
    updates = input_filter_backfill_updates(
        connected_times=[10.0],
        raw_times=[10.0],
        raw_values=[181.0],
        previous_latest=180.0,
        previous_previous=None,
    )

    assert [(update.index, update.value) for update in updates] == [(-1, 181.0)]


def test_input_filter_backfill_updates_previous_matching_connected_sample() -> None:
    updates = input_filter_backfill_updates(
        connected_times=[5.0, 10.0],
        raw_times=[5.0, 10.0],
        raw_values=[176.5, 181.0],
        previous_latest=181.0,
        previous_previous=176.0,
    )

    assert [(update.index, update.value) for update in updates] == [(-2, 176.5)]


def test_input_filter_backfill_updates_latest_and_previous_samples_in_order() -> None:
    updates = input_filter_backfill_updates(
        connected_times=[5.0, 10.0],
        raw_times=[5.0, 10.0],
        raw_values=[176.5, 181.5],
        previous_latest=181.0,
        previous_previous=176.0,
    )

    assert [(update.index, update.value) for update in updates] == [(-1, 181.5), (-2, 176.5)]


def test_input_filter_backfill_updates_skip_timestamp_mismatches() -> None:
    updates = input_filter_backfill_updates(
        connected_times=[4.0, 9.0],
        raw_times=[5.0, 10.0],
        raw_values=[176.5, 181.5],
        previous_latest=181.0,
        previous_previous=176.0,
    )

    assert updates == ()


def test_input_filter_backfill_updates_skip_unchanged_or_missing_previous_values() -> None:
    assert input_filter_backfill_updates(
        connected_times=[5.0, 10.0],
        raw_times=[5.0, 10.0],
        raw_values=[176.0, 181.0],
        previous_latest=181.0,
        previous_previous=176.0,
    ) == ()
    assert input_filter_backfill_updates(
        connected_times=[5.0, 10.0],
        raw_times=[5.0, 10.0],
        raw_values=[176.5, 181.5],
        previous_latest=None,
        previous_previous=None,
    ) == ()


def test_input_filter_previous_values_skip_sequence_access_when_disabled() -> None:
    previous = input_filter_previous_values(NoAccessSequence(), input_filters_enabled=False)

    assert previous.latest is None
    assert previous.previous is None


def test_input_filter_previous_values_return_empty_snapshot_for_no_readings() -> None:
    previous = input_filter_previous_values([], input_filters_enabled=True)

    assert previous.latest is None
    assert previous.previous is None


def test_input_filter_previous_values_return_latest_for_single_reading() -> None:
    previous = input_filter_previous_values([181.0], input_filters_enabled=True)

    assert previous.latest == 181.0
    assert previous.previous is None


def test_input_filter_previous_values_return_latest_and_previous_readings() -> None:
    previous = input_filter_previous_values([176.0, 181.0], input_filters_enabled=True)

    assert previous.latest == 181.0
    assert previous.previous == 176.0


def test_input_filter_result_repeats_latest_for_duplicate_reading() -> None:
    result = input_filter_result(
        sample_times=[0.0],
        temperatures=[150.0],
        current_time=1.0,
        current_temperature=150.2,
        is_bt=False,
        drop_duplicates=True,
        drop_duplicates_limit=0.54,
        minmax_limits=False,
        min_temperature=0.0,
        max_temperature=300.0,
        drop_spikes=False,
        auto_charge_flag=False,
        charge_index=-1,
        spike_period=3,
        spike_dror_limit=4.0,
    )

    assert result.value == 150.0
    assert result.backfill_updates == ()


def test_input_filter_result_returns_negative_one_for_repeated_minmax_violation() -> None:
    result = input_filter_result(
        sample_times=[0.0, 1.0, 2.0],
        temperatures=[150.0, 150.0, 150.0],
        current_time=3.0,
        current_temperature=999.0,
        is_bt=False,
        drop_duplicates=False,
        drop_duplicates_limit=0.54,
        minmax_limits=True,
        min_temperature=0.0,
        max_temperature=300.0,
        drop_spikes=False,
        auto_charge_flag=False,
        charge_index=-1,
        spike_period=3,
        spike_dror_limit=4.0,
    )

    assert result.value == -1
    assert result.backfill_updates == ()


def test_input_filter_result_passes_through_when_filters_are_disabled() -> None:
    result = input_filter_result(
        sample_times=[0.0, 1.0],
        temperatures=[150.0, 150.0],
        current_time=2.0,
        current_temperature=170.0,
        is_bt=False,
        drop_duplicates=False,
        drop_duplicates_limit=0.54,
        minmax_limits=False,
        min_temperature=0.0,
        max_temperature=300.0,
        drop_spikes=False,
        auto_charge_flag=False,
        charge_index=-1,
        spike_period=3,
        spike_dror_limit=4.0,
    )

    assert result.value == 170.0
    assert result.backfill_updates == ()


def test_input_filter_result_returns_single_backfill_for_previous_repeated_reading() -> None:
    result = input_filter_result(
        sample_times=[0.0, 1.0],
        temperatures=[150.0, 150.0],
        current_time=2.0,
        current_temperature=156.0,
        is_bt=False,
        drop_duplicates=False,
        drop_duplicates_limit=0.54,
        minmax_limits=True,
        min_temperature=0.0,
        max_temperature=300.0,
        drop_spikes=False,
        auto_charge_flag=False,
        charge_index=-1,
        spike_period=3,
        spike_dror_limit=4.0,
    )

    assert result.value == 156.0
    assert result.backfill_updates == (BackfillUpdate(1, 153.0),)


def test_input_filter_result_returns_two_backfills_for_three_repeated_readings() -> None:
    result = input_filter_result(
        sample_times=[0.0, 1.0, 2.0],
        temperatures=[150.0, 150.0, 150.0],
        current_time=3.0,
        current_temperature=156.0,
        is_bt=False,
        drop_duplicates=False,
        drop_duplicates_limit=0.54,
        minmax_limits=True,
        min_temperature=0.0,
        max_temperature=300.0,
        drop_spikes=False,
        auto_charge_flag=False,
        charge_index=-1,
        spike_period=3,
        spike_dror_limit=4.0,
    )

    assert result.value == 156.0
    assert result.backfill_updates == (
        BackfillUpdate(2, 154.0),
        BackfillUpdate(1, 152.0),
    )


def test_live_x_axis_extension_skips_sample_time_access_when_fixed_or_locked() -> None:
    assert live_x_axis_extension_end(
        fix_max_time=True,
        lock_time_x=False,
        charge_index=-1,
        sample_times=NoAccessSequence(),
        start_of_x=0.0,
        end_of_x=600.0,
    ) is None
    assert live_x_axis_extension_end(
        fix_max_time=False,
        lock_time_x=True,
        charge_index=-1,
        sample_times=NoAccessSequence(),
        start_of_x=0.0,
        end_of_x=600.0,
    ) is None


def test_live_x_axis_extension_returns_none_before_trigger() -> None:
    assert live_x_axis_extension_end(
        fix_max_time=False,
        lock_time_x=False,
        charge_index=-1,
        sample_times=[0.0, 550.0],
        start_of_x=0.0,
        end_of_x=600.0,
    ) is None


def test_live_x_axis_extension_uses_strict_trigger_boundary() -> None:
    assert live_x_axis_extension_end(
        fix_max_time=False,
        lock_time_x=False,
        charge_index=-1,
        sample_times=[0.0, 560.0],
        start_of_x=0.0,
        end_of_x=640.0,
    ) is None


def test_live_x_axis_extension_uses_charge_offset_and_trigger_period() -> None:
    assert live_x_axis_extension_end(
        fix_max_time=False,
        lock_time_x=False,
        charge_index=1,
        sample_times=[0.0, 100.0, 721.0],
        start_of_x=0.0,
        end_of_x=660.0,
    ) == 781.0


def test_manual_x_axis_extension_skips_sample_time_access_when_fixed_or_locked() -> None:
    assert manual_x_axis_extension_end(
        fix_max_time=True,
        lock_time_x=False,
        tx=590.0,
        charge_index=-1,
        sample_times=NoAccessSequence(),
        end_of_x=600.0,
    ) is None
    assert manual_x_axis_extension_end(
        fix_max_time=False,
        lock_time_x=True,
        tx=590.0,
        charge_index=-1,
        sample_times=NoAccessSequence(),
        end_of_x=600.0,
    ) is None


def test_manual_x_axis_extension_returns_none_before_threshold() -> None:
    assert manual_x_axis_extension_end(
        fix_max_time=False,
        lock_time_x=False,
        tx=555.0,
        charge_index=-1,
        sample_times=[0.0],
        end_of_x=600.0,
    ) is None


def test_manual_x_axis_extension_uses_charge_offset_and_extension_period() -> None:
    assert manual_x_axis_extension_end(
        fix_max_time=False,
        lock_time_x=False,
        tx=662.0,
        charge_index=1,
        sample_times=[0.0, 100.0],
        end_of_x=600.0,
    ) == 742.0


def test_manual_turning_point_check_candidate_requires_recording_charge_and_missing_tp() -> None:
    assert not manual_turning_point_check_candidate(
        recording=False,
        tp_alarm_timeindex=None,
        charge_index=2,
        sample_count=8,
    )
    assert not manual_turning_point_check_candidate(
        recording=True,
        tp_alarm_timeindex=5,
        charge_index=2,
        sample_count=8,
    )
    assert not manual_turning_point_check_candidate(
        recording=True,
        tp_alarm_timeindex=None,
        charge_index=-1,
        sample_count=8,
    )


def test_manual_turning_point_check_candidate_uses_strict_five_sample_gap_after_charge() -> None:
    assert not manual_turning_point_check_candidate(
        recording=True,
        tp_alarm_timeindex=None,
        charge_index=2,
        sample_count=7,
    )
    assert manual_turning_point_check_candidate(
        recording=True,
        tp_alarm_timeindex=None,
        charge_index=2,
        sample_count=8,
    )


def test_pid_process_value_uses_smoothed_bt_for_default_sources() -> None:
    assert pid_process_value(0, smoothed_et=181.0, smoothed_bt=202.5, extra_temps_1=[], extra_temps_2=[]) == 202.5
    assert pid_process_value(1, smoothed_et=181.0, smoothed_bt=203.5, extra_temps_1=[], extra_temps_2=[]) == 203.5


def test_pid_process_value_update_enabled_requires_control_button() -> None:
    assert not pid_process_value_update_enabled(
        control_button_enabled=False,
        external_pid_controller=None,
    )
    assert not pid_process_value_update_enabled(
        control_button_enabled=False,
        external_pid_controller=0,
    )


def test_pid_process_value_update_enabled_rejects_external_pid_control() -> None:
    assert pid_process_value_update_enabled(
        control_button_enabled=True,
        external_pid_controller=0,
    )
    for controller_code in (1, 2, 3, 4):
        assert not pid_process_value_update_enabled(
            control_button_enabled=True,
            external_pid_controller=controller_code,
        )


def test_pid_process_value_update_enabled_rejects_missing_external_pid_state() -> None:
    assert not pid_process_value_update_enabled(
        control_button_enabled=True,
        external_pid_controller=None,
    )


def test_pid_process_value_uses_smoothed_et_for_source_two() -> None:
    assert pid_process_value(2, smoothed_et=178.25, smoothed_bt=205.0, extra_temps_1=[], extra_temps_2=[]) == 178.25


def test_pid_process_value_uses_extra_device_channel_one_for_odd_numbered_extra_source() -> None:
    assert pid_process_value(
        3,
        smoothed_et=178.25,
        smoothed_bt=205.0,
        extra_temps_1=[[151.0], [162.0]],
        extra_temps_2=[[251.0], [262.0]],
    ) == 151.0
    assert pid_process_value(
        5,
        smoothed_et=178.25,
        smoothed_bt=205.0,
        extra_temps_1=[[151.0], [162.0]],
        extra_temps_2=[[251.0], [262.0]],
    ) == 162.0


def test_pid_process_value_uses_extra_device_channel_two_for_even_numbered_extra_source() -> None:
    assert pid_process_value(
        4,
        smoothed_et=178.25,
        smoothed_bt=205.0,
        extra_temps_1=[[151.0], [162.0]],
        extra_temps_2=[[251.0], [262.0]],
    ) == 251.0
    assert pid_process_value(
        6,
        smoothed_et=178.25,
        smoothed_bt=205.0,
        extra_temps_1=[[151.0], [162.0]],
        extra_temps_2=[[251.0], [262.0]],
    ) == 262.0


def test_pid_process_value_falls_back_when_extra_source_is_missing() -> None:
    assert pid_process_value(
        9,
        smoothed_et=178.25,
        smoothed_bt=205.0,
        extra_temps_1=[[151.0]],
        extra_temps_2=[[251.0]],
    ) == 0.0


def test_relative_alarm_index_ignores_non_if_alarms() -> None:
    assert relative_alarm_index(alarm_time=0, if_alarm_state=4, sample_count=10) is None


def test_relative_alarm_index_uses_if_alarm_trigger_sample() -> None:
    assert relative_alarm_index(alarm_time=10, if_alarm_state=4, sample_count=10) == 4


def test_relative_alarm_index_uses_existing_end_fallback_when_trigger_is_outside_window() -> None:
    assert relative_alarm_index(alarm_time=10, if_alarm_state=12, sample_count=10) == -1


def test_alarm_source_value_returns_delta_sources() -> None:
    assert alarm_source_value(
        -2,
        alarm_index=None,
        sample_delta1=[1.0, 2.5],
        sample_delta2=[3.0, 4.5],
        sample_temp1=[150.0, 160.0],
        sample_temp2=[170.0, 180.0],
        sample_extratemp1=[],
        sample_extratemp2=[],
        extra_device_count=0,
    ) == 2.5
    assert alarm_source_value(
        -1,
        alarm_index=0,
        sample_delta1=[1.0, 2.5],
        sample_delta2=[3.0, 4.5],
        sample_temp1=[150.0, 160.0],
        sample_temp2=[170.0, 180.0],
        sample_extratemp1=[],
        sample_extratemp2=[],
        extra_device_count=0,
    ) == 1.5


def test_alarm_source_value_returns_temperature_sources() -> None:
    assert alarm_source_value(
        0,
        alarm_index=0,
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[150.0, 160.0],
        sample_temp2=[170.0, 180.0],
        sample_extratemp1=[],
        sample_extratemp2=[],
        extra_device_count=0,
    ) == 10.0
    assert alarm_source_value(
        1,
        alarm_index=None,
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[150.0, 160.0],
        sample_temp2=[170.0, 180.0],
        sample_extratemp1=[],
        sample_extratemp2=[],
        extra_device_count=0,
    ) == 180.0


def test_alarm_source_value_returns_extra_device_sources() -> None:
    assert alarm_source_value(
        2,
        alarm_index=0,
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[],
        sample_temp2=[],
        sample_extratemp1=[[151.0, 161.0]],
        sample_extratemp2=[[251.0, 261.0]],
        extra_device_count=1,
    ) == 10.0
    assert alarm_source_value(
        3,
        alarm_index=None,
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[],
        sample_temp2=[],
        sample_extratemp1=[[151.0, 161.0]],
        sample_extratemp2=[[251.0, 261.0]],
        extra_device_count=1,
    ) == 261.0
    assert alarm_source_value(
        4,
        alarm_index=None,
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[],
        sample_temp2=[],
        sample_extratemp1=[[151.0, 161.0], [171.0, 181.0]],
        sample_extratemp2=[[251.0, 261.0], [271.0, 281.0]],
        extra_device_count=2,
    ) == 181.0
    assert alarm_source_value(
        5,
        alarm_index=None,
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[],
        sample_temp2=[],
        sample_extratemp1=[[151.0, 161.0], [171.0, 181.0]],
        sample_extratemp2=[[251.0, 261.0], [271.0, 281.0]],
        extra_device_count=2,
    ) == 281.0


def test_alarm_source_value_returns_none_for_missing_sources() -> None:
    assert alarm_source_value(
        4,
        alarm_index=None,
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[],
        sample_temp2=[],
        sample_extratemp1=[[151.0]],
        sample_extratemp2=[[251.0]],
        extra_device_count=1,
    ) is None
    assert alarm_source_value(
        -2,
        alarm_index=None,
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[],
        sample_temp2=[],
        sample_extratemp1=[],
        sample_extratemp2=[],
        extra_device_count=0,
    ) is None


def test_alarm_source_value_keeps_latest_delta_when_relative_baseline_is_none() -> None:
    assert alarm_source_value(
        -2,
        alarm_index=0,
        sample_delta1=[None, 2.5],
        sample_delta2=[],
        sample_temp1=[],
        sample_temp2=[],
        sample_extratemp1=[],
        sample_extratemp2=[],
        extra_device_count=0,
    ) == 2.5


def test_alarm_temperature_reaches_limit_for_standard_conditions() -> None:
    assert alarm_temperature_reaches_limit(181.0, alarm_cond=1, alarm_limit=180.0, alarm_index=None)
    assert alarm_temperature_reaches_limit(179.0, alarm_cond=0, alarm_limit=180.0, alarm_index=None)
    assert alarm_temperature_reaches_limit(180.0, alarm_cond=2, alarm_limit=180.0, alarm_index=None)
    assert alarm_temperature_reaches_limit(181.0, alarm_cond=3, alarm_limit=180.0, alarm_index=None)


def test_alarm_temperature_reaches_limit_includes_relative_equality() -> None:
    assert alarm_temperature_reaches_limit(180.0, alarm_cond=1, alarm_limit=180.0, alarm_index=0)


def test_alarm_temperature_reaches_limit_rejects_missing_and_dropout_values() -> None:
    assert not alarm_temperature_reaches_limit(None, alarm_cond=1, alarm_limit=180.0, alarm_index=None)
    assert not alarm_temperature_reaches_limit(-1.0, alarm_cond=1, alarm_limit=180.0, alarm_index=None)
    assert not alarm_temperature_reaches_limit(179.0, alarm_cond=1, alarm_limit=180.0, alarm_index=None)


def test_alarm_is_eligible_requires_active_and_untriggered_alarm() -> None:
    assert not alarm_is_eligible_for_evaluation(
        aflag=False,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=[],
        alarm_time=9,
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=3,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=[],
        alarm_time=9,
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )


def test_alarm_is_eligible_applies_positive_and_negative_guards() -> None:
    alarm_states = [-1, 4]
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=0,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=9,
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=1,
        alarm_states=alarm_states,
        alarm_time=9,
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=1,
        alarm_negative_guard=0,
        alarm_states=alarm_states,
        alarm_time=9,
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )


def test_alarm_is_eligible_applies_alarm_time_gates() -> None:
    alarm_states = [-1]
    assert alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=9,
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=-1,
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=-1,
        local_flagstart=True,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=0,
        local_flagstart=True,
        timeindex=[3, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=2,
        local_flagstart=True,
        timeindex=[3, 0, 5],
        tp_alarm_timeindex=None,
    )
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=8,
        local_flagstart=True,
        timeindex=[3, 0, 5],
        tp_alarm_timeindex=None,
    )
    assert alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=8,
        local_flagstart=True,
        timeindex=[3, 0, 5],
        tp_alarm_timeindex=7,
    )


def test_alarm_is_eligible_for_if_alarm_requires_guard() -> None:
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=[4],
        alarm_time=10,
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=0,
        alarm_negative_guard=-1,
        alarm_states=[4],
        alarm_time=10,
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )


def test_alarm_is_eligible_rejects_missing_event_boundaries() -> None:
    alarm_states = [-1]
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=0,
        local_flagstart=True,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=2,
        local_flagstart=True,
        timeindex=[3, 0, 0],
        tp_alarm_timeindex=None,
    )
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=8,
        local_flagstart=False,
        timeindex=[3, 0, 0],
        tp_alarm_timeindex=7,
    )
    assert not alarm_is_eligible_for_evaluation(
        aflag=True,
        alarm_state=-1,
        alarm_guard=-1,
        alarm_negative_guard=-1,
        alarm_states=alarm_states,
        alarm_time=8,
        local_flagstart=True,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=7,
    )


def test_alarm_time_offset_reached_uses_elapsed_time_without_event_offset() -> None:
    assert alarm_time_offset_reached(
        alarm_offset=30.0,
        elapsed_time=31.0,
        alarm_time=9,
        local_flagstart=False,
        sample_timex=[0.0],
        timeindex=[-1],
        tp_alarm_timeindex=None,
        alarm_states=[],
        alarm_guard=-1,
    )
    assert not alarm_time_offset_reached(
        alarm_offset=30.0,
        elapsed_time=29.0,
        alarm_time=-1,
        local_flagstart=True,
        sample_timex=[0.0],
        timeindex=[-1],
        tp_alarm_timeindex=None,
        alarm_states=[],
        alarm_guard=-1,
    )


def test_alarm_time_offset_reached_rejects_disabled_offset() -> None:
    assert not alarm_time_offset_reached(
        alarm_offset=0.0,
        elapsed_time=31.0,
        alarm_time=9,
        local_flagstart=False,
        sample_timex=[0.0],
        timeindex=[-1],
        tp_alarm_timeindex=None,
        alarm_states=[],
        alarm_guard=-1,
    )


def test_alarm_time_offset_reached_subtracts_event_indexes() -> None:
    sample_timex = [0.0, 10.0, 20.0, 30.0, 40.0]
    assert alarm_time_offset_reached(
        alarm_offset=15.0,
        elapsed_time=31.0,
        alarm_time=0,
        local_flagstart=True,
        sample_timex=sample_timex,
        timeindex=[1, 0, 3],
        tp_alarm_timeindex=None,
        alarm_states=[],
        alarm_guard=-1,
    )
    assert not alarm_time_offset_reached(
        alarm_offset=15.0,
        elapsed_time=31.0,
        alarm_time=2,
        local_flagstart=True,
        sample_timex=sample_timex,
        timeindex=[1, 0, 3],
        tp_alarm_timeindex=None,
        alarm_states=[],
        alarm_guard=-1,
    )


def test_alarm_time_offset_reached_subtracts_tp_and_if_alarm_indexes() -> None:
    sample_timex = [0.0, 10.0, 20.0, 30.0, 40.0]
    assert alarm_time_offset_reached(
        alarm_offset=20.0,
        elapsed_time=41.0,
        alarm_time=8,
        local_flagstart=True,
        sample_timex=sample_timex,
        timeindex=[1, 0, 0],
        tp_alarm_timeindex=2,
        alarm_states=[3],
        alarm_guard=0,
    )
    assert not alarm_time_offset_reached(
        alarm_offset=20.0,
        elapsed_time=41.0,
        alarm_time=10,
        local_flagstart=True,
        sample_timex=sample_timex,
        timeindex=[1, 0, 0],
        tp_alarm_timeindex=None,
        alarm_states=[3],
        alarm_guard=0,
    )


def test_evaluate_alarm_triggers_updates_guard_state_between_rules() -> None:
    alarm_states = [-1, -1]

    triggers = evaluate_alarm_triggers(
        alarm_flags=[True, True],
        alarm_states=alarm_states,
        alarm_guards=[-1, 0],
        alarm_negative_guards=[-1, -1],
        alarm_times=[9, 10],
        alarm_offsets=[1.0, 0.0],
        alarm_sources=[0, 0],
        alarm_conditions=[1, 2],
        alarm_temperatures=[999.0, 0.0],
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
        elapsed_time=2.0,
        sample_timex=[0.0, 10.0, 20.0],
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[100.0, 120.0, 150.0],
        sample_temp2=[101.0, 121.0, 151.0],
        sample_extratemp1=[],
        sample_extratemp2=[],
        extra_device_count=0,
        trigger_state_index=2,
    )

    assert [(trigger.alarm_index, trigger.state_index) for trigger in triggers] == [(0, 2), (1, 2)]
    assert alarm_states == [-1, -1]


def test_evaluate_alarm_triggers_returns_temperature_and_extra_device_triggers() -> None:
    triggers = evaluate_alarm_triggers(
        alarm_flags=[1, 1],
        alarm_states=[-1, -1],
        alarm_guards=[-1, -1],
        alarm_negative_guards=[-1, -1],
        alarm_times=[9, 9],
        alarm_offsets=[0.0, 0.0],
        alarm_sources=[1, 3],
        alarm_conditions=[1, 1],
        alarm_temperatures=[180.0, 250.0],
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
        elapsed_time=0.0,
        sample_timex=[0.0],
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[160.0],
        sample_temp2=[181.0],
        sample_extratemp1=[[240.0]],
        sample_extratemp2=[[251.0]],
        extra_device_count=1,
        trigger_state_index=-4,
    )

    assert [(trigger.alarm_index, trigger.state_index) for trigger in triggers] == [(0, 0), (1, 0)]


def test_evaluate_alarm_triggers_keeps_earlier_trigger_when_later_row_is_incomplete() -> None:
    triggers = evaluate_alarm_triggers(
        alarm_flags=[1, 1],
        alarm_states=[-1, -1],
        alarm_guards=[-1],
        alarm_negative_guards=[-1, -1],
        alarm_times=[9, 9],
        alarm_offsets=[1.0, 0.0],
        alarm_sources=[0, 0],
        alarm_conditions=[1, 1],
        alarm_temperatures=[999.0, 0.0],
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
        elapsed_time=2.0,
        sample_timex=[0.0],
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[150.0],
        sample_temp2=[151.0],
        sample_extratemp1=[],
        sample_extratemp2=[],
        extra_device_count=0,
        trigger_state_index=3,
    )

    assert [(trigger.alarm_index, trigger.state_index) for trigger in triggers] == [(0, 3)]


def test_evaluate_alarm_triggers_applies_negative_guard_after_same_pass_trigger() -> None:
    triggers = evaluate_alarm_triggers(
        alarm_flags=[1, 1],
        alarm_states=[-1, -1],
        alarm_guards=[-1, -1],
        alarm_negative_guards=[-1, 0],
        alarm_times=[9, 9],
        alarm_offsets=[1.0, 1.0],
        alarm_sources=[0, 0],
        alarm_conditions=[1, 1],
        alarm_temperatures=[999.0, 999.0],
        local_flagstart=False,
        timeindex=[-1, 0, 0],
        tp_alarm_timeindex=None,
        elapsed_time=2.0,
        sample_timex=[0.0],
        sample_delta1=[],
        sample_delta2=[],
        sample_temp1=[150.0],
        sample_temp2=[151.0],
        sample_extratemp1=[],
        sample_extratemp2=[],
        extra_device_count=0,
        trigger_state_index=4,
    )

    assert [(trigger.alarm_index, trigger.state_index) for trigger in triggers] == [(0, 4)]


def test_auto_charge_event_candidate_applies_celsius_and_fahrenheit_thresholds() -> None:
    assert auto_charge_event_candidate(
        auto_charge_idx=0,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        charge_index=-1,
        sample_count=5,
        mode='C',
        latest_bt=77.1,
    )
    assert auto_charge_event_candidate(
        auto_charge_idx=0,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        charge_index=-1,
        sample_count=5,
        mode='F',
        latest_bt=170.1,
    )
    assert not auto_charge_event_candidate(
        auto_charge_idx=0,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        charge_index=-1,
        sample_count=5,
        mode='C',
        latest_bt=77.0,
    )
    assert not auto_charge_event_candidate(
        auto_charge_idx=0,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        charge_index=-1,
        sample_count=5,
        mode='F',
        latest_bt=170.0,
    )


def test_auto_charge_event_candidate_rejects_disabled_or_already_charged_state() -> None:
    assert not auto_charge_event_candidate(
        auto_charge_idx=1,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        charge_index=-1,
        sample_count=5,
        mode='C',
        latest_bt=90.0,
    )
    assert not auto_charge_event_candidate(
        auto_charge_idx=0,
        auto_charge_flag=False,
        auto_charge_enabled=True,
        charge_index=-1,
        sample_count=5,
        mode='C',
        latest_bt=90.0,
    )
    assert not auto_charge_event_candidate(
        auto_charge_idx=0,
        auto_charge_flag=True,
        auto_charge_enabled=False,
        charge_index=-1,
        sample_count=5,
        mode='C',
        latest_bt=90.0,
    )
    assert not auto_charge_event_candidate(
        auto_charge_idx=0,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        charge_index=0,
        sample_count=5,
        mode='C',
        latest_bt=90.0,
    )
    assert not auto_charge_event_candidate(
        auto_charge_idx=0,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        charge_index=-1,
        sample_count=4,
        mode='C',
        latest_bt=90.0,
    )


def test_turning_point_timeout_index_returns_current_index_after_max_roast_time() -> None:
    assert turning_point_timeout_index(
        tp_alarm_timeindex=None,
        charge_index=1,
        sample_times=[0.0, 10.0, 80.1],
        tp_max_roast_time=70.0,
        sample_count=3,
    ) == 2
    assert turning_point_timeout_index(
        tp_alarm_timeindex=None,
        charge_index=1,
        sample_times=[0.0, 10.0, 80.0],
        tp_max_roast_time=70.0,
        sample_count=3,
    ) is None
    assert turning_point_timeout_index(
        tp_alarm_timeindex=2,
        charge_index=1,
        sample_times=[0.0, 10.0, 90.0],
        tp_max_roast_time=70.0,
        sample_count=3,
    ) is None


def test_turning_point_check_candidate_applies_charge_dry_and_sample_count_gates() -> None:
    assert turning_point_check_candidate(
        tp_alarm_timeindex=None,
        charge_index=1,
        dry_index=0,
        bt_sample_count=10,
    )
    assert not turning_point_check_candidate(
        tp_alarm_timeindex=2,
        charge_index=1,
        dry_index=0,
        bt_sample_count=10,
    )
    assert not turning_point_check_candidate(
        tp_alarm_timeindex=None,
        charge_index=-1,
        dry_index=0,
        bt_sample_count=10,
    )
    assert not turning_point_check_candidate(
        tp_alarm_timeindex=None,
        charge_index=1,
        dry_index=1,
        bt_sample_count=10,
    )
    assert not turning_point_check_candidate(
        tp_alarm_timeindex=None,
        charge_index=1,
        dry_index=0,
        bt_sample_count=9,
    )


def test_turning_point_temperature_is_valid_applies_celsius_and_fahrenheit_ranges() -> None:
    assert turning_point_temperature_is_valid('C', 100.0)
    assert not turning_point_temperature_is_valid('C', 50.0)
    assert not turning_point_temperature_is_valid('C', 150.0)
    assert turning_point_temperature_is_valid('F', 200.0)
    assert not turning_point_temperature_is_valid('F', 100.0)
    assert not turning_point_temperature_is_valid('F', 300.0)


def test_auto_drop_event_candidate_applies_thresholds_and_roast_elapsed_time() -> None:
    assert auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=0,
        sample_count=5,
        mode='C',
        latest_bt=160.1,
        sample_times=[0.0, 10.0, 431.0],
    )
    assert auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=0,
        sample_count=5,
        mode='F',
        latest_bt=320.1,
        sample_times=[0.0, 10.0, 431.0],
    )
    assert not auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=0,
        sample_count=5,
        mode='C',
        latest_bt=160.0,
        sample_times=[0.0, 10.0, 431.0],
    )
    assert not auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=0,
        sample_count=5,
        mode='F',
        latest_bt=320.0,
        sample_times=[0.0, 10.0, 431.0],
    )
    assert not auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=0,
        sample_count=5,
        mode='C',
        latest_bt=170.0,
        sample_times=[0.0, 10.0, 430.0],
    )


def test_auto_drop_event_candidate_rejects_disabled_or_unready_state() -> None:
    assert not auto_drop_event_candidate(
        auto_drop_idx=1,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=0,
        sample_count=5,
        mode='C',
        latest_bt=170.0,
        sample_times=ExplodingSequence(),
    )
    assert not auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=0,
        sample_count=5,
        mode='C',
        latest_bt=160.0,
        sample_times=ExplodingSequence(),
    )
    assert not auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=False,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=0,
        sample_count=5,
        mode='C',
        latest_bt=170.0,
        sample_times=ExplodingSequence(),
    )
    assert not auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=False,
        charge_index=1,
        drop_index=0,
        sample_count=5,
        mode='C',
        latest_bt=170.0,
        sample_times=ExplodingSequence(),
    )
    assert not auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=-1,
        drop_index=0,
        sample_count=5,
        mode='C',
        latest_bt=170.0,
        sample_times=ExplodingSequence(),
    )
    assert not auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=2,
        sample_count=5,
        mode='C',
        latest_bt=170.0,
        sample_times=ExplodingSequence(),
    )
    assert not auto_drop_event_candidate(
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        charge_index=1,
        drop_index=0,
        sample_count=4,
        mode='C',
        latest_bt=170.0,
        sample_times=ExplodingSequence(),
    )


def test_auto_dry_event_candidate_uses_tp_truthiness_and_phase_threshold() -> None:
    assert auto_dry_event_candidate(
        auto_dry_flag=True,
        auto_dry_enabled=True,
        tp_alarm_timeindex=7,
        charge_index=1,
        dry_index=0,
        fcs_index=0,
        latest_bt=151.0,
        dry_phase_temperature=150.0,
    )
    assert not auto_dry_event_candidate(
        auto_dry_flag=True,
        auto_dry_enabled=True,
        tp_alarm_timeindex=0,
        charge_index=1,
        dry_index=0,
        fcs_index=0,
        latest_bt=151.0,
        dry_phase_temperature=150.0,
    )
    assert not auto_dry_event_candidate(
        auto_dry_flag=True,
        auto_dry_enabled=False,
        tp_alarm_timeindex=7,
        charge_index=1,
        dry_index=0,
        fcs_index=0,
        latest_bt=151.0,
        dry_phase_temperature=150.0,
    )
    assert not auto_dry_event_candidate(
        auto_dry_flag=True,
        auto_dry_enabled=True,
        tp_alarm_timeindex=7,
        charge_index=1,
        dry_index=2,
        fcs_index=0,
        latest_bt=151.0,
        dry_phase_temperature=150.0,
    )
    assert not auto_dry_event_candidate(
        auto_dry_flag=True,
        auto_dry_enabled=True,
        tp_alarm_timeindex=7,
        charge_index=1,
        dry_index=0,
        fcs_index=2,
        latest_bt=151.0,
        dry_phase_temperature=150.0,
    )
    assert not auto_dry_event_candidate(
        auto_dry_flag=True,
        auto_dry_enabled=True,
        tp_alarm_timeindex=7,
        charge_index=1,
        dry_index=0,
        fcs_index=0,
        latest_bt=149.9,
        dry_phase_temperature=150.0,
    )


def test_auto_fcs_event_candidate_uses_tp_truthiness_and_phase_threshold() -> None:
    assert auto_fcs_event_candidate(
        auto_fcs_flag=True,
        auto_fcs_enabled=True,
        tp_alarm_timeindex=7,
        charge_index=1,
        fcs_index=0,
        fce_index=0,
        latest_bt=196.0,
        fcs_phase_temperature=196.0,
    )
    assert not auto_fcs_event_candidate(
        auto_fcs_flag=True,
        auto_fcs_enabled=True,
        tp_alarm_timeindex=0,
        charge_index=1,
        fcs_index=0,
        fce_index=0,
        latest_bt=196.0,
        fcs_phase_temperature=196.0,
    )
    assert not auto_fcs_event_candidate(
        auto_fcs_flag=True,
        auto_fcs_enabled=False,
        tp_alarm_timeindex=7,
        charge_index=1,
        fcs_index=0,
        fce_index=0,
        latest_bt=196.0,
        fcs_phase_temperature=196.0,
    )
    assert not auto_fcs_event_candidate(
        auto_fcs_flag=True,
        auto_fcs_enabled=True,
        tp_alarm_timeindex=7,
        charge_index=1,
        fcs_index=2,
        fce_index=0,
        latest_bt=196.0,
        fcs_phase_temperature=196.0,
    )
    assert not auto_fcs_event_candidate(
        auto_fcs_flag=True,
        auto_fcs_enabled=True,
        tp_alarm_timeindex=7,
        charge_index=1,
        fcs_index=0,
        fce_index=2,
        latest_bt=196.0,
        fcs_phase_temperature=196.0,
    )
    assert not auto_fcs_event_candidate(
        auto_fcs_flag=True,
        auto_fcs_enabled=True,
        tp_alarm_timeindex=7,
        charge_index=1,
        fcs_index=0,
        fce_index=0,
        latest_bt=195.9,
        fcs_phase_temperature=196.0,
    )


def test_delta_smoothing_filter_size_uses_existing_half_rounding_rule() -> None:
    assert delta_smoothing_filter_size(delta_filter=4, sample_count=5, unfiltered_count=5) == 2
    assert delta_smoothing_filter_size(delta_filter=5, sample_count=5, unfiltered_count=5) == 2
    assert delta_smoothing_filter_size(delta_filter=6, sample_count=5, unfiltered_count=5) == 3


def test_delta_smoothing_filter_size_rejects_disabled_or_unready_windows() -> None:
    assert delta_smoothing_filter_size(delta_filter=0, sample_count=5, unfiltered_count=5) is None
    assert delta_smoothing_filter_size(delta_filter=1, sample_count=5, unfiltered_count=5) is None
    assert delta_smoothing_filter_size(delta_filter=4, sample_count=2, unfiltered_count=5) is None
    assert delta_smoothing_filter_size(delta_filter=4, sample_count=5, unfiltered_count=2) is None


def test_smoothed_rate_of_change_value_falls_back_to_latest_without_usable_weights() -> None:
    assert smoothed_rate_of_change_value(
        sample_times=[0.0, 10.0],
        unfiltered_rates=[5.0, 9.0],
        decay_weights=None,
        sample_interval_seconds=10.0,
    ) == 9.0


def test_smoothed_rate_of_change_value_uses_decay_weighted_average() -> None:
    assert smoothed_rate_of_change_value(
        sample_times=[0.0, 1.0, 2.0],
        unfiltered_rates=[10.0, None, 30.0],
        decay_weights=[1, 2, 3],
        sample_interval_seconds=1.0,
    ) == pytest.approx(26.0)


def test_smoothed_rate_of_change_value_returns_negative_one_without_rates() -> None:
    assert smoothed_rate_of_change_value(
        sample_times=[],
        unfiltered_rates=[],
        decay_weights=[1, 2],
        sample_interval_seconds=1.0,
    ) == -1


def test_simple_rate_of_rise_uses_legacy_left_point_average() -> None:
    assert simple_rate_of_rise_per_minute(
        sample_times=[0.0, 10.0, 20.0],
        temperatures=[100.0, 110.0, 130.0],
        left_index=2,
        previous_rates=[],
    ) == pytest.approx(100.0)


def test_simple_rate_of_rise_reuses_previous_rate_for_dropout() -> None:
    assert simple_rate_of_rise_per_minute(
        sample_times=[0.0, 10.0],
        temperatures=[100.0, -1.0],
        left_index=2,
        previous_rates=[12.5],
    ) == 12.5
    assert simple_rate_of_rise_per_minute(
        sample_times=[0.0, 10.0],
        temperatures=[100.0, -1.0],
        left_index=2,
        previous_rates=[],
    ) == 0.0


def test_rate_of_rise_reuses_previous_rate_for_invalid_latest_sample() -> None:
    assert rate_of_rise_per_minute(
        latest_temperature=-1.0,
        sample_times=[0.0, 10.0],
        temperatures=[100.0, -1.0],
        previous_rates=[8.5],
        delta_samples=3,
        use_polyfit=False,
    ) == 8.5
    assert rate_of_rise_per_minute(
        latest_temperature=120.0,
        sample_times=[0.0],
        temperatures=[120.0],
        previous_rates=[],
        delta_samples=3,
        use_polyfit=False,
    ) == 0.0


def test_rate_of_rise_uses_delta_sample_window_without_polyfit() -> None:
    assert rate_of_rise_per_minute(
        latest_temperature=140.0,
        sample_times=[0.0, 10.0, 20.0, 30.0],
        temperatures=[100.0, 110.0, 120.0, 140.0],
        previous_rates=[],
        delta_samples=2,
        use_polyfit=False,
    ) == 90.0


def test_rate_of_rise_uses_polyfit_when_enabled() -> None:
    assert rate_of_rise_per_minute(
        latest_temperature=130.0,
        sample_times=[0.0, 10.0, 20.0, 30.0],
        temperatures=[100.0, 105.0, 120.0, 130.0],
        previous_rates=[],
        delta_samples=3,
        use_polyfit=True,
    ) == pytest.approx(63.0)


def test_rate_of_rise_falls_back_when_polyfit_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_polyfit(*_args: object, **_kwargs: object) -> list[float]:
        raise ValueError('SVD did not converge')

    monkeypatch.setattr(numpy.polynomial.polynomial, 'polyfit', fail_polyfit)

    assert rate_of_rise_per_minute(
        latest_temperature=140.0,
        sample_times=[0.0, 10.0, 20.0, 30.0],
        temperatures=[100.0, 110.0, 120.0, 140.0],
        previous_rates=[],
        delta_samples=2,
        use_polyfit=True,
    ) == 90.0


def test_displayed_ror_value_passes_through_when_limit_disabled_or_value_missing() -> None:
    assert displayed_ror_value(
        12.0,
        ror_limit_enabled=False,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
    ) == 12.0
    assert displayed_ror_value(
        None,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
    ) is None


def test_displayed_ror_value_masks_values_outside_open_limits() -> None:
    assert displayed_ror_value(
        19.9,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
    ) == 19.9
    assert displayed_ror_value(
        20.0,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
    ) is None
    assert displayed_ror_value(
        -20.0,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
    ) is None
    assert displayed_ror_value(
        -20.1,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
    ) is None


def test_displayed_ror_value_combines_global_and_user_limits() -> None:
    assert displayed_ror_value(
        25.0,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=40.0,
        ror_limit_min=-40.0,
    ) == 25.0
    assert displayed_ror_value(
        30.0,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=40.0,
        ror_limit_min=-40.0,
    ) is None
    assert displayed_ror_value(
        -30.0,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=40.0,
        ror_limit_min=-40.0,
    ) is None


def test_ror_curve_window_starts_before_charge_after_first_rate_sample() -> None:
    assert ror_curve_window(
        charge_index=-1,
        drop_index=0,
        sample_count=20,
        delta_filter=4,
        delta_samples=3,
    ) == (1, 20)


def test_ror_curve_window_waits_until_two_samples_exist() -> None:
    assert ror_curve_window(
        charge_index=-1,
        drop_index=0,
        sample_count=1,
        delta_filter=4,
        delta_samples=3,
    ) is None


def test_ror_curve_window_skips_charge_warmup_and_stops_after_drop() -> None:
    assert ror_curve_window(
        charge_index=5,
        drop_index=12,
        sample_count=20,
        delta_filter=4,
        delta_samples=3,
    ) == (11, 13)
    assert ror_curve_window(
        charge_index=5,
        drop_index=0,
        sample_count=20,
        delta_filter=0,
        delta_samples=0,
    ) == (7, 20)
    assert ror_curve_window(
        charge_index=5,
        drop_index=0,
        sample_count=6,
        delta_filter=4,
        delta_samples=3,
    ) == (1, 6)


def test_windowed_curve_data_returns_empty_payload_without_window() -> None:
    data = windowed_curve_data(
        sample_times=[0.0, 1.0, 2.0],
        values=[10.0, 11.0, 12.0],
        window=None,
    )

    assert data.times == ()
    assert data.values == ()


def test_windowed_curve_data_uses_existing_start_end_slice_semantics() -> None:
    data = windowed_curve_data(
        sample_times=[0.0, 1.0, 2.0, 3.0],
        values=[10.0, None, 12.0, 13.0],
        window=(1, 3),
    )

    assert data.times == (1.0, 2.0)
    assert data.values == (None, 12.0)


def test_full_curve_data_returns_empty_payload_for_empty_sequences() -> None:
    data = full_curve_data(
        sample_times=[],
        values=[],
    )

    assert data.times == ()
    assert data.values == ()


def test_full_curve_data_preserves_connected_curve_values() -> None:
    data = full_curve_data(
        sample_times=[0.0, 1.0, 2.0],
        values=[10.0, None, 12.0],
    )

    assert data.times == (0.0, 1.0, 2.0)
    assert data.values == (10.0, None, 12.0)


def test_build_live_processed_sample_frame_collects_display_axis_and_event_decisions() -> None:
    sample_times = [0.0, 100.0, 180.0, 240.0, 300.0, 360.0, 420.0, 480.0, 540.0, 600.0, 660.0, 721.0]
    frame = build_live_processed_sample_frame(
        timestamp=721.0,
        sample_count=len(sample_times),
        latest_et=180.0,
        latest_bt=201.0,
        smoothed_et=179.0,
        smoothed_bt=200.0,
        pid_process_value=200.0,
        raw_delta_et=25.0,
        raw_delta_bt=19.0,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
        charge_index=1,
        dry_index=0,
        drop_index=0,
        delta_et_filter=4.0,
        delta_bt_filter=0.0,
        delta_et_samples=3,
        delta_bt_samples=0,
        fix_max_time=False,
        lock_time_x=False,
        sample_times=sample_times,
        start_of_x=0.0,
        end_of_x=660.0,
        tp_alarm_timeindex=7,
        tp_max_roast_time=120.0,
        auto_charge_idx=0,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        mode='C',
    )

    assert frame.timestamp == 721.0
    assert frame.sample_count == len(sample_times)
    assert frame.latest_et == 180.0
    assert frame.latest_bt == 201.0
    assert frame.smoothed_et == 179.0
    assert frame.smoothed_bt == 200.0
    assert frame.pid_process_value == 200.0
    assert frame.displayed_delta_et is None
    assert frame.displayed_delta_bt == 19.0
    assert frame.delta_et_window == (7, 12)
    assert frame.delta_bt_window == (3, 12)
    assert frame.live_x_axis_extension_end == 781.0
    assert not frame.events.charge_candidate
    assert frame.events.turning_point_timeout_index is None
    assert not frame.events.turning_point_check_candidate
    assert frame.events.drop_candidate


def test_build_live_processed_sample_frame_returns_precharge_ror_windows_without_sample_access() -> None:
    frame = build_live_processed_sample_frame(
        timestamp=12.0,
        sample_count=4,
        latest_et=80.0,
        latest_bt=90.0,
        smoothed_et=79.0,
        smoothed_bt=89.0,
        pid_process_value=None,
        raw_delta_et=None,
        raw_delta_bt=None,
        ror_limit_enabled=True,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
        charge_index=-1,
        dry_index=0,
        drop_index=0,
        delta_et_filter=4.0,
        delta_bt_filter=4.0,
        delta_et_samples=3,
        delta_bt_samples=3,
        fix_max_time=True,
        lock_time_x=False,
        sample_times=NoAccessSequence(),
        start_of_x=0.0,
        end_of_x=660.0,
        tp_alarm_timeindex=None,
        tp_max_roast_time=120.0,
        auto_charge_idx=1,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        auto_drop_idx=0,
        auto_drop_flag=True,
        auto_drop_enabled=True,
        mode='C',
    )

    assert frame.displayed_delta_et is None
    assert frame.displayed_delta_bt is None
    assert frame.delta_et_window == (1, 4)
    assert frame.delta_bt_window == (1, 4)
    assert frame.live_x_axis_extension_end is None
    assert not frame.events.charge_candidate
    assert frame.events.turning_point_timeout_index is None
    assert not frame.events.turning_point_check_candidate
    assert not frame.events.drop_candidate


def test_phase_event_candidates_are_evaluated_after_turning_point_timeout_state() -> None:
    sample_times = [0.0, 10.0, 131.0]
    frame = build_live_processed_sample_frame(
        timestamp=131.0,
        sample_count=len(sample_times),
        latest_et=180.0,
        latest_bt=201.0,
        smoothed_et=179.0,
        smoothed_bt=200.0,
        pid_process_value=200.0,
        raw_delta_et=5.0,
        raw_delta_bt=6.0,
        ror_limit_enabled=False,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
        charge_index=1,
        dry_index=0,
        drop_index=0,
        delta_et_filter=0.0,
        delta_bt_filter=0.0,
        delta_et_samples=0,
        delta_bt_samples=0,
        fix_max_time=True,
        lock_time_x=False,
        sample_times=sample_times,
        start_of_x=0.0,
        end_of_x=660.0,
        tp_alarm_timeindex=None,
        tp_max_roast_time=120.0,
        auto_charge_idx=1,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        auto_drop_idx=0,
        auto_drop_flag=False,
        auto_drop_enabled=True,
        mode='C',
    )

    assert frame.events.turning_point_timeout_index == 2

    phase_events = phase_event_candidates_after_turning_point(
        auto_dry_flag=True,
        auto_dry_enabled=True,
        auto_fcs_flag=True,
        auto_fcs_enabled=True,
        tp_alarm_timeindex=frame.events.turning_point_timeout_index,
        charge_index=1,
        dry_index=0,
        fcs_index=0,
        fce_index=0,
        latest_bt=201.0,
        dry_phase_temperature=150.0,
        fcs_phase_temperature=196.0,
    )

    assert phase_events.dry_candidate
    assert phase_events.fcs_candidate


# ----------------------------------------------------------------------------
# Phase 3 audit additive characterization tests (2026-06-30).
#
# These tests document the existing contract of symbols in
# ``artisanlib.sample_processing`` that prior Phase 3 slices left without
# direct unit coverage. They are intentionally minimal (one equality test +
# one frozen test per dataclass; a small behaviour matrix per private
# helper) and exist to break loudly if a future cleanup slice changes a
# dataclass field, drops ``frozen=True``, or silently alters the private
# helper contracts that the public wrappers depend on.
#
# No production code was modified to add these tests.
# ----------------------------------------------------------------------------


def test_alarm_trigger_is_frozen_and_equal() -> None:
    assert AlarmTrigger(alarm_index=2, state_index=1) == AlarmTrigger(alarm_index=2, state_index=1)
    assert AlarmTrigger(alarm_index=2, state_index=1) != AlarmTrigger(alarm_index=3, state_index=1)
    trigger = AlarmTrigger(alarm_index=2, state_index=1)
    with pytest.raises(FrozenInstanceError):
        trigger.alarm_index = 5  # type: ignore[misc]


def test_backfill_update_is_frozen_and_equal() -> None:
    assert BackfillUpdate(index=1, value=199.5) == BackfillUpdate(index=1, value=199.5)
    assert BackfillUpdate(index=1, value=199.5) != BackfillUpdate(index=2, value=199.5)
    update = BackfillUpdate(index=1, value=199.5)
    with pytest.raises(FrozenInstanceError):
        update.value = 200.0  # type: ignore[misc]


def test_auto_event_decisions_is_frozen_and_equal() -> None:
    a = AutoEventDecisions(
        charge_candidate=True,
        turning_point_timeout_index=4,
        turning_point_check_candidate=False,
        drop_candidate=False,
    )
    b = AutoEventDecisions(
        charge_candidate=True,
        turning_point_timeout_index=4,
        turning_point_check_candidate=False,
        drop_candidate=False,
    )
    assert a == b
    assert a != AutoEventDecisions(True, None, False, False)
    with pytest.raises(FrozenInstanceError):
        a.charge_candidate = False  # type: ignore[misc]


def test_connected_curve_point_is_frozen_and_equal() -> None:
    assert ConnectedCurvePoint(should_append=True, value=200.0) == ConnectedCurvePoint(True, 200.0)
    assert ConnectedCurvePoint(True, 200.0) != ConnectedCurvePoint(False, 200.0)
    point = ConnectedCurvePoint(True, 200.0)
    with pytest.raises(FrozenInstanceError):
        point.value = 201.0  # type: ignore[misc]


def test_curve_window_data_is_frozen_and_equal() -> None:
    payload_a = CurveWindowData(times=(0.0, 1.0), values=(200.0, 201.0))
    payload_b = CurveWindowData(times=(0.0, 1.0), values=(200.0, 201.0))
    assert payload_a == payload_b
    assert payload_a != CurveWindowData(times=(0.0,), values=(200.0,))
    with pytest.raises(FrozenInstanceError):
        payload_a.times = (9.0,)  # type: ignore[misc]


def test_input_filter_result_is_frozen_and_equal() -> None:
    result = InputFilterResult(value=200.0, backfill_updates=(BackfillUpdate(0, 199.0),))
    same = InputFilterResult(value=200.0, backfill_updates=(BackfillUpdate(0, 199.0),))
    assert result == same
    assert result != InputFilterResult(value=201.0, backfill_updates=())
    with pytest.raises(FrozenInstanceError):
        result.value = 205.0  # type: ignore[misc]


def test_phase_event_decisions_is_frozen_and_equal() -> None:
    assert PhaseEventDecisions(dry_candidate=True, fcs_candidate=False) == PhaseEventDecisions(True, False)
    assert PhaseEventDecisions(True, False) != PhaseEventDecisions(False, True)
    decisions = PhaseEventDecisions(True, False)
    with pytest.raises(FrozenInstanceError):
        decisions.dry_candidate = False  # type: ignore[misc]


def test_post_sample_update_decisions_is_frozen_and_equal() -> None:
    assert PostSampleUpdateDecisions(True, True, False) == PostSampleUpdateDecisions(True, True, False)
    assert PostSampleUpdateDecisions(True, True, False) != PostSampleUpdateDecisions(False, True, False)
    decisions = PostSampleUpdateDecisions(True, True, False)
    with pytest.raises(FrozenInstanceError):
        decisions.update_auc = False  # type: ignore[misc]


def test_previous_readings_is_frozen_and_equal() -> None:
    assert PreviousReadings(latest=200.0, previous=199.5) == PreviousReadings(200.0, 199.5)
    assert PreviousReadings(200.0, 199.5) != PreviousReadings(200.0, None)
    readings = PreviousReadings(200.0, 199.5)
    with pytest.raises(FrozenInstanceError):
        readings.latest = 205.0  # type: ignore[misc]


def test_processed_sample_frame_is_frozen_and_field_set_pinned() -> None:
    frame = build_live_processed_sample_frame(
        timestamp=120.0,
        sample_count=3,
        latest_et=180.0,
        latest_bt=200.0,
        smoothed_et=179.5,
        smoothed_bt=199.5,
        pid_process_value=199.5,
        raw_delta_et=5.0,
        raw_delta_bt=6.0,
        ror_limit_enabled=False,
        max_ror_limit=30.0,
        ror_limit=20.0,
        ror_limit_min=-20.0,
        charge_index=1,
        dry_index=0,
        drop_index=0,
        delta_et_filter=0.0,
        delta_bt_filter=0.0,
        delta_et_samples=0,
        delta_bt_samples=0,
        fix_max_time=True,
        lock_time_x=False,
        sample_times=[0.0, 60.0, 120.0],
        start_of_x=0.0,
        end_of_x=660.0,
        tp_alarm_timeindex=None,
        tp_max_roast_time=120.0,
        auto_charge_idx=1,
        auto_charge_flag=True,
        auto_charge_enabled=True,
        auto_drop_idx=0,
        auto_drop_flag=False,
        auto_drop_enabled=True,
        mode='C',
    )
    # Pin the runtime type and field set so canvas.py consumers don't silently
    # lose a payload attribute if a future slice renames or removes a field.
    assert isinstance(frame, ProcessedSampleFrame)
    assert set(frame.__dataclass_fields__) == {
        'timestamp', 'sample_count', 'latest_et', 'latest_bt',
        'smoothed_et', 'smoothed_bt', 'pid_process_value',
        'displayed_delta_et', 'displayed_delta_bt',
        'delta_et_window', 'delta_bt_window',
        'live_x_axis_extension_end', 'events',
    }
    with pytest.raises(FrozenInstanceError):
        frame.latest_bt = 999.0  # type: ignore[misc]


def test_bt_above_event_threshold_is_strict_per_mode() -> None:
    # Celsius mode uses celsius_threshold and is strict inequality.
    assert _bt_above_event_threshold('C', 195.0, 194.0, 380.0) is True
    assert _bt_above_event_threshold('C', 194.0, 194.0, 380.0) is False
    # Fahrenheit mode uses fahrenheit_threshold and ignores celsius_threshold.
    assert _bt_above_event_threshold('F', 380.0, 999.0, 379.0) is True
    assert _bt_above_event_threshold('F', 379.0, 0.0, 379.0) is False
    # Any other mode string yields False (guarded equality, not membership).
    assert _bt_above_event_threshold('c', 9999.0, 0.0, 0.0) is False
    assert _bt_above_event_threshold('', 9999.0, 0.0, 0.0) is False


def test_alarm_row_is_complete_requires_every_input_long_enough() -> None:
    # 8 sequences after index: states, guards, negative_guards, times,
    # offsets, sources, conditions, temperatures.
    full_args = ([0], [0], [0], [0], [0.0], [0], [0], [0.0])
    assert _alarm_row_is_complete(0, *full_args) is True
    # Each sequence is checked independently; shortening any one trips False.
    for short_idx in range(8):
        args = list(full_args)
        args[short_idx] = []
        assert _alarm_row_is_complete(0, *args) is False
    # Index equal to length is the boundary (not complete).
    assert _alarm_row_is_complete(1, *full_args) is False


def test_relative_latest_value_handles_empty_dropout_and_baseline_cases() -> None:
    # Empty values short-circuit to None.
    assert _relative_latest_value([], alarm_index=None) is None
    # Latest dropout propagates as None without consulting earlier entries.
    assert _relative_latest_value([1.0, None], alarm_index=None) is None
    # Without a baseline request, the latest value is returned as-is.
    assert _relative_latest_value([1.0, 2.0, 3.0], alarm_index=None) == 3.0
    # With a valid baseline index, the baseline is subtracted.
    assert _relative_latest_value([10.0, 20.0, 30.0], alarm_index=0) == 20.0
    # A dropout baseline is treated as zero (no subtraction).
    assert _relative_latest_value([None, 20.0, 30.0], alarm_index=0) == 30.0
    # An out-of-range baseline is caught and the helper returns None.
    assert _relative_latest_value([1.0, 2.0, 3.0], alarm_index=99) is None
