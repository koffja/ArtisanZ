from __future__ import annotations

from dataclasses import dataclass

from artisanlib.plot_snapshot import AxisSnapshot, EventMarkerSnapshot
from artisanlib.plot_snapshot_extractor import build_roast_plot_snapshot


@dataclass
class FakeAxis:
    xlim: tuple[float, float]
    ylim: tuple[float, float]

    def get_xlim(self) -> tuple[float, float]:
        return self.xlim

    def get_ylim(self) -> tuple[float, float]:
        return self.ylim


class FakeCanvas:
    timex = [0, 1, 2]
    temp1 = [150, 151, 152]
    temp2 = [140, 142, 144]
    delta1 = [None, 3.0, 3.5]
    delta2 = [None, 5.0, 5.5]
    ETcurve = True
    BTcurve = True
    DeltaETflag = False
    DeltaBTflag = True
    palette = {
        'et': '#B5644F',
        'bt': '#4E7180',
        'deltaet': '#B98A4B',
        'deltabt': '#78905D',
        'specialeventtext': '#FFFFFF',
    }
    specialevents = [1, 2, 99]
    specialeventstype = [1, 2, 0]
    specialeventsvalue = [55.0, 25.0, 10.0]
    specialeventsStrings = ['power up', '', 'ignored']
    etypes = ['None', 'Power', 'Fan', 'Damper']
    showEtypes = [True, True, True, True]
    EvalueColor = ['#111111', '#222222', '#333333', '#444444']
    ax = FakeAxis(xlim=(-1.0, 12.0), ylim=(70.0, 270.0))
    delta_ax = FakeAxis(xlim=(-1.0, 12.0), ylim=(-15.0, 25.0))


def test_build_roast_plot_snapshot_extracts_main_curves_and_axes() -> None:
    snapshot = build_roast_plot_snapshot(FakeCanvas())

    assert snapshot.time_axis == AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time')
    assert snapshot.temperature_axis == AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature')
    assert snapshot.ror_axis == AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR')
    assert [curve.name for curve in snapshot.curves] == ['BT', 'ET', 'Delta BT', 'Delta ET']
    assert [curve.name for curve in snapshot.visible_curves()] == ['BT', 'ET', 'Delta BT']


def test_build_roast_plot_snapshot_preserves_curve_data_and_visibility() -> None:
    snapshot = build_roast_plot_snapshot(FakeCanvas())
    curves = {curve.name: curve for curve in snapshot.curves}

    assert curves['BT'].x == (0.0, 1.0, 2.0)
    assert curves['BT'].y == (140.0, 142.0, 144.0)
    assert curves['BT'].color == '#4E7180'
    assert curves['BT'].y_axis == 'temperature'
    assert curves['Delta BT'].y == (None, 5.0, 5.5)
    assert curves['Delta BT'].y_axis == 'ror'
    assert curves['Delta ET'].visible is False


def test_build_roast_plot_snapshot_extracts_foreground_event_markers() -> None:
    snapshot = build_roast_plot_snapshot(FakeCanvas())

    assert snapshot.events == (
        EventMarkerSnapshot(time=1.0, label='power up', event_type=1, color='#222222', value=55.0),
        EventMarkerSnapshot(time=2.0, label='Fan', event_type=2, color='#333333', value=25.0),
    )
