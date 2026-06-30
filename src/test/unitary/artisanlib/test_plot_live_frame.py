from __future__ import annotations

import numpy
import pytest
from matplotlib.lines import Line2D

from artisanlib.plot_live_frame import (
    LiveCurveData,
    LivePlotFrame,
    apply_matplotlib_live_curve_data,
    apply_matplotlib_live_frame,
)


class FakeLine:
    def __init__(self) -> None:
        self.x: tuple[float, ...] = ()
        self.y: numpy.ndarray | None = None
        self.calls = 0

    def set_data(self, x: tuple[float, ...], y: numpy.ndarray) -> None:
        self.x = x
        self.y = y
        self.calls += 1


class NoSetDataLine:
    pass


def test_live_curve_data_from_sequences_normalizes_values() -> None:
    curve = LiveCurveData.from_sequences(
        name='Delta BT',
        x=[0, 1.5, 2],
        y=[None, 4, 5.5],
        y_axis='ror',
    )

    assert curve.name == 'Delta BT'
    assert curve.x == (0.0, 1.5, 2.0)
    assert curve.y == (None, 4.0, 5.5)
    assert curve.y_axis == 'ror'


def test_live_curve_data_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match='same length'):
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120])


def test_live_plot_frame_exposes_stable_curve_names() -> None:
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='ET', x=[0], y=[130]),
        LiveCurveData.from_sequences(name='BT', x=[0], y=[120]),
    ))

    assert frame.curve_names() == ('ET', 'BT')


def test_apply_matplotlib_live_curve_data_updates_line_with_numpy_values() -> None:
    line = FakeLine()
    curve = LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, None])

    assert apply_matplotlib_live_curve_data(line, curve) is True

    assert line.x == (0.0, 1.0)
    assert line.y is not None
    assert line.y.tolist() == [120.0, None]
    assert line.calls == 1


def test_apply_matplotlib_live_curve_data_matches_real_line2d_behavior() -> None:
    line = Line2D([], [])
    curve = LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, None])

    assert apply_matplotlib_live_curve_data(line, curve) is True

    assert line.get_xdata() == (0.0, 1.0)
    y_data = line.get_ydata()
    assert isinstance(y_data, numpy.ndarray)
    assert y_data.tolist() == [120.0, None]


def test_apply_matplotlib_live_curve_data_skips_missing_or_incompatible_line() -> None:
    curve = LiveCurveData.from_sequences(name='BT', x=[0], y=[120])

    assert apply_matplotlib_live_curve_data(None, curve) is False
    assert apply_matplotlib_live_curve_data(NoSetDataLine(), curve) is False


def test_apply_matplotlib_live_frame_updates_known_curves_only() -> None:
    et_line = FakeLine()
    bt_line = FakeLine()
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='ET', x=[0, 1], y=[130, 131]),
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, 121]),
        LiveCurveData.from_sequences(name='Delta BT', x=[0, 1], y=[None, 4], y_axis='ror'),
    ))

    applied = apply_matplotlib_live_frame({'ET': et_line, 'BT': bt_line}, frame)

    assert applied == ('ET', 'BT')
    assert et_line.y is not None
    assert et_line.y.tolist() == [130.0, 131.0]
    assert bt_line.y is not None
    assert bt_line.y.tolist() == [120.0, 121.0]
