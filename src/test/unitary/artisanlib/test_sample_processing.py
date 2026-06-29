from __future__ import annotations

from artisanlib.sample_processing import (
    decay_weight_sequence,
    pid_process_value,
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
