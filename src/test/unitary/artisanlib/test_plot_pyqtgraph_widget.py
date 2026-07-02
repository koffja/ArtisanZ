from __future__ import annotations

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PyQt6.QtWidgets import QApplication

from artisanlib.plot_pyqtgraph_widget import create_pyqtgraph_plot_target
from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, RoastPlotSnapshot

pg = pytest.importorskip('pyqtgraph')
_APPLICATION = QApplication.instance() or QApplication([])


def _snapshot(*, include_ror: bool = True) -> RoastPlotSnapshot:
    curves = [
        CurveSnapshot.from_sequences(
            name='BT',
            x=[0, 1, 2],
            y=[140, 142, 144],
            color='#4E7180',
        ),
    ]
    ror_axis = None
    if include_ror:
        curves.append(CurveSnapshot.from_sequences(
            name='Delta BT',
            x=[0, 1, 2],
            y=[None, 5.0, 5.5],
            color='#78905D',
            y_axis='ror',
        ))
        ror_axis = AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR')
    return RoastPlotSnapshot(
        curves=tuple(curves),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=ror_axis,
    )


def test_create_pyqtgraph_plot_target_renders_temperature_and_ror_curves() -> None:
    target = create_pyqtgraph_plot_target(use_opengl=False, include_ror=True)
    try:
        target.renderer.set_snapshot(_snapshot(include_ror=True))
        _APPLICATION.processEvents()

        assert target.opengl_requested is False
        assert target.ror_plot is not None
        assert _plot_data_item_count(target.temperature_plot) == 1
        assert _plot_data_item_count(target.ror_plot) == 1
    finally:
        target.close()


def test_create_pyqtgraph_plot_target_can_skip_ror_plot() -> None:
    target = create_pyqtgraph_plot_target(use_opengl=False, include_ror=False)
    try:
        target.renderer.set_snapshot(_snapshot(include_ror=False))
        _APPLICATION.processEvents()

        assert target.ror_plot is None
        assert _plot_data_item_count(target.temperature_plot) == 1
    finally:
        target.close()


def test_create_pyqtgraph_plot_target_restores_opengl_config_on_close() -> None:
    previous_opengl = bool(pg.getConfigOption('useOpenGL'))
    target = create_pyqtgraph_plot_target(use_opengl=not previous_opengl, include_ror=False)

    assert bool(pg.getConfigOption('useOpenGL')) is (not previous_opengl)

    target.close()

    assert bool(pg.getConfigOption('useOpenGL')) is previous_opengl


def _plot_data_item_count(plot: object) -> int:
    list_data_items = getattr(plot, 'listDataItems', None)
    if callable(list_data_items):
        return len(list_data_items())
    return 0
