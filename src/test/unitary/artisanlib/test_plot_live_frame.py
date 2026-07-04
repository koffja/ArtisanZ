from __future__ import annotations

import math

import numpy
import pytest
from matplotlib.lines import Line2D

from artisanlib.plot_live_frame import (
    LiveAxisRange,
    LiveCurveData,
    LivePlotFrame,
    apply_matplotlib_live_axis_range,
    apply_matplotlib_live_curve_data,
    apply_matplotlib_live_curve_sequences,
    apply_matplotlib_live_frame,
    apply_pyqtgraph_live_curve_data,
    apply_pyqtgraph_live_frame,
    apply_selected_live_frame,
    live_frame_to_snapshot,
    merge_static_plot_overlays,
)
from artisanlib.plot_snapshot import (
    AreaFillSnapshot,
    AxisSnapshot,
    ChargeTargetAnnotationSnapshot,
    EventMarkerSnapshot,
    EventValueSnapshot,
    GuideLineSnapshot,
    PhaseBandSnapshot,
    RoastPlotSnapshot,
)
from artisanlib.plot_renderer_registry import create_default_renderer_registry
from artisanlib.plot_renderer_settings import RendererSelection


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


class FakeAxis:
    def __init__(self) -> None:
        self.xlim: tuple[float, float] | None = None
        self.calls = 0

    def set_xlim(self, minimum: float, maximum: float) -> None:
        self.xlim = (minimum, maximum)
        self.calls += 1


class NoSetXLimAxis:
    pass


class FakePyQtGraphItem:
    def __init__(self) -> None:
        self.x: tuple[float, ...] = ()
        self.y: tuple[float, ...] = ()
        self.calls = 0

    def setData(self, x: tuple[float, ...], y: tuple[float, ...]) -> None:  # noqa: N802
        self.x = x
        self.y = y
        self.calls += 1


def _renderer_selection(renderer_id: str) -> RendererSelection:
    registry = create_default_renderer_registry()
    return RendererSelection(
        requested_renderer_id=renderer_id,
        renderer_id=renderer_id,
        plugin=registry.get(renderer_id),
        registry=registry,
    )


def test_live_curve_data_from_sequences_normalizes_values() -> None:
    curve = LiveCurveData.from_sequences(
        name='Delta BT',
        x=[0, 1.5, 2],
        y=[None, 4, 5.5],
        y_axis='ror',
        color='#78905D',
        line_style='--',
        line_width=2.0,
    )

    assert curve.name == 'Delta BT'
    assert curve.x == (0.0, 1.5, 2.0)
    assert curve.y == (None, 4.0, 5.5)
    assert curve.y_axis == 'ror'
    assert curve.color == '#78905D'
    assert curve.line_style == '--'
    assert curve.line_width == 2.0


def test_live_curve_data_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match='same length'):
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120])


def test_live_plot_frame_exposes_stable_curve_names() -> None:
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='ET', x=[0], y=[130]),
        LiveCurveData.from_sequences(name='BT', x=[0], y=[120]),
    ))

    assert frame.curve_names() == ('ET', 'BT')


def test_live_axis_range_from_values_normalizes_bounds() -> None:
    axis_range = LiveAxisRange.from_values(1, 12.5)

    assert axis_range.minimum == 1.0
    assert axis_range.maximum == 12.5


def test_live_axis_range_rejects_inverted_bounds() -> None:
    with pytest.raises(ValueError, match='maximum'):
        LiveAxisRange.from_values(12.5, 1)


def test_apply_matplotlib_live_axis_range_updates_axis() -> None:
    axis = FakeAxis()
    axis_range = LiveAxisRange.from_values(0, 15)

    assert apply_matplotlib_live_axis_range(axis, axis_range) is True

    assert axis.xlim == (0.0, 15.0)
    assert axis.calls == 1


def test_apply_matplotlib_live_axis_range_skips_missing_or_incompatible_axis() -> None:
    axis_range = LiveAxisRange.from_values(0, 15)

    assert apply_matplotlib_live_axis_range(None, axis_range) is False
    assert apply_matplotlib_live_axis_range(NoSetXLimAxis(), axis_range) is False


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


def test_apply_matplotlib_live_curve_sequences_updates_real_line2d() -> None:
    line = Line2D([], [])

    assert apply_matplotlib_live_curve_sequences(
        line,
        name='BT projection',
        x=[0, 2],
        y=[120, 125.5],
    ) is True

    assert line.get_xdata() == (0.0, 2.0)
    y_data = line.get_ydata()
    assert isinstance(y_data, numpy.ndarray)
    assert y_data.tolist() == [120.0, 125.5]


