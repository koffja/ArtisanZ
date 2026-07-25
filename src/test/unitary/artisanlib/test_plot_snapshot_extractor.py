from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from artisanlib.plot_snapshot import (
    AnalysisMaskSnapshot,
    AreaFillSnapshot,
    AxisSnapshot,
    EventMarkerSnapshot,
    EventValueSnapshot,
    GuideLineSnapshot,
    PhaseBandSnapshot,
    PhaseSummarySnapshot,
    RoRFlickAnnotationSnapshot,
    StatisticsBackgroundSnapshot,
    TimeRangeSnapshot,
)
from artisanlib import plot_snapshot_extractor
from artisanlib.plot_snapshot_extractor import build_roast_plot_snapshot, build_roast_plot_static_overlay_snapshot


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
    EvalueMarker = ['o', 's', 'h', 'D']
    EvalueMarkerSize = [4.0, 5.0, 6.0, 7.0]
    Evaluelinethickness = [1.0, 1.5, 2.0, 2.5]
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
    AUCguideFlag = True
    AUCguideTime = 10.0
    endofx = 12.0
    compareBBP = True
    BBPindex = 1
    charge_manager = type('FakeChargeManager', (), {'enabled': True, 'target_temp': 182.0})()
    palette = {
        **FakeCanvas.palette,
        'markers': '#666666',
        'rect1': '#A0A0A0',
        'rect2': '#B0B0B0',
        'rect3': '#C0C0C0',
        'bgeventtext': '#777777',
        'aucguide': '#336677',
        'timeguide': '#557766',
    }


class FakeAucAw:
    @staticmethod
    def findTP() -> int:
        return 1


class FakeAucTsAw(FakeAucAw):
    @staticmethod
    def ts() -> tuple[None, None, None, int]:
        return (None, None, None, 2)


class FakeCompletedAw:
    @staticmethod
    def findTP() -> int:
        return 2


class FakeAucCanvas(FakeCanvas):
    timex = [0.0, 60.0, 120.0, 180.0]
    temp1 = [130.0, 140.0, 155.0, 175.0]
    temp2 = [120.0, 130.0, 150.0, 170.0]
    stemp2 = [120.0, 130.0, 150.0, 170.0]
    delta1 = [None, 4.0, 5.0, 4.5]
    delta2 = [None, 5.0, 6.0, 5.0]
    timeindex = [0, 0, 0, 0, 0, 0, 3, 0]
    AUCshowFlag = True
    AUCbaseFlag = False
    AUCbase = 135.0
    flagon = False
    aw = FakeAucAw()
    palette = {
        **FakeCanvas.palette,
        'aucarea': '#767676',
    }


class FakeCompletedRoastCanvas(FakeOverlayCanvas):
    timex = [float(index * 60) for index in range(11)]
    temp1 = [160.0, 155.0, 150.0, 160.0, 170.0, 180.0, 190.0, 200.0, 210.0, 218.0, 215.0]
    temp2 = [150.0, 130.0, 110.0, 125.0, 140.0, 155.0, 170.0, 185.0, 200.0, 208.0, 212.0]
    delta1 = [None, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 4.8, 4.2, 3.8, 3.0]
    delta2 = [None, 1.2, 2.2, 3.2, 4.2, 4.6, 5.2, 4.9, 4.4, 3.9, 3.2]
    stemp2 = temp2
    timeindex = [0, 3, 7, 0, 0, 0, 10, 0]
    flagon = False
    markTPflag = True
    mode = 'F'
    delay = 1000
    statisticsflags = [True, True, True, True]
    aw = FakeCompletedAw()
    palette = {
        **FakeOverlayCanvas.palette,
        'roastphasetext': '#20272B',
        'roastphase1': '#DDE8E0',
        'roastphase2': '#E7DEC9',
        'roastphase3': '#F4F2EC',
    }


class FakeRecordedExtraCanvas(FakeCompletedRoastCanvas):
    extradevices = [127]
    extratimex = [[0.0, 60.0, 120.0, 180.0]]
    extratemp1 = [[150.0, 155.0, 160.0, 165.0]]
    extratemp2 = [[100.0, 105.0, 110.0, 115.0]]
    extrastemp1 = extratemp1
    extrastemp2 = extratemp2
    extraname1 = ['Exhaust']
    extraname2 = ['Inlet']
    extradevicecolor1 = ['#B87968']
    extradevicecolor2 = ['#668B95']
    extralinestyles1 = ['--']
    extralinestyles2 = [':']
    extralinewidths1 = [2.0]
    extralinewidths2 = [1.5]
    aw = SimpleNamespace(
        findTP=lambda: 2,
        extraCurveVisibility1=[True],
        extraCurveVisibility2=[False],
        extraDelta1=[False],
        extraDelta2=[False],
    )


class FakeAnalysisCanvas(FakeCompletedRoastCanvas):
    analysisresultsstr = 'Fit result'
    segmentresultstr = 'Segment result'
    analysisresultsloc = (0.25, 0.60)
    segmentresultsloc = (0.50, 0.40)
    curvefit_starttime = 120.0
    curvefit_endtime = 600.0
    analysis_starttime = 240.0
    analysis_endtime = 600.0
    alpha = {'analysismask': 0.4, 'statsanalysisbkgnd': 0.75}
    phase_labels = {'drying': '烘焙前段', 'maillard': '梅拉德', 'development': '发展段'}
    palette = {
        **FakeCompletedRoastCanvas.palette,
        'analysismask': '#D6D1C6',
        'statsanalysisbkgnd': '#FFFDF8',
        'text': '#20272B',
    }


def test_build_roast_plot_snapshot_extracts_main_curves_and_axes() -> None:
    snapshot = build_roast_plot_snapshot(FakeCanvas())

    assert snapshot.time_axis == AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time')
    assert snapshot.temperature_axis == AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature')
    assert snapshot.ror_axis == AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR')
    assert [curve.name for curve in snapshot.curves] == ['BT', 'ET', 'Delta BT', 'Delta ET']
    assert [curve.name for curve in snapshot.visible_curves()] == ['BT', 'ET', 'Delta BT']


