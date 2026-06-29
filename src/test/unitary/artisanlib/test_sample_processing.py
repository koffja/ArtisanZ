from __future__ import annotations

from collections.abc import Iterator, Sequence

from artisanlib.sample_processing import (
    alarm_is_eligible_for_evaluation,
    alarm_source_value,
    alarm_temperature_reaches_limit,
    alarm_time_offset_reached,
    auto_charge_event_candidate,
    auto_drop_event_candidate,
    auto_dry_event_candidate,
    auto_fcs_event_candidate,
    connected_curve_point,
    decay_weight_sequence,
    delta_smoothing_filter_size,
    displayed_ror_value,
    input_filter_backfill_updates,
    input_filter_previous_values,
    pid_process_value,
    relative_alarm_index,
    ror_curve_window,
    smoothing_weights_for_recent_readings,
    turning_point_check_candidate,
    turning_point_temperature_is_valid,
    turning_point_timeout_index,
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


def test_pid_process_value_uses_smoothed_bt_for_default_sources() -> None:
    assert pid_process_value(0, smoothed_et=181.0, smoothed_bt=202.5, extra_temps_1=[], extra_temps_2=[]) == 202.5
    assert pid_process_value(1, smoothed_et=181.0, smoothed_bt=203.5, extra_temps_1=[], extra_temps_2=[]) == 203.5


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


def test_ror_curve_window_returns_none_before_charge() -> None:
    assert ror_curve_window(
        charge_index=-1,
        drop_index=0,
        sample_count=20,
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