def test_apply_matplotlib_live_curve_sequences_clears_real_line2d() -> None:
    line = Line2D([0, 1], [120, 121])

    assert apply_matplotlib_live_curve_sequences(
        line,
        name='BT projection',
        x=[],
        y=[],
    ) is True

    assert line.get_xdata() == ()
    y_data = line.get_ydata()
    assert isinstance(y_data, numpy.ndarray)
    assert y_data.tolist() == []


def test_apply_matplotlib_live_curve_sequences_skips_missing_line() -> None:
    assert apply_matplotlib_live_curve_sequences(
        None,
        name='BT projection',
        x=[0],
        y=[120],
    ) is False


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


def test_apply_pyqtgraph_live_curve_data_converts_dropouts_to_nan() -> None:
    item = FakePyQtGraphItem()
    curve = LiveCurveData.from_sequences(name='Delta BT', x=[0, 1], y=[None, 4.5], y_axis='ror')

    assert apply_pyqtgraph_live_curve_data(item, curve) is True

    assert item.x == (0.0, 1.0)
    assert math.isnan(item.y[0])
    assert item.y[1] == 4.5
    assert item.calls == 1


def test_apply_pyqtgraph_live_curve_data_skips_missing_or_incompatible_item() -> None:
    curve = LiveCurveData.from_sequences(name='BT', x=[0], y=[120])

    assert apply_pyqtgraph_live_curve_data(None, curve) is False
    assert apply_pyqtgraph_live_curve_data(NoSetDataLine(), curve) is False


def test_apply_pyqtgraph_live_frame_updates_known_curves_only() -> None:
    et_item = FakePyQtGraphItem()
    bt_item = FakePyQtGraphItem()
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='ET', x=[0, 1], y=[130, 131]),
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, 121]),
        LiveCurveData.from_sequences(name='Delta BT', x=[0, 1], y=[None, 4], y_axis='ror'),
    ))

    applied = apply_pyqtgraph_live_frame({'ET': et_item, 'BT': bt_item}, frame)

    assert applied == ('ET', 'BT')
    assert et_item.y == (130.0, 131.0)
    assert bt_item.y == (120.0, 121.0)


def test_apply_selected_live_frame_uses_matplotlib_surface() -> None:
    bt_line = FakeLine()
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, 121]),
    ))

    result = apply_selected_live_frame(
        _renderer_selection('matplotlib-snapshot'),
        frame,
        matplotlib_lines={'BT': bt_line},
    )

    assert result.requested_renderer_id == 'matplotlib-snapshot'
    assert result.renderer_id == 'matplotlib-snapshot'
    assert result.surface == 'matplotlib-axis'
    assert result.applied_curves == ('BT',)
    assert result.used_fallback is False
    assert bt_line.y is not None
    assert bt_line.y.tolist() == [120.0, 121.0]


def test_apply_selected_live_frame_uses_pyqtgraph_surface_when_targets_exist() -> None:
    bt_item = FakePyQtGraphItem()
    bt_line = FakeLine()
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, None]),
    ))

    result = apply_selected_live_frame(
        _renderer_selection('pyqtgraph-snapshot'),
        frame,
        matplotlib_lines={'BT': bt_line},
        pyqtgraph_items={'BT': bt_item},
    )

    assert result.requested_renderer_id == 'pyqtgraph-snapshot'
    assert result.renderer_id == 'pyqtgraph-snapshot'
    assert result.surface == 'pyqtgraph-plot'
    assert result.applied_curves == ('BT',)
    assert result.used_fallback is False
    assert bt_item.x == (0.0, 1.0)
    assert math.isnan(bt_item.y[1])
    assert bt_line.y is not None
    assert bt_line.y.tolist()[0] == 120.0
    assert bt_line.y.tolist()[1] is None


def test_apply_selected_live_frame_reports_pyqtgraph_update_fallback_reason() -> None:
    bt_line = FakeLine()
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, 121]),
    ))

    result = apply_selected_live_frame(
        _renderer_selection('pyqtgraph-snapshot'),
        frame,
        matplotlib_lines={'BT': bt_line},
        pyqtgraph_fallback_reason='pyqtgraph_live_update_error',
    )

    assert result.renderer_id == 'matplotlib-snapshot'
    assert result.surface == 'matplotlib-axis'
    assert result.fallback_reason == 'pyqtgraph_live_update_error'
    assert result.applied_curves == ('BT',)