def test_default_background_opacity_is_visible() -> None:
    assert pytest.approx(0.35) == plot_snapshot_extractor.DEFAULT_BACKGROUND_OPACITY
    assert plot_snapshot_extractor._opacity(
        SimpleNamespace(),
        'backgroundalpha',
        plot_snapshot_extractor.DEFAULT_BACKGROUND_OPACITY,
    ) == pytest.approx(0.35)


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
        EventMarkerSnapshot(time=1.0, label='power up', event_type=1, color='#222222', value=55.0, source_index=0),
        EventMarkerSnapshot(time=2.0, label='Fan', event_type=2, color='#333333', value=25.0, source_index=1),
    )
    assert snapshot.event_values == (
        EventValueSnapshot(time=1.0, value=55.0, event_type=1, color='#222222', label='power up', marker='s', marker_size=5.0, line_width=1.5),
        EventValueSnapshot(time=2.0, value=25.0, event_type=2, color='#333333', label='Fan', marker='h', marker_size=6.0, line_width=2.0),
    )


def test_build_roast_plot_snapshot_extracts_overlay_curves_and_phase_bands(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(plot_snapshot_extractor, '_settings_float', lambda _keys, default: default)
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
    assert len(snapshot.projection_bands) == 2
    assert snapshot.projection_bands[0].lower[0] == pytest.approx(144.0)
    assert snapshot.projection_bands[0].upper[-1] > snapshot.projection_bands[0].lower[-1]
    assert snapshot.phase_bands == (
        PhaseBandSnapshot(minimum=100.0, maximum=150.0, color='#A0A0A0', opacity=0.3),
        PhaseBandSnapshot(minimum=150.0, maximum=190.0, color='#B0B0B0', opacity=0.3),
        PhaseBandSnapshot(minimum=190.0, maximum=230.0, color='#C0C0C0', opacity=0.3),
    )


def test_build_roast_plot_snapshot_extracts_selected_background_extra_curves() -> None:
    class FakeExtraBackgroundCanvas(FakeOverlayCanvas):
        xtcurveidx = 1
        ytcurveidx = 4
        extraname1B = ['Drum', 'Air']
        extraname2B = ['Power', 'Damper']
        extratimexB = [[0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 2.0, 3.0]]
        temp1BX = [[100.0, 101.0, 102.0, 103.0], [200.0, 201.0, 202.0, 203.0]]
        temp2BX = [[10.0, 11.0, 12.0, 13.0], [20.0, 21.0, 22.0, 23.0]]
        stemp1BX = [[110.0, 111.0, 112.0, 113.0], [210.0, 211.0, 212.0, 213.0]]
        stemp2BX = [[15.0, 16.0, 17.0, 18.0], [25.0, 26.0, 27.0, 28.0]]
        backgroundxtcolor = '#123456'
        backgroundytcolor = '#654321'
        XTbacklinestyle = ':'
        YTbacklinestyle = '-.'
        XTbacklinewidth = 1.25
        YTbacklinewidth = 1.75
        aw = SimpleNamespace(extraDelta1b=[True, False], extraDelta2b=[False, False])

    snapshot = build_roast_plot_snapshot(FakeExtraBackgroundCanvas())
    curves = {curve.name: curve for curve in snapshot.curves}

    assert curves['Background XT'].x == (0.0, 1.0, 2.0, 3.0)
    assert curves['Background XT'].y == (None, 111.0, 112.0, None)
    assert curves['Background XT'].y_axis == 'ror'
    assert curves['Background XT'].color == '#123456'
    assert curves['Background XT'].line_style == ':'
    assert curves['Background XT'].line_width == 1.25
    assert curves['Background XT'].opacity == 0.4

    assert curves['Background YT'].x == (0.0, 1.0, 2.0, 3.0)
    assert curves['Background YT'].y == (None, 26.0, 27.0, None)
    assert curves['Background YT'].y_axis == 'temperature'
    assert curves['Background YT'].color == '#654321'
    assert curves['Background YT'].line_style == '-.'
    assert curves['Background YT'].line_width == 1.75
    assert curves['Background YT'].opacity == 0.4


def test_build_roast_plot_snapshot_uses_selected_background_extra_curve_pair() -> None:
    class FakeExtraBackgroundCanvas(FakeOverlayCanvas):
        xtcurveidx = 2
        ytcurveidx = 1
        extratimexB = [[0.0, 1.0, 2.0]]
        temp1BX = [[100.0, 101.0, 102.0]]
        temp2BX = [[200.0, 201.0, 202.0]]
        stemp1BX = [[110.0, 111.0, 112.0]]
        stemp2BX = [[210.0, 211.0, 212.0]]
        aw = SimpleNamespace(extraDelta1b=[False], extraDelta2b=[True])

    snapshot = build_roast_plot_snapshot(FakeExtraBackgroundCanvas())
    curves = {curve.name: curve for curve in snapshot.curves}

    assert curves['Background XT'].y == (None, 211.0, 212.0)
    assert curves['Background XT'].y_axis == 'ror'
    assert curves['Background YT'].y == (None, 111.0, 112.0)
    assert curves['Background YT'].y_axis == 'temperature'


@pytest.mark.parametrize(
    ('selection', 'expected'),
    [(1, (None, 111.0, 112.0)), (2, (None, 211.0, 212.0)), (3, (None, 311.0, 312.0))],
)
def test_build_roast_plot_snapshot_maps_extra_background_selection(
        selection: int, expected: tuple[float | None, ...]) -> None:
    class FakeExtraBackgroundCanvas(FakeOverlayCanvas):
        xtcurveidx = selection
        ytcurveidx = 0
        extratimexB = [[0.0, 1.0, 2.0], [0.0, 1.0, 2.0]]
        temp1BX = [[100.0, 101.0, 102.0], [300.0, 301.0, 302.0]]
        temp2BX = [[200.0, 201.0, 202.0], [400.0, 401.0, 402.0]]
        stemp1BX = [[110.0, 111.0, 112.0], [310.0, 311.0, 312.0]]
        stemp2BX = [[210.0, 211.0, 212.0], [410.0, 411.0, 412.0]]
        aw = SimpleNamespace(extraDelta1b=[False, False], extraDelta2b=[False, False])

    snapshot = build_roast_plot_snapshot(FakeExtraBackgroundCanvas())
    curves = {curve.name: curve for curve in snapshot.curves}
    assert curves['Background XT'].y == expected


def test_build_roast_plot_snapshot_handles_invalid_extra_background_state() -> None:
    class FakeInvalidExtraBackgroundCanvas(FakeOverlayCanvas):
        xtcurveidx = float('inf')
        ytcurveidx = 1
        extratimexB = None
        temp1BX = None
        stemp1BX = None
        aw = SimpleNamespace(extraDelta1b=None)

    snapshot = build_roast_plot_snapshot(FakeInvalidExtraBackgroundCanvas())
    assert all(curve.name != 'Background XT' for curve in snapshot.curves)
    assert all(curve.name != 'Background YT' for curve in snapshot.curves)


@pytest.mark.parametrize('selection', [0, -1, 1.5, 2.5, 99])
def test_build_roast_plot_snapshot_skips_invalid_extra_background_selection(selection: float) -> None:
    class FakeInvalidSelectionCanvas(FakeOverlayCanvas):
        xtcurveidx = selection
        ytcurveidx = 0
        extratimexB = [[0.0, 1.0]]
        temp1BX = [[100.0, 101.0]]
        stemp1BX = [[100.0, 101.0]]

    snapshot = build_roast_plot_snapshot(FakeInvalidSelectionCanvas())
    assert all(curve.name != 'Background XT' for curve in snapshot.curves)


def test_build_roast_plot_snapshot_keeps_extra_delta_on_temperature_axis_without_delta_axis() -> None:
    class FakeNoDeltaAxisCanvas(FakeOverlayCanvas):
        xtcurveidx = 1
        ytcurveidx = 0
        extratimexB = [[0.0, 1.0, 2.0, 3.0]]
        temp1BX = [[100.0, 101.0, 102.0, 103.0]]
        stemp1BX = [[110.0, 111.0, 112.0, 113.0]]
        aw = SimpleNamespace(extraDelta1b=[True])
        delta_ax = None

    snapshot = build_roast_plot_snapshot(FakeNoDeltaAxisCanvas())
    curves = {curve.name: curve for curve in snapshot.curves}
    assert curves['Background XT'].y_axis == 'temperature'


def test_projection_curves_match_matplotlib_style_and_delta_axis_visibility() -> None:
    class AllProjectionCanvas(FakeOverlayCanvas):
        DeltaETflag = True

    snapshot = build_roast_plot_snapshot(AllProjectionCanvas())
    projections = {curve.name: curve for curve in snapshot.curves if 'projection' in curve.name.lower()}

    assert set(projections) == {
        'BT projection',
        'ET projection',
        'Delta BT projection',
        'Delta ET projection',
    }
    assert projections['BT projection'].y_axis == 'temperature'
    assert projections['ET projection'].y_axis == 'temperature'
    assert projections['Delta BT projection'].y_axis == 'ror'
    assert projections['Delta ET projection'].y_axis == 'ror'
    for curve in projections.values():
        assert curve.visible is True
        assert curve.line_style == '-.'
        assert curve.line_width == 8.0
        assert curve.opacity == pytest.approx(0.3)

    class NoDeltaAxisCanvas(AllProjectionCanvas):
        delta_ax = None

    no_delta_axis = build_roast_plot_snapshot(NoDeltaAxisCanvas())
    assert [curve.name for curve in no_delta_axis.curves if 'projection' in curve.name.lower()] == [
        'BT projection',
        'ET projection',
    ]


def test_build_roast_plot_static_overlay_snapshot_keeps_static_curve_payload() -> None:
    static_snapshot = build_roast_plot_static_overlay_snapshot(
        FakeOverlayCanvas(),
        time_axis=AxisSnapshot(minimum=0.0, maximum=12.0, label='Live Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Live Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='Live RoR'),
    )
    full_snapshot = build_roast_plot_snapshot(FakeOverlayCanvas())

    curve_names = [curve.name for curve in static_snapshot.curves]
    assert {'Background BT', 'Background ET', 'Background Delta BT', 'Background Delta ET'}.issubset(curve_names)
    assert not {'BT', 'ET', 'Delta BT', 'Delta ET'}.intersection(curve_names)
    assert static_snapshot.curves == tuple(
        curve for curve in full_snapshot.curves
        if curve.name.startswith('Background ') or 'projection' in curve.name.lower()
    )
    assert static_snapshot.time_axis == AxisSnapshot(minimum=0.0, maximum=12.0, label='Live Time')
    assert static_snapshot.temperature_axis == AxisSnapshot(minimum=70.0, maximum=270.0, label='Live Temperature')
    assert static_snapshot.ror_axis == AxisSnapshot(minimum=-15.0, maximum=25.0, label='Live RoR')
    assert static_snapshot.events == full_snapshot.events
    assert static_snapshot.event_values == full_snapshot.event_values
    assert static_snapshot.phase_bands == full_snapshot.phase_bands
    assert static_snapshot.guides == full_snapshot.guides
    assert static_snapshot.areas == full_snapshot.areas


def test_build_roast_plot_snapshot_extracts_main_and_background_event_markers() -> None:
    snapshot = build_roast_plot_snapshot(FakeOverlayCanvas())

    assert snapshot.events[:2] == (
        EventMarkerSnapshot(time=0.0, label='CHARGE', event_type=100, color='#666666', temperature=140.0, kind='main'),
        EventMarkerSnapshot(time=2.0, label='FCs 0:02', event_type=102, color='#666666', temperature=144.0, kind='main'),
    )
    assert EventMarkerSnapshot(
        time=1.0,
        label='bg power',
        event_type=1,
        color='#222222',
        value=45.0,
        kind='background',
    ) in snapshot.events
    assert EventValueSnapshot(
        time=1.0,
        value=45.0,
        event_type=1,
        color='#222222',
        label='bg power',
        kind='background',
        opacity=0.34,
        marker='s',
        marker_size=5.0,
        line_width=1.5,
    ) in snapshot.event_values


def test_build_roast_plot_snapshot_translates_main_event_markers(
        monkeypatch: pytest.MonkeyPatch) -> None:
    translations = {
        ('Label', 'CHARGE'): '投豆',
        ('Label', 'FCs'): '一爆开始',
    }

    def translate(context: str, text: str) -> str:
        return translations.get((context, text), text)

    monkeypatch.setattr(
        plot_snapshot_extractor,
        'QApplication',
        SimpleNamespace(translate=translate),
        raising=False,
    )

    snapshot = build_roast_plot_snapshot(FakeOverlayCanvas())

    assert snapshot.events[:2] == (
        EventMarkerSnapshot(time=0.0, label='投豆', event_type=100, color='#666666', temperature=140.0, kind='main'),
        EventMarkerSnapshot(time=2.0, label='一爆开始 0:02', event_type=102, color='#666666', temperature=144.0, kind='main'),
    )


def test_build_roast_plot_snapshot_extracts_completed_phase_summary_and_phase_ranges() -> None:
    snapshot = build_roast_plot_snapshot(FakeCompletedRoastCanvas())

    assert snapshot.time_ranges == (
        TimeRangeSnapshot(
            start=0.0,
            end=180.0,
            color='#A0A0A0',
            opacity=0.28,
            label='Drying',
            kind='drying',
        ),
        TimeRangeSnapshot(
            start=180.0,
            end=420.0,
            color='#B0B0B0',
            opacity=0.28,
            label='Maillard',
            kind='maillard',
        ),
        TimeRangeSnapshot(
            start=420.0,
            end=600.0,
            color='#C0C0C0',
            opacity=0.28,
            label='Development',
            kind='development',
        ),
    )
    assert snapshot.phase_summaries == (
        PhaseSummarySnapshot(
            start=0.0,
            end=180.0,
            label='Drying',
            duration_text='3:00',
            percent_text='30.0%',
            delta_text='15.0F',
            color='#DDE8E0',
        ),
        PhaseSummarySnapshot(
            start=180.0,
            end=420.0,
            label='Maillard',
            duration_text='4:00',
            percent_text='40.0%',
            delta_text='60.0F',
            color='#E7DEC9',
        ),
        PhaseSummarySnapshot(
            start=420.0,
            end=600.0,
            label='Development',
            duration_text='3:00',
            percent_text='30.0%',
            delta_text='27.0F',
            color='#F4F2EC',
        ),
    )


def test_build_roast_plot_snapshot_extracts_recorded_extra_curves_and_visibility() -> None:
    snapshot = build_roast_plot_snapshot(FakeRecordedExtraCanvas())
    curves = {curve.name: curve for curve in snapshot.curves}

    assert curves['Exhaust'].x == (0.0, 60.0, 120.0, 180.0)
    assert curves['Exhaust'].line_style == '--'
    assert curves['Exhaust'].line_width == 2.0
    assert curves['Exhaust'].visible
    assert curves['Inlet'].line_style == ':'
    assert not curves['Inlet'].visible


def test_build_roast_plot_snapshot_keeps_duplicate_extra_names_unique() -> None:
    class DuplicateExtraCanvas(FakeRecordedExtraCanvas):
        extradevices = [127, 128]
        extratimex = [FakeRecordedExtraCanvas.extratimex[0], FakeRecordedExtraCanvas.extratimex[0]]
        extratemp1 = [FakeRecordedExtraCanvas.extratemp1[0], FakeRecordedExtraCanvas.extratemp1[0]]
        extratemp2 = [FakeRecordedExtraCanvas.extratemp2[0], FakeRecordedExtraCanvas.extratemp2[0]]
        extrastemp1 = extratemp1
        extrastemp2 = extratemp2
        extraname1 = ['Exhaust', 'Exhaust']
        extraname2 = ['Inlet', 'Inlet']
        extradevicecolor1 = ['#B87968', '#B87968']
        extradevicecolor2 = ['#668B95', '#668B95']
        extralinestyles1 = ['-', '-']
        extralinestyles2 = ['-', '-']
        extralinewidths1 = [1.0, 1.0]
        extralinewidths2 = [1.0, 1.0]
        aw = SimpleNamespace(
            findTP=lambda: 2,
            extraCurveVisibility1=[True, True],
            extraCurveVisibility2=[True, True],
            extraDelta1=[False, False],
            extraDelta2=[False, False],
        )

    names = [curve.name for curve in build_roast_plot_snapshot(DuplicateExtraCanvas()).curves]

    assert len(names) == len(set(names))


def test_build_roast_plot_snapshot_keeps_partial_phase_ranges_during_live_roast() -> None:
    source = FakeCompletedRoastCanvas()
    source.timeindex = [0, 3, 0, 0, 0, 0, 0, 0]

    snapshot = build_roast_plot_snapshot(source)

    assert snapshot.time_ranges == (
        TimeRangeSnapshot(
            start=0.0,
            end=180.0,
            color='#A0A0A0',
            opacity=0.28,
            label='Drying',
            kind='drying',
        ),
    )


def test_time_ranges_keep_charge_origin_and_reject_missing_or_non_monotonic_data() -> None:
    class ChargeNotStartedCanvas(FakeCompletedRoastCanvas):
        timeindex = [-1, 3, 0, 0, 0, 0, 0, 0]

    assert plot_snapshot_extractor._time_ranges(ChargeNotStartedCanvas()) == (
        TimeRangeSnapshot(
            start=0.0,
            end=180.0,
            color='#A0A0A0',
            opacity=0.28,
            label='Drying',
            kind='drying',
        ),
    )

    class MissingSequenceCanvas:
        timeindex = None
        timex = None

    assert plot_snapshot_extractor._time_ranges(MissingSequenceCanvas()) == ()

    class NonMonotonicCanvas(FakeCompletedRoastCanvas):
        timeindex = [0, 8, 7, 0, 0, 0, 10, 0]

    non_monotonic = plot_snapshot_extractor._time_ranges(NonMonotonicCanvas())
    assert non_monotonic == (
        TimeRangeSnapshot(
            start=0.0,
            end=480.0,
            color='#A0A0A0',
            opacity=0.28,
            label='Drying',
            kind='drying',
        ),
    )


def test_build_roast_plot_snapshot_extracts_analysis_masks_backgrounds_and_guides() -> None:
    snapshot = build_roast_plot_snapshot(FakeAnalysisCanvas())

    assert snapshot.analysis_masks == (
        AnalysisMaskSnapshot(
            curvefit_start=120.0,
            curvefit_end=600.0,
            analysis_start=240.0,
            analysis_end=600.0,
            color='#D6D1C6',
            opacity=0.2,
        ),
    )
    assert snapshot.statistics_backgrounds == (
        StatisticsBackgroundSnapshot(
            text='Segment result',
            position=(0.50, 0.40),
            color='#FFFDF8',
            text_color='#20272B',
            opacity=0.75,
            kind='segment',
            z_value=30.0,
        ),
        StatisticsBackgroundSnapshot(
            text='Fit result',
            position=(0.25, 0.60),
            color='#FFFDF8',
            text_color='#20272B',
            opacity=0.75,
            kind='analysis',
            z_value=31.0,
        ),
    )
    assert [guide.position for guide in snapshot.guides if guide.kind == 'analysis'] == [
        120.0, 600.0, 240.0, 600.0,
    ]


def test_build_roast_plot_snapshot_skips_empty_and_invalid_analysis_overlays() -> None:
    empty = build_roast_plot_snapshot(FakeCanvas())
    assert empty.analysis_masks == ()
    assert empty.statistics_backgrounds == ()
    assert all(guide.kind != 'analysis' for guide in empty.guides)

    class InvalidAnalysisCanvas(FakeAnalysisCanvas):
        curvefit_starttime = float('nan')
        curvefit_endtime = -1
        analysis_starttime = 700.0
        analysis_endtime = 600.0

    invalid = build_roast_plot_snapshot(InvalidAnalysisCanvas())
    assert invalid.analysis_masks == ()
    assert all(guide.kind != 'analysis' for guide in invalid.guides)
    assert len(invalid.statistics_backgrounds) == 2


def test_build_roast_plot_snapshot_rejects_invalid_phase_indexes_and_times() -> None:
    class InvalidPhaseIndexCanvas(FakeCompletedRoastCanvas):
        timeindex = [0, 99, 7, 0, 0, 0, 10, 0]

    invalid_index = build_roast_plot_snapshot(InvalidPhaseIndexCanvas())
    assert invalid_index.phase_summaries == ()
    assert invalid_index.time_ranges == ()

    class InvalidPhaseTimeCanvas(FakeCompletedRoastCanvas):
        timex = [0.0, 60.0, 120.0, 180.0, 240.0, 300.0, 360.0, float('nan'), 480.0, 540.0, 600.0]

    invalid_time = build_roast_plot_snapshot(InvalidPhaseTimeCanvas())
    assert invalid_time.phase_summaries == ()
    assert invalid_time.time_ranges == (
        TimeRangeSnapshot(
            start=0.0,
            end=180.0,
            color='#A0A0A0',
            opacity=0.28,
            label='Drying',
            kind='drying',
        ),
    )


def test_analysis_overlay_opacity_rejects_nonfinite_values() -> None:
    class NonfiniteAlphaCanvas(FakeAnalysisCanvas):
        alpha = {'analysismask': float('nan'), 'statsanalysisbkgnd': float('inf')}

    snapshot = build_roast_plot_snapshot(NonfiniteAlphaCanvas())
    assert snapshot.analysis_masks[0].opacity == pytest.approx(0.2)
    assert all(background.opacity == pytest.approx(1.0) for background in snapshot.statistics_backgrounds)


def test_statistics_backgrounds_do_not_read_stale_matplotlib_annotations() -> None:
    class StaleAnnotation:
        @staticmethod
        def get_text() -> str:
            return 'stale result'

    class StaleAnnotationCanvas(FakeCompletedRoastCanvas):
        aw = SimpleNamespace(
            findTP=lambda: 2,
            analysisresultsanno=StaleAnnotation(),
            segmentresultsanno=StaleAnnotation(),
        )

    snapshot = build_roast_plot_snapshot(StaleAnnotationCanvas())
    assert snapshot.statistics_backgrounds == ()


def test_phase_summary_uses_label_i18n_for_development(monkeypatch: pytest.MonkeyPatch) -> None:
    translations = {('Label', 'Development'): '发展期'}

    def translate(context: str, text: str) -> str:
        return translations.get((context, text), text)

    monkeypatch.setattr(
        plot_snapshot_extractor,
        'QApplication',
        SimpleNamespace(translate=translate),
        raising=False,
    )
    summaries = build_roast_plot_snapshot(FakeCompletedRoastCanvas()).phase_summaries
    assert summaries[-1].label == '发展期'


def test_phase_summary_reuses_existing_snapshot_with_source_visibility_and_labels() -> None:
    class ConfiguredPhaseCanvas(FakeCompletedRoastCanvas):
        statisticsflags = [False, True, True, True]
        aw = SimpleNamespace(findTP=lambda: 2, percent_decimals=0)
        phase_labels = {'drying': '烘焙前段', 'maillard': '梅拉德', 'development': '发展段'}

    summaries = build_roast_plot_snapshot(ConfiguredPhaseCanvas()).phase_summaries

    assert len(summaries) == 3
    assert [summary.label for summary in summaries] == ['烘焙前段', '梅拉德', '发展段']
    assert all(summary.bar_visible for summary in summaries)
    assert all(not summary.label_visible for summary in summaries)
    assert summaries[0].percent_text.endswith('%')


def test_phase_summary_visibility_flags_are_independent() -> None:
    class HiddenLabelsAndDelta(FakeCompletedRoastCanvas):
        statisticsflags = [False, True, True, True, False, False, False]

    hidden = build_roast_plot_snapshot(HiddenLabelsAndDelta()).phase_summaries
    assert all(summary.bar_visible for summary in hidden)
    assert all(not summary.label_visible for summary in hidden)
    assert all(not summary.delta_visible for summary in hidden)

    class HiddenBarsOnly(FakeCompletedRoastCanvas):
        statisticsflags = [True, False, True, True, False, False, True]

    bars_hidden = build_roast_plot_snapshot(HiddenBarsOnly()).phase_summaries
    assert all(not summary.bar_visible for summary in bars_hidden)
    assert all(summary.label_visible for summary in bars_hidden)
    assert all(summary.delta_visible for summary in bars_hidden)


def test_phase_summary_respects_statistics_summary_master_switch() -> None:
    class SummaryDisabledCanvas(FakeCompletedRoastCanvas):
        statssummary = False
        flagon = True

    assert build_roast_plot_snapshot(SummaryDisabledCanvas()).phase_summaries == ()


def test_completed_phase_summary_recovers_legacy_disabled_master_switch() -> None:
    class LegacyCompletedCanvas(FakeCompletedRoastCanvas):
        statssummary = False

    assert len(build_roast_plot_snapshot(LegacyCompletedCanvas()).phase_summaries) == 3


def test_completed_phase_summary_accepts_charge_before_first_sample() -> None:
    class PrechargeCompletedCanvas(FakeCompletedRoastCanvas):
        timeindex = [-1, 3, 7, 0, 0, 0, 10, 0]

    snapshot = build_roast_plot_snapshot(PrechargeCompletedCanvas())

    assert len(snapshot.phase_summaries) == 3


def test_build_roast_plot_snapshot_extracts_turning_point_marker() -> None:
    snapshot = build_roast_plot_snapshot(FakeCompletedRoastCanvas())

    assert EventMarkerSnapshot(
        time=120.0,
        label='TP 2:00',
        event_type=99,
        color='#666666',
        temperature=110.0,
        kind='main',
    ) in snapshot.events


def test_build_roast_plot_snapshot_limits_ror_axis_to_visible_saved_profile_values() -> None:
    snapshot = build_roast_plot_snapshot(FakeCompletedRoastCanvas())
    curves = {curve.name: curve for curve in snapshot.curves}

    assert curves['Delta BT'].y == (None, None, None, None, None, 4.6, 5.2, 4.9, None, None, None)
    assert snapshot.ror_axis is not None
    assert snapshot.ror_axis.maximum >= 5.2


def test_build_roast_plot_snapshot_extracts_guides_when_source_data_exists() -> None:
    snapshot = build_roast_plot_snapshot(FakeOverlayCanvas())

    assert GuideLineSnapshot(
        position=10.0,
        label='AUC guide',
        color='#336677',
        orientation='vertical',
        line_style='-',
        opacity=0.5,
        kind='auc',
    ) in snapshot.guides
    assert GuideLineSnapshot(
        position=1.0,
        label='BBP',
        color='#557766',
        orientation='vertical',
        line_style='--',
        opacity=0.45,
        kind='bbp',
    ) in snapshot.guides
    assert GuideLineSnapshot(
        position=182.0,
        label='Charge target',
        color='#B4685C',
        orientation='horizontal',
        line_style='--',
        opacity=0.42,
        kind='charge_target',
    ) in snapshot.guides


def test_rorflick_annotations_returns_empty_when_manager_disabled() -> None:
    source = SimpleNamespace(
        timex=[0.0, 1.0, 2.0],
        delta2=[None, 5.0, 6.0],
        rorflick_manager=SimpleNamespace(enabled=False, events=(
            SimpleNamespace(
                start_idx=0,
                end_idx=2,
                peak_idx=1,
                event_type='flick',
                severity='soft',
                peak_magnitude=3.0,
                in_development=False,
            ),
        )),
    )

    assert plot_snapshot_extractor._rorflick_annotations(source) == ()


def test_rorflick_annotations_extracts_single_event_coordinates() -> None:
    source = SimpleNamespace(
        timex=[0.0, 60.0, 120.0, 180.0],
        delta2=[None, 4.0, 13.5, 5.0],
        rorflick_manager=SimpleNamespace(enabled=True, events=(
            SimpleNamespace(
                start_idx=1,
                end_idx=3,
                peak_idx=2,
                event_type='flick',
                severity='hard',
                peak_magnitude=8.4,
                in_development=True,
            ),
        )),
    )

    assert plot_snapshot_extractor._rorflick_annotations(source) == (
        RoRFlickAnnotationSnapshot(
            enabled=True,
            start_time=60.0,
            end_time=180.0,
            peak_time=120.0,
            peak_value=13.5,
            event_type='flick',
            severity='hard',
            peak_magnitude=8.4,
            in_development=True,
        ),
    )


def test_rorflick_annotations_skips_events_with_out_of_bounds_indices() -> None:
    source = SimpleNamespace(
        timex=[0.0, 60.0],
        delta2=[None, 4.0],
        rorflick_manager=SimpleNamespace(enabled=True, events=(
            SimpleNamespace(
                start_idx=0,
                end_idx=3,
                peak_idx=1,
                event_type='crash',
                severity='moderate',
                peak_magnitude=4.2,
                in_development=False,
            ),
        )),
    )

    assert plot_snapshot_extractor._rorflick_annotations(source) == ()


def test_rorflick_annotations_returns_empty_when_timex_is_none() -> None:
    source = SimpleNamespace(
        timex=None,
        delta2=[None, 4.0],
        rorflick_manager=SimpleNamespace(enabled=True, events=(
            SimpleNamespace(
                start_idx=0,
                end_idx=1,
                peak_idx=1,
                event_type='flick',
                severity='soft',
                peak_magnitude=2.4,
                in_development=False,
            ),
        )),
    )

    assert plot_snapshot_extractor._rorflick_annotations(source) == ()


def test_build_roast_plot_snapshot_extracts_auc_area_fill() -> None:
    snapshot = build_roast_plot_snapshot(FakeAucCanvas())

    assert snapshot.areas == (
        AreaFillSnapshot.from_sequences(
            x=[60.0, 120.0, 180.0],
            y=[130.0, 150.0, 170.0],
            baseline=130.0,
            color='#767676',
            label='AUC area',
            opacity=0.28,
            kind='auc',
        ),
    )


def test_build_roast_plot_snapshot_skips_auc_area_before_drop() -> None:
    class Canvas(FakeAucCanvas):
        timeindex = [0, 0, 0, 0, 0, 0, 0, 0]

    snapshot = build_roast_plot_snapshot(Canvas())

    assert snapshot.areas == ()


def test_build_roast_plot_snapshot_skips_auc_area_when_disabled() -> None:
    class Canvas(FakeAucCanvas):
        AUCshowFlag = False

    snapshot = build_roast_plot_snapshot(Canvas())

    assert snapshot.areas == ()


def test_build_roast_plot_snapshot_skips_auc_area_while_recording() -> None:
    class Canvas(FakeAucCanvas):
        flagon = True

    snapshot = build_roast_plot_snapshot(Canvas())

    assert snapshot.areas == ()


def test_build_roast_plot_snapshot_uses_auc_ts_base_index() -> None:
    class Canvas(FakeAucCanvas):
        AUCbaseFlag = True
        aw = FakeAucTsAw()

    snapshot = build_roast_plot_snapshot(Canvas())

    assert snapshot.areas == (
        AreaFillSnapshot.from_sequences(
            x=[120.0, 180.0],
            y=[150.0, 170.0],
            baseline=150.0,
            color='#767676',
            label='AUC area',
            opacity=0.28,
            kind='auc',
        ),
    )


def test_build_roast_plot_snapshot_keeps_auc_base_offsets_with_invalid_samples() -> None:
    class Canvas(FakeAucCanvas):
        stemp2 = [120.0, -1.0, 150.0, 170.0]

    snapshot = build_roast_plot_snapshot(Canvas())

    assert snapshot.areas == (
        AreaFillSnapshot.from_sequences(
            x=[120.0, 180.0],
            y=[150.0, 170.0],
            baseline=150.0,
            color='#767676',
            label='AUC area',
            opacity=0.28,
            kind='auc',
        ),
    )


def test_charge_target_annotations_disabled_returns_empty():
    """When charge_manager.enabled is False, the extractor returns an empty tuple."""
    from artisanlib.plot_snapshot_extractor import _charge_target_annotations
    class FakeManager:
        enabled = False
        target_temp = 200.0
        target_ror = 18.0
        active = True
    class FakeSource:
        charge_manager = FakeManager()
    assert _charge_target_annotations(FakeSource()) == ()


def test_charge_target_annotations_active_state_returns_snapshot():
    """When enabled and not yet charged, extractor returns a single active-state snapshot."""
    from artisanlib.plot_snapshot_extractor import _charge_target_annotations
    from artisanlib.plot_snapshot import ChargeTargetAnnotationSnapshot
    from artisanlib.charge_manager import ChargeReadiness
    class FakeManager:
        enabled = True
        active = True
        target_temp = 200.0
        target_ror = 18.0
        charged_temp = 0.0
        charged_ror = 0.0
        temp_tolerance = 1.0
        ror_tolerance = 6.0
        prediction_window = 5.0
        prediction_time = None
        def evaluate_readiness(self, current_temp, current_ror, short_ror=None, long_ror=None, et_bt_gap=None, reference_et_bt_gap=None):  # noqa: ARG002
            return ChargeReadiness(
                status='near',
                title='接近目标',
                reason='接近目标，继续观察',
                color='green',
                prediction_seconds=8.4,
                current_rwt=34.9,
                target_rwt=33.3,
            )
        @staticmethod
        def calculate_rwt(ror):
            return 600.0 / ror if ror and ror > 0 else 0.0
    class FakeSource:
        charge_manager = FakeManager()
        timex = (0.0, 100.0, 200.0, 423.5)
        temp2 = (25.0, 100.0, 150.0, 192.1)
        delta2 = (0.0, 30.0, 22.0, 18.5)
    result = _charge_target_annotations(FakeSource())
    assert len(result) == 1
    snap = result[0]
    assert isinstance(snap, ChargeTargetAnnotationSnapshot)
    assert snap.enabled is True
    assert snap.is_charged is False
    assert snap.target_temp == 200.0
    assert snap.target_ror == 18.0
    assert snap.title == '接近目标'
    assert snap.color == 'green'
    assert snap.prediction_seconds == 8.4
    assert snap.anchor_time == 423.5
    assert snap.anchor_temp == 192.1
    assert snap.x_limit > 0
    assert snap.y_limit_top > 0


def test_charge_target_annotations_charged_state_returns_snapshot():
    """When charge_manager.active is False (post-charge), extractor returns a charged-state snapshot."""
    from artisanlib.plot_snapshot_extractor import _charge_target_annotations
    class FakeManager:
        enabled = True
        active = False  # post-charge
        target_temp = 200.0
        target_ror = 18.0
        charged_temp = 198.5
        charged_ror = 17.2
        temp_tolerance = 1.0
        ror_tolerance = 6.0
        prediction_window = 5.0
        prediction_time = None
        def evaluate_readiness(self, current_temp, current_ror, short_ror=None, long_ror=None, et_bt_gap=None, reference_et_bt_gap=None):  # noqa: ARG002
            raise AssertionError('evaluate_readiness should NOT be called in charged state')
        @staticmethod
        def calculate_rwt(ror):
            return 600.0 / ror if ror and ror > 0 else 0.0
    class FakeSource:
        charge_manager = FakeManager()
        timex = (0.0, 100.0, 200.0, 423.5)
        temp2 = (25.0, 100.0, 150.0, 192.1)
        delta2 = (0.0, 30.0, 22.0, 18.5)
    result = _charge_target_annotations(FakeSource())
    assert len(result) == 1
    snap = result[0]
    assert snap.is_charged is True
    assert snap.charged_temp == 198.5
    assert snap.charged_ror == 17.2
    assert snap.target_temp == 200.0
    assert snap.target_ror == 18.0


def test_charge_target_annotations_falls_back_when_evaluate_raises():
    """If evaluate_readiness raises, extractor returns a waiting-state fallback snapshot."""
    from artisanlib.plot_snapshot_extractor import _charge_target_annotations
    class FakeManager:
        enabled = True
        active = True
        target_temp = 200.0
        target_ror = 18.0
        charged_temp = 0.0
        charged_ror = 0.0
        @staticmethod
        def calculate_rwt(ror):
            return 600.0 / ror if ror and ror > 0 else 0.0
        def evaluate_readiness(self, **_kwargs):
            raise ValueError('bad manager state')
    class FakeSource:
        charge_manager = FakeManager()
        timex = (10.0,)
        temp2 = (190.0,)
        delta2 = (18.0,)
    result = _charge_target_annotations(FakeSource())
    assert len(result) == 1
    assert result[0].color == 'gray'
    assert result[0].title == '等待数据'


def test_charge_target_annotations_handles_inf_and_nan_inputs():
    """Inf/NaN in canvas data must not crash the extractor or produce non-finite snapshot fields."""
    from artisanlib.plot_snapshot_extractor import _charge_target_annotations
    class FakeManager:
        enabled = True
        active = True
        target_temp = 200.0
        target_ror = 18.0
        charged_temp = 0.0
        charged_ror = 0.0
        @staticmethod
        def calculate_rwt(ror):
            return 600.0 / ror if ror and ror > 0 else 0.0
        def evaluate_readiness(self, **_kwargs):
            from artisanlib.charge_manager import ChargeReadiness
            return ChargeReadiness(
                status='waiting',
                title='等待升温',
                reason='距离目标还远',
                color='gray',
                prediction_seconds=None,
                current_rwt=33.3,
                target_rwt=33.3,
            )
    class FakeSource:
        charge_manager = FakeManager()
        timex = (float('inf'),)
        temp2 = (float('nan'), float('inf'))
        delta2 = (float('inf'),)
    result = _charge_target_annotations(FakeSource())
    assert len(result) == 1
    snap = result[0]
    import math
    assert math.isfinite(snap.anchor_time), f'anchor_time must be finite, got {snap.anchor_time}'
    assert math.isfinite(snap.anchor_temp), f'anchor_temp must be finite, got {snap.anchor_temp}'
    assert math.isfinite(snap.x_limit), f'x_limit must be finite, got {snap.x_limit}'
    assert math.isfinite(snap.y_limit_top), f'y_limit_top must be finite, got {snap.y_limit_top}'


def test_charge_target_annotations_reuses_precomputed_axes():
    """When axes are provided, extractor must use them instead of scanning temp2/timex."""
    from artisanlib.plot_snapshot_extractor import _charge_target_annotations
    from artisanlib.plot_snapshot import AxisSnapshot
    class FakeManager:
        enabled = True
        active = True
        target_temp = 200.0
        target_ror = 18.0
        charged_temp = 0.0
        charged_ror = 0.0
        @staticmethod
        def calculate_rwt(ror):
            return 600.0 / ror if ror and ror > 0 else 0.0
        def evaluate_readiness(self, **_kwargs):
            from artisanlib.charge_manager import ChargeReadiness
            return ChargeReadiness(
                status='waiting',
                title='等待升温',
                reason='距离目标还远',
                color='gray',
                prediction_seconds=None,
                current_rwt=33.3,
                target_rwt=33.3,
            )
    class FakeSource:
        charge_manager = FakeManager()
        timex = (0.0, 100.0)
        temp2 = (25.0, 100.0)
        delta2 = (0.0, 30.0)
    time_axis = AxisSnapshot(minimum=0.0, maximum=999.0, label='')
    temperature_axis = AxisSnapshot(minimum=0.0, maximum=888.0, label='')
    result = _charge_target_annotations(FakeSource(), time_axis=time_axis, temperature_axis=temperature_axis)
    assert len(result) == 1
    snap = result[0]
    # x_limit/y_limit_top should come from axes, not from timex/temp2
    assert snap.x_limit == 999.0
    assert snap.y_limit_top == 888.0


def test_phase_band_color_uses_configured_palette():
    from artisanlib.plot_snapshot_extractor import _phase_band_color
    class FakeSource:
        palette = {'rect1': '#e5e5e5', 'rect2': '#b2b2b2', 'rect3': '#d3d3d3'}
    s = FakeSource()
    assert _phase_band_color(s, 'rect1', 0) == '#e5e5e5'
    assert _phase_band_color(s, 'rect2', 1) == '#b2b2b2'
    assert _phase_band_color(s, 'rect3', 2) == '#d3d3d3'


def test_background_curves_default_to_dashed_and_lower_alpha():
    from artisanlib.plot_snapshot_extractor import _background_curves
    class FakeSource:
        backgroundBTflag = True
        backgroundETflag = True
        DeltaBTBflag = True
        DeltaETBflag = True
        backgroundbt = '#B29E84'
        backgroundet = '#8493A0'
        backgrounddeltabt = '#B29E84'
        backgrounddeltaet = '#8493A0'
        timex = (0.0, 100.0, 200.0)
        timeB = (0.0, 100.0, 200.0)
        timeindexB = (0, 0, 0, 0, 0, 0, 2)
        flagon = True
        temp2B = (150.0, 180.0, 200.0)
        temp1B = (180.0, 210.0, 230.0)
        stemp2B = (150.0, 180.0, 200.0)
        stemp1B = (180.0, 210.0, 230.0)
        delta2B = (30.0, 20.0, 15.0)
        delta1B = (40.0, 30.0, 20.0)
        BTbacklinewidth = 1.5
        ETbacklinewidth = 1.5
        BTBdeltalinewidth = 1.0
        ETBdeltalinewidth = 1.0
        backgroundShowFullflag = True
        palette = {}
    curves = _background_curves(FakeSource())
    assert len(curves) == 4
    for curve in curves:
        assert curve.line_style == '--', f'background curve {curve.name} should be dashed, got {curve.line_style}'
        assert curve.opacity <= 0.35, f'background curve {curve.name} alpha should be <= 0.35, got {curve.opacity}'
