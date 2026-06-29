from __future__ import annotations

from artisanlib.sample_processing import (
    alarm_source_value,
    alarm_temperature_reaches_limit,
    decay_weight_sequence,
    pid_process_value,
    relative_alarm_index,
    smoothing_weights_for_recent_readings,
)


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
