from __future__ import annotations

from artisanlib.sample_processing import decay_weight_sequence, smoothing_weights_for_recent_readings


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
