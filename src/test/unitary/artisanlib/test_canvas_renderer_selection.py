from __future__ import annotations

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PyQt6.QtWidgets import QApplication

_APPLICATION = QApplication.instance() or QApplication([])
_APPLICATION.artisanviewerMode = False  # type: ignore[attr-defined]

from artisanlib import canvas
from artisanlib.plot_live_frame import LiveCurveData, LivePlotFrame
from artisanlib.plot_renderer_registry import create_default_renderer_registry
from artisanlib.plot_renderer_settings import ARTISANZ_RENDERER_ID, RendererSelectionError
from artisanlib.plot_renderer_settings import RendererSelection


class FakeLine:
    def __init__(self) -> None:
        self.x: tuple[float, ...] = ()
        self.y: object = None

    def set_data(self, x: tuple[float, ...], y: object) -> None:
        self.x = x
        self.y = y


class FakePyQtGraphItem:
    def __init__(self) -> None:
        self.x: tuple[float, ...] = ()
        self.y: tuple[float, ...] = ()

    def setData(self, x: tuple[float, ...], y: tuple[float, ...]) -> None:  # noqa: N802
        self.x = x
        self.y = y


class FakePyQtGraphRenderer:
    def __init__(self, *, fail_update: bool = False) -> None:
        self.items: dict[str, FakePyQtGraphItem] = {}
        self.snapshots: list[object] = []
        self.view_states: list[object] = []
        self.fail_update = fail_update

    def update_live_frame(self, snapshot: object) -> None:
        if self.fail_update:
            raise RuntimeError('pyqtgraph update failed')
        self.snapshots.append(snapshot)
        for curve in snapshot.curves:
            self.items.setdefault(curve.name, FakePyQtGraphItem())

    def reset_view(self, view_state: object) -> None:
        self.view_states.append(view_state)

    def item_for(self, name: str) -> FakePyQtGraphItem | None:
        return self.items.get(name)


class FakePyQtGraphTarget:
    def __init__(self, *, fail_update: bool = False) -> None:
        self.renderer = FakePyQtGraphRenderer(fail_update=fail_update)
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeWidget:
    def __init__(self) -> None:
        self.visible = True

    def parentWidget(self) -> None:  # noqa: N802
        return None

    def setVisible(self, visible: bool) -> None:  # noqa: N802
        self.visible = visible


class FakeLiveFrameCanvas:
    def __init__(self, selection: RendererSelection) -> None:
        self.plot_renderer_selection = selection
        self.plot_pyqtgraph_target = None
        self.plot_renderer_embed_fallback_reason = None
        self.canvas = FakeWidget()
        self.plot_display_widget = self.canvas
        self.ETcurve = True
        self.BTcurve = True
        self.DeltaETflag = True
        self.DeltaBTflag = True
        self.l_temp1 = FakeLine()
        self.l_temp2 = FakeLine()
        self.l_delta1 = FakeLine()
        self.l_delta2 = FakeLine()
        self.plot_live_frame_apply_result = None
        self.ax = None
        self.delta_ax = None
        self.startofx = 0.0
        self.endofx = 12.0
        self.ylimit_min = 70.0
        self.ylimit = 270.0

    def apply_pyqtgraph_live_plot_frame(self, frame: LivePlotFrame) -> dict[str, object | None]:
        return canvas.tgraphcanvas.apply_pyqtgraph_live_plot_frame(self, frame)

    def disable_selected_plot_widget(self) -> None:
        return canvas.tgraphcanvas.disable_selected_plot_widget(self)

    def live_time_axis_snapshot(self) -> object:
        return canvas.tgraphcanvas.live_time_axis_snapshot(self)

    def live_temperature_axis_snapshot(self) -> object:
        return canvas.tgraphcanvas.live_temperature_axis_snapshot(self)

    def live_ror_axis_snapshot(self) -> object:
        return canvas.tgraphcanvas.live_ror_axis_snapshot(self)


def _renderer_selection(renderer_id: str) -> RendererSelection:
    registry = create_default_renderer_registry()
    return RendererSelection(
        requested_renderer_id=renderer_id,
        renderer_id=renderer_id,
        plugin=registry.get(renderer_id),
        registry=registry,
    )


def test_select_canvas_renderer_defaults_to_matplotlib(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ARTISANZ_RENDERER_ID, raising=False)

    selection = canvas.select_canvas_renderer()

    assert selection.renderer_id == 'matplotlib-snapshot'
    assert selection.registry.get('matplotlib-snapshot').renderer_id == 'matplotlib-snapshot'


def test_select_canvas_renderer_accepts_env_requested_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ARTISANZ_RENDERER_ID, 'pyqtgraph-snapshot')

    selection = canvas.select_canvas_renderer()

    assert selection.requested_renderer_id == 'pyqtgraph-snapshot'
    assert selection.renderer_id == 'pyqtgraph-snapshot'


def test_select_canvas_renderer_falls_back_after_selection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_selection() -> canvas.RendererSelection:
        raise RendererSelectionError('no available renderer plugins')

    monkeypatch.setattr(canvas, 'select_renderer', fail_selection)

    selection = canvas.select_canvas_renderer()

    assert selection.renderer_id == 'matplotlib-snapshot'
    assert selection.fallback_reason == 'selection_error'