def test_apply_selected_live_frame_falls_back_without_pyqtgraph_targets() -> None:
    bt_line = FakeLine()
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, 121]),
    ))

    result = apply_selected_live_frame(
        _renderer_selection('pyqtgraph-snapshot'),
        frame,
        matplotlib_lines={'BT': bt_line},
    )

    assert result.requested_renderer_id == 'pyqtgraph-snapshot'
    assert result.renderer_id == 'matplotlib-snapshot'
    assert result.surface == 'matplotlib-axis'
    assert result.applied_curves == ('BT',)
    assert result.fallback_reason == 'pyqtgraph_targets_unavailable'
    assert result.used_fallback is True
    assert bt_line.y is not None
    assert bt_line.y.tolist() == [120.0, 121.0]


def test_live_frame_to_snapshot_preserves_curve_style_payload() -> None:
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(
            name='Delta BT',
            x=[0, 1],
            y=[None, 4.0],
            y_axis='ror',
            color='#78905D',
            line_style='--',
            line_width=2.5,
        ),
    ))

    snapshot = live_frame_to_snapshot(
        frame,
        time_axis=AxisSnapshot(minimum=0.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )

    assert snapshot.curves[0].name == 'Delta BT'
    assert snapshot.curves[0].y_axis == 'ror'
    assert snapshot.curves[0].color == '#78905D'
    assert snapshot.curves[0].line_style == '--'
    assert snapshot.curves[0].line_width == 2.5
    assert snapshot.ror_axis == AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR')


def test_merge_static_plot_overlays_keeps_live_curves_and_restores_background_layers() -> None:
    live_snapshot = live_frame_to_snapshot(
        LivePlotFrame(curves=(
            LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, 121], color='#4E7180'),
        )),
        time_axis=AxisSnapshot(minimum=0.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )
    static_snapshot = RoastPlotSnapshot(
        curves=(),
        time_axis=AxisSnapshot(minimum=10.0, maximum=99.0, label='Old Time'),
        temperature_axis=AxisSnapshot(minimum=10.0, maximum=99.0, label='Old Temperature'),
        ror_axis=None,
        events=(EventMarkerSnapshot(time=2.0, label='CHARGE', event_type=100, color='#B85F56'),),
        event_values=(EventValueSnapshot(time=3.0, value=40.0, event_type=1, color='#4E7180'),),
        phase_bands=(PhaseBandSnapshot(minimum=100.0, maximum=150.0, color='#E5E5E5'),),
        guides=(GuideLineSnapshot(position=4.0, label='AUC', color='#78905D'),),
        areas=(AreaFillSnapshot.from_sequences(
            x=[1.0, 2.0],
            y=[120.0, 125.0],
            baseline=100.0,
            color='#767676',
            label='AUC',
        ),),
    )

    merged = merge_static_plot_overlays(live_snapshot, static_snapshot)

    assert merged.curves == live_snapshot.curves
    assert merged.time_axis == live_snapshot.time_axis
    assert merged.temperature_axis == live_snapshot.temperature_axis
    assert merged.ror_axis == live_snapshot.ror_axis
    assert merged.events == static_snapshot.events
    assert merged.event_values == static_snapshot.event_values
    assert merged.phase_bands == static_snapshot.phase_bands
    assert merged.guides == static_snapshot.guides
    assert merged.areas == static_snapshot.areas


def test_merge_static_plot_overlays_preserves_charge_target_annotations() -> None:
    """The live-frame merge must carry charge_target_annotations from static snapshot."""
    annotation = ChargeTargetAnnotationSnapshot(
        enabled=True,
        is_charged=False,
        target_temp=200.0,
        target_ror=18.0,
        charged_temp=0.0,
        charged_ror=0.0,
        title='接近目标',
        reason='接近目标，继续观察',
        prediction_seconds=8.4,
        color='green',
        current_rwt=34.9,
        target_rwt=33.3,
        anchor_time=423.5,
        anchor_temp=192.1,
        x_limit=600.0,
        y_limit_top=250.0,
    )
    static_snapshot = RoastPlotSnapshot(
        curves=(),
        time_axis=AxisSnapshot(minimum=0.0, maximum=600.0, label=''),
        temperature_axis=AxisSnapshot(minimum=0.0, maximum=250.0, label=''),
        charge_target_annotations=(annotation,),
    )
    live_snapshot = RoastPlotSnapshot(
        curves=(),
        time_axis=AxisSnapshot(minimum=0.0, maximum=400.0, label=''),
        temperature_axis=AxisSnapshot(minimum=0.0, maximum=220.0, label=''),
    )
    merged = merge_static_plot_overlays(live_snapshot, static_snapshot)
    assert merged.charge_target_annotations == (annotation,), (
        'charge_target_annotations must be preserved from static snapshot'
    )
