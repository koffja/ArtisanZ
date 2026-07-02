from __future__ import annotations

from dataclasses import dataclass

from artisanlib.plot_snapshot import AxisSnapshot, EventMarkerSnapshot, PhaseBandSnapshot
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


class FakeOverlayCanvas(FakeCanvas):
    timeindex = [0, 0, 2, 0, 0, 0, 0, 0]
    watermarksflag = True
    phases = [100.0, 150.0, 190.0, 230.0]
    background = True
    backgroundprofile = object()
    backgroundShowFullflag = False
    autotimex = False
    autotimexMode = 0
    flagon = False
    timeB = [0.0, 1.0, 2.0, 3.0]
    temp1B = [130.0, 131.0, 132.0, 133.0]
    temp2B = [120.0, 121.0, 122.0, 123.0]
    stemp1B = [130.5, 131.5, 132.5, 133.5]
    stemp2B = [120.5, 121.5, 122.5, 123.5]
    delta1B = [None, 2.0, 2.5, None]
    delta2B = [None, 3.0, 3.5, None]
    timeindexB = [1, 0, 0, 0, 0, 0, 2, 0]
    backgroundBTcurve = True
    backgroundETcurve = True
    DeltaBTBflag = True
    DeltaETBflag = True
    backgroundalpha = 0.4
    backgroundbtcolor = '#314E59'
    backgroundmetcolor = '#8B4D3E'
    backgrounddeltabtcolor = '#647A4E'
    backgrounddeltaetcolor = '#98713F'
    BTbacklinestyle = '--'
    ETbacklinestyle = ':'
    BTBdeltalinestyle = '-.'
    ETBdeltalinestyle = '--'
    BTbacklinewidth = 1.5
    ETbacklinewidth = 1.25
    BTBdeltalinewidth = 1.1
    ETBdeltalinewidth = 1.2
    BTprojectFlag = True
    ETprojectFlag = True
    projectDeltaFlag = True
    BTprojection_tx = [2.0, 12.0]
    BTprojection_temp = [144.0, 190.0]
    ETprojection_tx = [2.0, 12.0]
    ETprojection_temp = [152.0, 196.0]
    DeltaBTprojection_tx = [2.0, 12.0]
    DeltaBTprojection_temp = [5.5, 4.5]
    DeltaETprojection_tx = [2.0, 12.0]
    DeltaETprojection_temp = [3.5, 3.0]
    backgroundeventsflag = True
    backgroundEvents = [1]
    backgroundEtypes = [1]
    backgroundEvalues = [45.0]
    backgroundEStrings = ['bg power']
    palette = {
        **FakeCanvas.palette,
        'markers': '#666666',
        'rect1': '#A0A0A0',
        'rect2': '#B0B0B0',
        'rect3': '#C0C0C0',
        'bgeventtext': '#777777',
    }


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


def test_build_roast_plot_snapshot_extracts_overlay_curves_and_phase_bands() -> None:
    snapshot = build_roast_plot_snapshot(FakeOverlayCanvas())
    curves = {curve.name: curve for curve in snapshot.curves}

    assert curves['Background BT'].x == (0.0, 1.0, 2.0, 3.0)
    assert curves['Background BT'].y == (None, 121.5, 122.5, None)
    assert curves['Background BT'].color == '#314E59'
    assert curves['Background BT'].line_style == '--'
    assert curves['Background BT'].opacity == 0.4
    assert curves['Background Delta BT'].y_axis == 'ror'
    assert curves['BT projection'].x == (2.0, 12.0)
    assert curves['BT projection'].y == (144.0, 190.0)
    assert curves['Delta BT projection'].y_axis == 'ror'
    assert snapshot.phase_bands == (
        PhaseBandSnapshot(minimum=100.0, maximum=150.0, color='#A0A0A0', opacity=0.22),
        PhaseBandSnapshot(minimum=150.0, maximum=190.0, color='#B0B0B0', opacity=0.22),
        PhaseBandSnapshot(minimum=190.0, maximum=230.0, color='#C0C0C0', opacity=0.22),
    )


def test_build_roast_plot_snapshot_extracts_main_and_background_event_markers() -> None:
    snapshot = build_roast_plot_snapshot(FakeOverlayCanvas())

    assert snapshot.events[:2] == (
        EventMarkerSnapshot(time=0.0, label='CHARGE', event_type=100, color='#666666', kind='main'),
        EventMarkerSnapshot(time=2.0, label='FCs', event_type=102, color='#666666', kind='main'),
    )
    assert EventMarkerSnapshot(
        time=1.0,
        label='bg power',
        event_type=1,
        color='#222222',
        value=45.0,
        kind='background',
    ) in snapshot.events
