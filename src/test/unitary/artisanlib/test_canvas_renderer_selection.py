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


class FakeLiveFrameCanvas:
    def __init__(self, selection: RendererSelection) -> None:
        self.plot_renderer_selection = selection
        self.ETcurve = True
        self.BTcurve = True
        self.DeltaETflag = True
        self.DeltaBTflag = True
        self.l_temp1 = FakeLine()
        self.l_temp2 = FakeLine()
        self.l_delta1 = FakeLine()
        self.l_delta2 = FakeLine()
        self.plot_live_frame_apply_result = None


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