def test_select_canvas_renderer_falls_back_after_unexpected_selection_error(
        monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_selection() -> canvas.RendererSelection:
        raise ModuleNotFoundError("No module named 'missing.parent'")

    monkeypatch.setattr(canvas, 'select_renderer', fail_selection)

    selection = canvas.select_canvas_renderer()

    assert selection.renderer_id == 'matplotlib-snapshot'
    assert selection.fallback_reason == 'selection_error'


def test_canvas_renderer_selection_slot_is_declared() -> None:
    assert 'plot_renderer_selection' in canvas.tgraphcanvas.__slots__
    assert 'plot_live_frame_apply_result' in canvas.tgraphcanvas.__slots__


def test_apply_live_plot_frame_uses_selected_matplotlib_renderer() -> None:
    window = FakeLiveFrameCanvas(_renderer_selection('matplotlib-snapshot'))
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='ET', x=[0, 1], y=[130, 131]),
        LiveCurveData.from_sequences(name='Delta BT', x=[0, 1], y=[None, 4], y_axis='ror'),
    ))

    result = canvas.tgraphcanvas.apply_live_plot_frame(window, frame)

    assert result.renderer_id == 'matplotlib-snapshot'
    assert result.surface == 'matplotlib-axis'
    assert result.applied_curves == ('ET', 'Delta BT')
    assert result.used_fallback is False
    assert window.plot_live_frame_apply_result == result
    assert window.l_temp1.x == (0.0, 1.0)
    assert window.l_delta2.x == (0.0, 1.0)


def test_apply_live_plot_frame_falls_back_when_pyqtgraph_targets_are_not_embedded() -> None:
    window = FakeLiveFrameCanvas(_renderer_selection('pyqtgraph-snapshot'))
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, 121]),
    ))

    result = canvas.tgraphcanvas.apply_live_plot_frame(window, frame)

    assert result.requested_renderer_id == 'pyqtgraph-snapshot'
    assert result.renderer_id == 'matplotlib-snapshot'
    assert result.surface == 'matplotlib-axis'
    assert result.fallback_reason == 'pyqtgraph_targets_unavailable'
    assert result.applied_curves == ('BT',)
    assert window.plot_live_frame_apply_result == result
    assert window.l_temp2.x == (0.0, 1.0)


def test_apply_live_plot_frame_uses_embedded_pyqtgraph_target() -> None:
    window = FakeLiveFrameCanvas(_renderer_selection('pyqtgraph-snapshot'))
    window.plot_pyqtgraph_target = FakePyQtGraphTarget()
    window.plot_display_widget = FakeWidget()
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(
            name='BT',
            x=[0, 1],
            y=[120, None],
            color='#4E7180',
        ),
    ))

    result = canvas.tgraphcanvas.apply_live_plot_frame(window, frame)

    assert result.requested_renderer_id == 'pyqtgraph-snapshot'
    assert result.renderer_id == 'pyqtgraph-snapshot'
    assert result.surface == 'pyqtgraph-plot'
    assert result.applied_curves == ('BT',)
    assert result.used_fallback is False
    assert window.plot_live_frame_apply_result == result
    assert window.plot_pyqtgraph_target.renderer.snapshots
    assert window.plot_pyqtgraph_target.renderer.view_states
    bt_item = window.plot_pyqtgraph_target.renderer.item_for('BT')
    assert bt_item is not None
    assert bt_item.x == (0.0, 1.0)
    assert window.l_temp2.x == (0.0, 1.0)


def test_apply_live_plot_frame_keeps_extra_curve_items_distinct() -> None:
    window = FakeLiveFrameCanvas(_renderer_selection('pyqtgraph-snapshot'))
    window.plot_pyqtgraph_target = FakePyQtGraphTarget()
    window.plot_display_widget = FakeWidget()
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='Extra 1 1', x=[0, 1], y=[101, 102]),
        LiveCurveData.from_sequences(name='Extra 2 1', x=[0, 1], y=[111, 112]),
    ))

    result = canvas.tgraphcanvas.apply_live_plot_frame(window, frame)

    assert result.surface == 'pyqtgraph-plot'
    assert result.applied_curves == ('Extra 1 1', 'Extra 2 1')
    assert set(window.plot_pyqtgraph_target.renderer.items) == {'Extra 1 1', 'Extra 2 1'}


def test_apply_live_plot_frame_falls_back_after_pyqtgraph_update_error() -> None:
    window = FakeLiveFrameCanvas(_renderer_selection('pyqtgraph-snapshot'))
    failing_target = FakePyQtGraphTarget(fail_update=True)
    window.plot_pyqtgraph_target = failing_target
    window.plot_display_widget = FakeWidget()
    frame = LivePlotFrame(curves=(
        LiveCurveData.from_sequences(name='BT', x=[0, 1], y=[120, 121]),
    ))

    result = canvas.tgraphcanvas.apply_live_plot_frame(window, frame)

    assert result.requested_renderer_id == 'pyqtgraph-snapshot'
    assert result.renderer_id == 'matplotlib-snapshot'
    assert result.surface == 'matplotlib-axis'
    assert result.fallback_reason == 'pyqtgraph_live_update_error'
    assert result.applied_curves == ('BT',)
    assert window.plot_renderer_embed_fallback_reason == 'pyqtgraph_live_update_error'
    assert window.plot_pyqtgraph_target is None
    assert failing_target.closed is True
    assert window.l_temp2.x == (0.0, 1.0)
