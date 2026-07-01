from __future__ import annotations

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PyQt6.QtWidgets import QApplication

_APPLICATION = QApplication.instance() or QApplication([])
_APPLICATION.artisanviewerMode = False  # type: ignore[attr-defined]

from artisanlib import canvas
from artisanlib.plot_renderer_settings import ARTISANZ_RENDERER_ID, RendererSelectionError


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
